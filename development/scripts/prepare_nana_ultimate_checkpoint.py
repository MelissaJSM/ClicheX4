"""얼티밋 획득 전 대기 저장의 그래픽만 갱신하고 진행·해금 상태를 보존한다."""
import argparse,gzip,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_ultimate_start import PARENT,PARENT_SHA,entry,require,write
from scripts.project import digest
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,decode_stream
from src.epsxe_state import locate_vram
BUILD=ROOT/'out/ver_rin_nana/nana_ultimate_start_20261030T131517719423Z'
BUILD_SHA='b2888964e995b0d63b2d862921a938fa2de59454dee5175fb55e5d697179c94e'

def refresh(state,old,new,menu_old,menu_new):
    require(len(state)==4254418 and state.startswith(b'ePSXe\x06\x00SLUS_005.61'),'Unsupported state')
    rp=442;ram=state[rp:rp+0x200000];player=ram[0x1418c8:0x1418c8+228];n=player[0x47]
    require(player[2]==0 and player[0x17]==5 and n in (0,115,116,117,118,119) and player[0xa7]==0 and player[0x93]==0 and ram[0x1721f7]==1,'Expected unarmored Ultimate idle')
    cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text());exe=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.exe').read_bytes();addr=cfg['idle_sequence_address'];off=2048+addr-cfg['executable']['load_address'];anchor=exe[off:off+48]
    require(ram[addr&0x1fffff:(addr&0x1fffff)+48]==anchor,'Unexpected US RAM layout')
    dst=bytearray(state);allowed=bytearray(len(state));ranges=[]
    def replace(pos,a,b,name):
        require(len(a)==len(b) and state[pos:pos+len(a)]==a,'Unexpected asset: '+name)
        dst[pos:pos+len(b)]=b;allowed[pos:pos+len(b)]=b'\1'*len(b);ranges.append({'kind':name,'offset':pos,'size':len(b),'before_sha256':sha256(a),'after_sha256':sha256(b)})
    assets=[(f'PL02 entry {k}',entry(old,k),entry(new,k)) for k in (2,3,9)]+[('MOJIPAT',menu_old,menu_new)]
    for name,a,b in assets:
        pos=ram.find(a);require(pos>=0 and ram.find(a,pos+1)<0,'Nonunique or missing asset: '+name);replace(rp+pos,a,b,name)
    # SP(0x024/0x028)는 색상 원본 은행과 실제 업로드 색상 버퍼를 가리킨다.
    # 원본 은행만 바꾸면 다음 전체 팔레트 업로드가 이전 몸색을 다시 덮는다.
    bankaddr=ram.find(entry(old,9))|0x80000000;needle=struct.pack('<I',bankaddr);scratch_hits=[];pos=0x200000
    while True:
        pos=state.find(needle,pos,0x270000)
        if pos<0:break
        ptr=struct.unpack_from('<I',state,pos+4)[0]
        if 0x80000000<=ptr<0x80200000 and ram[ptr&0x1fffff:(ptr&0x1fffff)+32]==entry(old,9)[:32]:scratch_hits.append((pos-0x24,ptr&0x1fffff))
        pos+=1
    require(len(scratch_hits)==1,'Nonunique active palette scratchpad pointer');scratch,active=scratch_hits[0]
    replace(rp+active,entry(old,9)[:32],entry(new,9)[:32],'RAM active body palette')
    replace(rp+0x141f70,entry(old,9)[:32],entry(new,9)[:32],'RAM filtered body palette')
    dec=[];frames=[]
    for arc in (old,new):
        g=entry(arc,2);f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];frames.append(f);dec.append(decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data)
    a,b=dec;tiles=frames[0]['tile_count'];require(tiles==frames[1]['tile_count'],'Active tile count changed');replace(rp+0x16dea8,a,b,'RAM active texture');vr=locate_vram(state,a,tiles);cursor=0
    for first in range(0,tiles,16):
        width=min(16,tiles-first)*8
        for y in range(16):
            pos=vr+(first//16*16+y)*2048+640;replace(pos,a[cursor:cursor+width],b[cursor:cursor+width],'VRAM active texture row');cursor+=width
    clut=struct.unpack_from('<H',player,0x42)[0];require(clut==0x7800,'Unexpected default body CLUT');palpos=vr+(clut>>6)*2048+(clut&63)*32
    replace(palpos,entry(old,9)[:32],entry(new,9)[:32],'VRAM active body palette')
    changes=[i for i,(a,b) in enumerate(zip(state,dst)) if a!=b];require(all(allowed[i] for i in changes),'Nonasset change');require(dst[rp+0x1418c8:rp+0x1418c8+228]==player and dst[rp+0x1721c0:rp+0x172224]==state[rp+0x1721c0:rp+0x172224],'Player or engine changed')
    return bytes(dst),{'ram_offset':rp,'vram_offset':vr,'scratchpad_offset':scratch,'active_palette_ram_offset':active,'frame':n,'world':[struct.unpack_from('<i',player,o)[0]/65536 for o in (8,12)],'hp':player[0x5c],'armor':0,'ultimate':1,'changed_bytes':len(changes),'asset_ranges':ranges,'all_nonasset_bytes_preserved':True,'player_and_engine_bytes_preserved':True,'evidence_kind':'graphics-refreshed checkpoint, not fresh disc loading'}

def main(source,source_sha,output):
    source,output=source.resolve(),output.resolve();root=ROOT/'work/ver_rin_nana/checkpoints';require(source.is_relative_to(root) and output.is_relative_to(root) and not output.exists() and source!=output,'Fresh isolated output required')
    require(digest(source)==source_sha and digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(BUILD/'rin_nana.bin')==BUILD_SHA,'Source/build identity changed')
    old=(PARENT/'PL02_U.ARC').read_bytes();new=(BUILD/'PL02_U.ARC').read_bytes();require(sha256(old)=='1fd806088d6ffb0f655a53fe6cd6961eb839dface1a735ccedf3ac42b2bc6c94' and sha256(new)=='fbd74583c552b86c9298fa6b3d27cbe160f9c430bdffce06509257ae6ca61e7f','ARC changed')
    menu_old=(PARENT/'fourth_ui/MOJIPAT.ARC').read_bytes();menu_new=(BUILD/'ultimate_start/MOJIPAT.ARC').read_bytes();state=gzip.decompress(source.read_bytes());updated,report=refresh(state,old,new,menu_old,menu_new);again,_=refresh(state,old,new,menu_old,menu_new);require(updated==again,'Independent refresh differs')
    rejects=[]
    for label,offset in [('wrong_mode',442+0x1721f7),('active_texture',442+0x16dea8),('resource',442+state[442:442+0x200000].find(entry(old,3))),('palette',report['vram_offset']+480*2048),('active_palette',442+report['active_palette_ram_offset']),('filtered_palette',442+0x141f70)]:
        bad=bytearray(state);bad[offset]^=1
        try:refresh(bytes(bad),old,new,menu_old,menu_new)
        except ValueError:rejects.append(label)
        else:raise ValueError('Accepted invalid '+label)
    output.parent.mkdir(parents=True,exist_ok=True);packed=gzip.compress(updated,mtime=0);output.write_bytes(packed);require(digest(source)==source_sha,'Source state changed');report.update(source=source.relative_to(ROOT).as_posix(),source_sha256=source_sha,output_sha256=sha256(packed),build=BUILD.relative_to(ROOT).as_posix(),build_sha256=BUILD_SHA,reproduced_identical=True,rejected_corrupt_inputs=rejects);write(output.parent/'refresh.json',report);print(json.dumps({k:v for k,v in report.items() if k!='asset_ranges'}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--source-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.source,a.source_sha256,a.output)
