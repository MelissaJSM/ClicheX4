"""사용자 카드·진행을 보존하고 새 테스트 카드의 Ultimate 플래그만 설정한다."""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_ultimate_start import D,require,write
from scripts.project import digest
from scripts.discover_inputs import sha256

def main():
    c=json.loads((ROOT/'projects/ver_rin_nana/nana_ultimate_candidate.json').read_text('utf8'));require(c['full_animation_production_approved'],'Production approval missing')
    source=ROOT/'work/ver_rin_nana/test_cards/nana_fourth_idle_v1';out=D/'test_cards_v1';require(not out.exists(),'Fresh test directory required')
    data=(source/'epsxe001.mcr').read_bytes();require(sha256(data)=='ab68aa740dd7a93b8b01b4b4b9cf1a57dab11c9900052879bfbc665499bf120f' and len(data)==131072 and data[:2]==b'MC','Unexpected card')
    directory=data[128:256];checksum=0
    for b in directory[:127]:checksum^=b
    require(checksum==directory[127] and directory[10:30].split(b'\0')[0]==b'BASLUS-00561','Wrong directory')
    offset=8192+512+2*42;slot=data[offset:offset+42];require(tuple(slot[i] for i in (0,1,2,3,4,41))==(0,48,2,15,255,0),'Unexpected DATA3')
    target=bytearray(data);target[offset+41]=1;changed=[i for i,(a,b) in enumerate(zip(data,target)) if a!=b];require(changed==[offset+41],'Other save data changed')
    out.mkdir();(out/'card2_ultimate.mcr').write_bytes(target);shutil.copyfile(source/'epsxe000.mcr',out/'card1_copy.mcr')
    require((source/'epsxe001.mcr').read_bytes()==data,'Source changed')
    write(out/'preparation.json',{'task':'ultimate_armor_nana','method':'isolated clone; acquired Ultimate mode flag only; not a native capsule acquisition test','source':source.relative_to(ROOT).as_posix(),'source_card2_sha256':sha256(data),'card2_sha256':sha256(target),'card1_sha256':digest(out/'card1_copy.mcr'),'changed_offsets':changed,'game_executable_changed':False,'runtime_loaded':False})
    print(json.dumps({'output':str(out),'changed_offsets':changed}))
if __name__=='__main__':main()
