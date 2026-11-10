"""Nana 최종 F3 trial의 실제 캡처와 SPU 읽기 증거를 독립 대조한다."""
import argparse,gzip,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_nana_progress_refresh import read_assets,entry,loaded_vab_header,native_audio_check,active_composite
from scripts.overhaul_audio_verify_cpu import banks
from src.psx_player import graphics_bank,bank_offsets,decode_stream
BIN=ROOT/'out/ver_rin_nana/overhaul_20261105_candidate04/rin_nana.bin'
BIN_SHA='1a2d97272bb0dde2395aa7f1daa9136dd247125456090ff519fe3c484e3be2e2'
CLONE=ROOT/'work/overhaul_20261105/audio/nana_user_progress_candidate04_final_v1/SLUS_005.61.000'
CLONE_SHA='57977106f9bf2a8fae08834c94225fdcdf477d895e82256510e7a745f5259440'
SOURCE=ROOT/'work/overhaul_20261105/baseline/current_progress/SLUS_005.61.000'
SOURCE_SHA='736cdc2dc277767d2e4c8b935137bc9ad5ab07ff8074323e0b2f710070657719'
OUT=ROOT/'work/overhaul_20261105/runtime/nana_final_checkpoint_trial/live_verification.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
def require(v,msg):
    if not v:raise ValueError(msg)
