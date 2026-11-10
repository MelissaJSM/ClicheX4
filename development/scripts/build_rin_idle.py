"""수용된 린 대기 6참조를 PS1 미국판 작업용 BIN에 적용하고 변경 범위를 검증."""
import argparse,hashlib,json,struct,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,load_project,inspect_references,working_cue
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas
from src.psx_frame_edit import read_indexed_png,edit_frame_set
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks
from scripts.prepare_rin_idle import PILOT,SEQUENCE,TICKS

# The first production revision has a superseded blink. Keep v1 only as history.
ART=ROOT/'work/ver_rin_nana/idle_production/v2'

IDS=(0,1,2,146,147,148)
def sha(data):return hashlib.sha256(data).hexdigest()
def entry(arc,kind):
    e=next(e for e in psx_arc(arc) if e['type']==hex(kind))
    return e,arc[e['offset']:e['offset']+e['size']]

def prepare(art=ART):
    art=art.resolve()
    if not art.is_relative_to(ROOT/'work/ver_rin_nana/idle_production'):raise ValueError('Unexpected Rin art directory')
    project=load_project(ROOT,'ver_rin_nana');inspect_references(ROOT,project)
    if not project.get('style_approved'):raise ValueError('Rin pilot not approved')
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf-8'))
    extract=ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z'
    arc=(extract/'original.arc').read_bytes()
    if sha(arc)!=profile['zero_archive']['sha256']:raise ValueError('Original ARC changed')
    gm,gfx=entry(arc,2);_,parts=entry(arc,3);pm,pal=entry(arc,9)
    palette=(PILOT/'candidate_palette.bin').read_bytes();words=struct.unpack('<16H',palette)
    if any((a^b)&0x8000 for a,b in zip(struct.unpack_from('<16H',pal),words)):raise ValueError('Palette alpha bit changed')
    recipe=json.loads((art/'recipe.json').read_text('utf-8'))
    if digest(PILOT/'rin_idle147_indexed.png')!=recipe['master_sha256']:raise ValueError('Master changed')
    frames={}
    for n in IDS:
        path=art/f'idle_{n:03}.png'
        if digest(path)!=recipe['frame_sha256'][str(n)]:raise ValueError('Art hash changed')
        frames[n]=read_indexed_png(path,words)
    bank=graphics_bank(gfx,0);groups={}
    for f in bank['frames']:groups.setdefault(f['offset'],[]).append(f)
    old={o:decode_stream(gfx,refs[0]['offset'],refs[0]['limit'],refs[0]['tile_count']*128) for o,refs in groups.items()}
    replacements={};checks=[];updated_offsets=set()
    for offset,refs in groups.items():
        if not any(f['index'] in IDS for f in refs):continue
        if any(f['index'] not in IDS for f in refs):raise ValueError('Shared unrelated frame')
        edits=[(composition_frame(parts,0,f['index']),*frames[f['index']]) for f in refs]
        packed=edit_frame_set(old[offset].data,refs[0]['tile_count'],edits)
        atlas,_,_=indexed_atlas(packed,refs[0]['tile_count'])
        for c,_,_ in edits:
            for p in c['parts']:
                t=p['tile']
                if t%16==0 and any(atlas[(t//16*16+y)*256] for y in range(16)):raise ValueError('Opaque U=0 boundary would clip under mirror')
                if p['flip_y'] and t<16 and any(atlas[t*16:t*16+16]):raise ValueError('Opaque V=0 boundary under flip')
        code=encode_stream(packed)
        if decode_stream(code,0,len(code),len(packed)).data!=packed:raise ValueError('Encoding mismatch')
        for f in refs:replacements[f['index']]=code
        checks.append({'frames':[f['index'] for f in refs],'encoded_bytes':len(code),'old_bytes':old[offset].end-offset})
        updated_offsets.add(offset)
    available=bank['end']-bank['base']-len(bank['frames'])*4
    required=sum(len(replacements[refs[0]['index']]) if refs[0]['index'] in replacements else old[o].end-o for o,refs in groups.items())
    savings=[]
    for o,s in sorted(old.items(),key=lambda v:-(v[1].end-v[1].start)):
        if required<=available:break
        if o in updated_offsets:continue
        code=encode_stream(s.data);gain=s.end-o-len(code)
        if gain<=0:continue
        if decode_stream(code,0,len(code),len(s.data)).data!=s.data:raise ValueError('Lossless recompression mismatch')
        for f in groups[o]:replacements[f['index']]=code
        required-=gain;savings.append({'frames':[f['index'] for f in groups[o]],'bytes':gain})
    print(json.dumps({'compression':checks,'required':required,'capacity':available,'lossless_streams':len(savings)}),flush=True)
    if all(r['encoded_bytes']<=r['old_bytes'] for r in checks):
        modified_gfx=gfx
        for r in checks:
            f=bank['frames'][r['frames'][0]];code=replacements[f['index']]
            raw=decode_stream(code,0,len(code),f['tile_count']*128).data
            modified_gfx,_=replace_stream(modified_gfx,f,raw)
        repack={'method':'original_stream_slots','remaining_slack':available-required,'relocated':False}
    else:
        modified_gfx,repack=repack_graphics_bank(gfx,0,replacements)
    changed=[]
    for bi in (0,1):
        a=graphics_bank(gfx,bi);b=graphics_bank(modified_gfx,bi)
        for before,after in zip(a['frames'],b['frames']):
            raw0=decode_stream(gfx,before['offset'],before['limit'],before['tile_count']*128).data
            raw1=decode_stream(modified_gfx,after['offset'],after['limit'],after['tile_count']*128).data
            if raw0!=raw1:
                n=before['index']
                if bi!=0 or n not in IDS:raise ValueError('Unrelated raw bitmap changed')
                rendered=compose_indices(raw1,after['tile_count'],composition_frame(parts,0,n))
                if rendered[:2]!=(frames[n][0],tuple(frames[n][1])):raise ValueError('Displayed pixels differ from approved input')
                changed.append(n)
    if sorted(changed)!=sorted(IDS):raise ValueError('Idle references missing')
    result=bytearray(arc);result[gm['offset']:gm['offset']+gm['size']]=modified_gfx;result[pm['offset']:pm['offset']+32]=palette
    allowed=[(gm['offset']+bank['base'],gm['offset']+bank['end']),(pm['offset'],pm['offset']+32)]
    if len(result)!=len(arc) or any(a!=b and not any(lo<=i<hi for lo,hi in allowed) for i,(a,b) in enumerate(zip(arc,result))):raise ValueError('ARC mutation escaped approved ranges')
    report={'frames':list(IDS),'compressed_streams':checks,'recompression':savings,'repack':repack,'all_444_raw_references_checked':True,'modified_display_frames':changed,'bank1_unchanged':True,'composition_unchanged':True,'animation_unchanged':True,'sequence':SEQUENCE,'duration_ticks':TICKS,'palette_row':0,'other_palette_rows_unchanged':True,'palette_intermediate_limitation':'미제작 제로 동작도 공유 행0의 린 색상으로 표시됨','gpu_boundaries_safe_both_directions':True,'art_recipe_sha256':digest(art/'recipe.json'),'modified_archive_sha256':sha(result),'allowed_archive_ranges':allowed}
    return project,profile,bytes(result),report

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--art-dir',type=Path,default=ART);args=p.parse_args()
    art=args.art_dir.resolve();project,profile,arc,report=prepare(art)
    (art/'static_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    if not args.build:return
    out=ROOT/'out/ver_rin_nana'/('rin_idle_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True)
    source=ROOT/project['source_bin'];target=out/'rin_nana.bin'
    first=ROOT/'completed/ver_buki_riko/v1.0.0/ClicheX4_Shibuki_Riko_v1.0.0.bin'
    if digest(first)!='8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a':raise ValueError('Protected first release differs')
    result=write_archive_copy(source,target,profile['zero_archive'],arc,profile['source_sha256'])
    (out/'rin_nana.cue').write_text(working_cue((ROOT/project['source_cue']).read_text('utf-8-sig'),'rin_nana.bin'),'ascii',newline='')
    (out/'modified.arc').write_bytes(arc)
    changed={r['lba'] for r in result['changed_sectors']};readback=bytearray();count=0
    with source.open('rb') as a,target.open('rb') as b:
        while True:
            x=a.read(2352);y=b.read(2352)
            if not x:break
            if (x!=y)!=(count in changed):raise ValueError('Unexpected changed sector')
            if count in changed:validate_checks(y)
            rec=profile['zero_archive']
            if rec['lba']<=count<rec['lba']+(rec['size']+2047)//2048:readback.extend(y[24:2072])
            count+=1
    if readback[:len(arc)]!=arc:raise ValueError('BIN reextraction differs')
    if digest(source)!=profile['source_sha256'] or digest(first)!='8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a':raise ValueError('Protected input changed')
    report.update({'all_disc_sectors_compared':count,'changed_sector_count':len(changed),'changed_sector_edc_ecc_valid':True,'reextracted_arc_equal':True,'source_and_completed_release_preserved':True})
    manifest={'project':'ver_rin_nana','task':'zero_rin','kind':'idle_production','source_sha256':profile['source_sha256'],'modified_bin':result,'modified_archive_sha256':sha(arc),'verification':report,'runtime_verified':False,'known_limit':'이번 적용은 대기6참조. 이동·공격·UI·대사는 아직 원작이며 미교체 몸의 공유 팔레트는 린 색으로 표시됨.'}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'frames':list(IDS),'art':art.relative_to(ROOT).as_posix(),'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed),'remaining_slack':report['repack']['remaining_slack']}))

if __name__=='__main__':main()
