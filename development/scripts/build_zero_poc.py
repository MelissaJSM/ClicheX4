"""대기 0x93의 정확히 두 픽셀만 변경한 기술 시험 BIN 생성. Riko 아트가 아니다."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.project import load_project,validate_bin,working_cue,write_json,inspect_references
from scripts.discover_inputs import sha256,psx_arc
from scripts.extract_zero import save_image
from src.psx_player import decode_stream,graphics_bank,composition_frame,compose_indices
from src.psx_disc import write_archive_copy


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract',type=Path,required=True)
    args=parser.parse_args()
    extracted=args.extract.resolve()
    if not extracted.is_relative_to((ROOT/'work/ver_buki_riko').resolve()):
        raise ValueError('Expected first-project extraction directory')
    report=json.loads((extracted/'report.json').read_text(encoding='utf-8'))
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text(encoding='utf-8'))
    project=load_project(ROOT,'ver_buki_riko');inspect_references(ROOT,project)
    source=ROOT/project['source_bin'];validate_bin(source,profile['source_sha256'])
    if not report.get('runtime',{}).get('framebuffer_matches') or not report['compressed_token_roundtrip']:
        raise ValueError('Runtime frame match and no-change roundtrip are required')
    arc=(extracted/'original.arc').read_bytes(); rebuilt=(extracted/'roundtrip.arc').read_bytes()
    if sha256(arc)!=profile['zero_archive']['sha256'] or rebuilt!=arc:
        raise ValueError('Extraction identity/roundtrip mismatch')
    entries=psx_arc(arc)
    def get(kind):
        values=[e for e in entries if e['type']==hex(kind)]
        if len(values)!=1:raise ValueError('Ambiguous entry')
        e=values[0];return e,arc[e['offset']:e['offset']+e['size']]
    gfx_entry,graphics=get(2);_,parts=get(3);_,palettes=get(9)
    frame=147; f=graphics_bank(graphics,0)['frames'][frame]
    decoded=decode_stream(graphics,f['offset'],f['limit'],f['tile_count']*128)
    composition=composition_frame(parts,0,frame)
    before,size,bounds,provenance=compose_indices(decoded.data,f['tile_count'],composition)
    # 실제 저장 화면과 대응한 프레임의 중앙 2픽셀. 고정 실험 레시피일 뿐 제작 규격이 아니다.
    x,y,new_index=26,24,3
    pixel=y*size[0]+x
    a,b=provenance[pixel:pixel+2]
    if not a or not b or a['byte']!=b['byte'] or (a['shift'],b['shift'])!=(0,4):
        raise ValueError('Unexpected pixel provenance')
    packed_byte=a['byte']; owner=decoded.owners[packed_byte//2]
    if owner is None or Counter(decoded.owners)[owner]!=1:
        raise ValueError('Literal edit would propagate through back-references')
    compressed_byte=owner+(packed_byte%2)
    updated_graphics=bytearray(graphics)
    old_value=updated_graphics[compressed_byte]
    updated_graphics[compressed_byte]=new_index*17
    after_decoded=decode_stream(updated_graphics,f['offset'],f['limit'],f['tile_count']*128)
    if after_decoded.end!=decoded.end or len(updated_graphics)!=len(graphics):
        raise ValueError('Compression layout changed')
    changed_nibbles=sum(((a&15)!=(b&15))+((a>>4)!=(b>>4)) for a,b in zip(decoded.data,after_decoded.data))
    if changed_nibbles!=2:raise ValueError('Expected exactly two decoded pixel changes')
    sharing=[];affected=[]
    for bank_index in range(len(report['graphics_banks'])):
        for candidate in graphics_bank(graphics,bank_index)['frames']:
            # 모든 스트림을 다시 해석하여 예상 밖 영향을 검사한다.
            old=decode_stream(graphics,candidate['offset'],candidate['limit'],candidate['tile_count']*128)
            new=decode_stream(updated_graphics,candidate['offset'],candidate['limit'],candidate['tile_count']*128)
            if old.data!=new.data:
                sharing.append([bank_index,candidate['index']])
                if bank_index!=0:raise ValueError('Unexpected second-bank change')
                c=composition_frame(parts,0,candidate['index'])
                oi,os,_,_=compose_indices(old.data,candidate['tile_count'],c)
                ni,ns,_,_=compose_indices(new.data,candidate['tile_count'],c)
                if os!=ns:raise ValueError('Frame size changed')
                n=sum(a!=b for a,b in zip(oi,ni))
                if n:affected.append({'bank':bank_index,'frame':candidate['index'],'changed_pixels':n})
    if affected!=[{'bank':0,'frame':147,'changed_pixels':2}]:
        raise ValueError('Unexpected shared-frame effects')
    patched=bytearray(arc)
    arc_offset=gfx_entry['offset']+compressed_byte
    patched[arc_offset]=updated_graphics[compressed_byte]
    parent=ROOT/'out/ver_buki_riko'
    if not parent.resolve().is_relative_to(ROOT):raise ValueError('Output escaped workspace')
    out=parent/('poc_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True,exist_ok=False)
    roundtrip=write_archive_copy(source,out/'roundtrip.bin',profile['zero_archive'],rebuilt,profile['source_sha256'])
    if roundtrip['sha256']!=profile['source_sha256']:raise ValueError('BIN no-change roundtrip failed')
    result=write_archive_copy(source,out/'pixel_poc.bin',profile['zero_archive'],patched,profile['source_sha256'])
    if len(result['changed_sectors'])!=1 or len(result['changed_sectors'][0]['data_offsets'])!=1:
        raise ValueError('Unexpected disc change footprint')
    cue=(ROOT/project['source_cue']).read_bytes().decode('utf-8-sig')
    (out/'pixel_poc.cue').write_text(working_cue(cue,'pixel_poc.bin'),encoding='ascii',newline='')
    (out/'modified.arc').write_bytes(patched)
    after,_,_,_=compose_indices(after_decoded.data,f['tile_count'],composition)
    palette=struct.unpack_from('<16H',palettes)
    for name,data in [('before',before),('after',after)]:
        im=save_image(data,size,palette,out/(name+'.png'))
        im.resize((size[0]*8,size[1]*8),resample=0).save(out/(name+'_8x.png'))
    validate_bin(source,profile['source_sha256'])
    manifest={'project':'ver_buki_riko','task':'zero_riko','kind':'technical_two_pixel_bitmap_test',
              'source_sha256':profile['source_sha256'],'extraction_report':str(extracted/'report.json'),
              'roundtrip':roundtrip,'modified_bin':result,'modified_archive_sha256':sha256(patched),
              'source_archive_sha256':sha256(arc),'frame':frame,'pixel_positions':[[x,y],[x+1,y]],
              'original_indices':list(before[pixel:pixel+2]),'new_indices':[new_index,new_index],
              'graphics_entry_byte':compressed_byte,'arc_byte':arc_offset,'original_byte':old_value,
              'modified_byte':updated_graphics[compressed_byte],'decoded_shared_frames':sharing,
              'visible_affected_frames':affected,'source_preserved':True,'runtime_modified_verified':False,
              'caution':'Old save state contains original graphics; verify from a fresh boot, not F3 restore.'}
    write_json(out/'manifest.json',manifest)
    print(json.dumps({'output':str(out),'roundtrip':roundtrip,'modified':result,'affected':affected}))


if __name__=='__main__':main()