def main(a):
    require(not OUT.exists(),'Live report already exists');require(digest(BIN)==BIN_SHA and digest(CLONE)==CLONE_SHA and digest(SOURCE)==SOURCE_SHA,'Protected input changed')
    capture=a.capture.resolve();probe=a.spu_evidence.resolve();meta=json.loads((capture/'evidence.json').read_text('utf8'));audio=json.loads(probe.read_text('utf8'))
    require(meta['bin_sha256']==BIN_SHA and meta['pid']==audio['pid'],'Captures are different build/process')
    require(len(meta['ram_bases'])==len(meta['vram_bases'])==1,'Ambiguous RAM/VRAM capture');rb=meta['ram_bases'][0];vb=meta['vram_bases'][0]
    require(audio['ram_base']==rb,'SPU probe source RAM differs');ram=(capture/f'ram_{rb}.bin').read_bytes();vram=(capture/f'vram_{vb}.bin').read_bytes();require(len(ram)==0x200000 and len(vram)==0x100000,'Bad capture size')
    files=read_assets(BIN);arc=files['PL02_U.ARC'];ref=gzip.decompress(CLONE.read_bytes());reference_player=ref[442+0x1418c8:442+0x1418c8+228];p=ram[0x1418c8:0x1418c8+228]
    for addr in (0x1540c,0x15ecc,0x16ff4,0x233c8):require(ram[addr:addr+64]==files['SLUS_005.61'][addr-0x10000+2048:addr-0x10000+2112],'EXE anchor mismatch')
    def progress(ram,player):return dict(character=player[2],hp=player[0x5c],weapon=player[0x93],armor=player[0xa7],arm_type=player[0xb8],ultimate=ram[0x1721f7],stage=ram[0x1721cc],area=ram[0x1721cd],world_raw=list(struct.unpack_from('<ii',player,8)))
    before=progress(ref[442:442+0x200000],reference_player);actual=progress(ram,p);require(before==actual,'Live player progress differs from protected clone')
    resident={}
    for kind in (2,3,9,0x15):
        b=entry(arc,kind);at=ram.find(b);require(at>=0 and ram.find(b,at+1)<0,'Full resident resource missing/ambiguous '+hex(kind));resident[hex(kind)]=dict(ram_offset=at,size=len(b),sha256=sha(b))
    for name in ('MOJIPAT.ARC',):
        b=files[name];at=ram.find(b);require(at>=0 and ram.find(b,at+1)<0,'Full resident menu differs');resident[name]=dict(ram_offset=at,size=len(b),sha256=sha(b))
    g=entry(arc,2);parts=entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);frame=p[0x47];fr=bank['frames'][frame];expected=decode_stream(g,fr['offset'],fr['limit'],fr['tile_count']*128).data
    gp,cp=struct.unpack_from('<II',p,0x38);require(gp==0x80000000+resident['0x2']['ram_offset']+bank['base'] and cp==0x80000000+resident['0x3']['ram_offset']+bank_offsets(parts)[0],'Active bank pointers mismatch')
    require(ram[0x16dea8:0x16dea8+len(expected)]==expected,'Active decoded RAM differs')
    gpu=b''.join(vram[(first//16*16+y)*2048+640:(first//16*16+y)*2048+640+min(16,fr['tile_count']-first)*8] for first in range(0,fr['tile_count'],16) for y in range(16));require(gpu==expected,'Active GPU upload differs')
    static=entry(arc,0x10206);read_static=b''.join(vram[(176+y%80)*2048+640+(y//80)*128:(176+y%80)*2048+640+(y//80)*128+128] for y in range(len(static)//128));require(static==read_static,'Static player/UI atlas differs')
    persistent=entry(files['LOAD_U.ARC'],0x10008);require(b''.join(vram[(256+y)*2048+1792:(256+y)*2048+1920] for y in range(256))==persistent,'Persistent save UI atlas differs')
    pals={}
    def palette(c):
        at=(c>>6)*2048+(c&63)*32;b=vram[at:at+32];rows=[i for i in range(len(entry(arc,9))//32) if entry(arc,9)[i*32:(i+1)*32]==b];require(rows,'Live CLUT outside target palettes');pals[hex(c)]=dict(sha256=sha(b),matching_rows=rows);return b
    image=active_composite(gpu,fr['tile_count'],parts,palette,p)
    starts=struct.unpack_from('<4I',ram,0x141f30);cmds=struct.unpack_from('<4I',ram,0x141f50);loaded=banks(arc);spus=audio['spu_candidates'];require(len(spus)==1,'SPURAM not uniquely authenticated');spu_info=spus[0];spu_file=probe.parent/f"spuram_{spu_info['host_base']}.bin";spu=spu_file.read_bytes();require(len(spu)==0x80000 and sha(spu)==spu_info['sha256'],'SPURAM capture hash differs');sound=[]
    for slot,(h,b,q) in loaded.items():
        at=(cmds[slot]&0x1fffffff)-8;wanted=loaded_vab_header(h,b,starts[slot]);require(ram[at:at+len(wanted)]==wanted and spu[starts[slot]:starts[slot]+len(b)]==b,'Full live VAB/SPURAM bank differs')
        for table,target in ((0x141840,at+q['vab_offset']),(0x1406b8,at+q['vab_offset']+32),(0x141888,at+q['vab_offset']+32+2048)):
            require(struct.unpack_from('<I',ram,table+slot*4)[0]&0x1fffffff==target,'Live SDK pointer cache differs')
        require(struct.unpack_from('<I',ram,0x175ea8+slot*4)[0]==starts[slot] and struct.unpack_from('<I',ram,0x175e58+slot*4)[0]==len(b),'Live SDK transfer cache differs')
        sound.append(dict(bank=slot,spu_start=starts[slot],body_bytes=len(b),body_sha256=sha(b),ram_header=hex(at),header_sha256=sha(wanted),complete_header_and_body_match=True,sdk_caches_match=True))
    sdk=native_audio_check(ram,files['ST6_1_1.ARC']);require(digest(CLONE)==CLONE_SHA and digest(SOURCE)==SOURCE_SHA and digest(BIN)==BIN_SHA,'Protected inputs changed')
    report=dict(passed=True,target_bin=BIN.relative_to(ROOT).as_posix(),target_bin_sha256=BIN_SHA,source_state=SOURCE.relative_to(ROOT).as_posix(),source_state_sha256=SOURCE_SHA,refreshed_trial_state=CLONE.relative_to(ROOT).as_posix(),refreshed_trial_state_sha256=CLONE_SHA,capture=capture.relative_to(ROOT).as_posix(),pid=meta['pid'],ram_host_base=rb,vram_host_base=vb,progress_before=before,progress_live=actual,progress_matches=True,resident_assets=resident,active_frame=frame,active_tile_count=fr['tile_count'],active_decoded_ram_gpu_sha256=sha(expected),active_ram_gpu_and_bank_pointers_match=True,active_composite_rgba_sha256=sha(image.tobytes()),palettes=pals,static_player_atlas_equal=True,persistent_save_ui_atlas_equal=True,live_spu_evidence=probe.relative_to(ROOT).as_posix(),spu_host_base=spu_info['host_base'],sound_banks=sound,native_sdk_checks_from_live_ram=sdk,source_files_modified=False,process_memory_written=False,keys_sent=False,scope='최종 candidate04용 진행 보존 F1을 루트가 F3로 불러온 후 실제 ePSXe RAM/VRAM/SPURAM을 읽은 검증. fresh 디스크 로딩, 전체 동작 실기, 음향 청취 검증과 구분.',limitations=['현재 관측 프레임과 캐시/진행값을 검증했다.','native SDK5호출은 실제 캡처 RAM을 격리 CPU에 넣어 실행했다. 피콕 ST6 명령표는 그 CPU 시험에만 임시 배치했다.','실제 화면 전체 픽셀 대조·청취 출력은 검사하지 않았다.'])
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(output=str(OUT),passed=True,frame=frame,tiles=fr['tile_count'],banks=len(sound),sdk_checks=len(sdk))))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--spu-evidence',type=Path,required=True);main(p.parse_args())
