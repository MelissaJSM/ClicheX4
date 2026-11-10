"""User-authorized Ultimate unlock on an isolated copy of card 2, DATA3."""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.emulator_session import EMULATOR

def main():
    out=D/'test_save';out.mkdir(exist_ok=False);backup=out/'original_backup';backup.mkdir()
    paths=[EMULATOR.parent/'memcards/epsxe000.mcr',EMULATOR.parent/'memcards/epsxe001.mcr',EMULATOR.parent/'sstates/SLUS_005.61.000',EMULATOR.parent/'sstates/SLUS_005.61.000.pic'];rows=[]
    for p in paths:
        before=digest(p);shutil.copyfile(p,backup/p.name)
        if digest(p)!=before or digest(backup/p.name)!=before:raise ValueError('Input changed while backing up')
        rows.append({'source':str(p.relative_to(ROOT)),'backup':str((backup/p.name).relative_to(ROOT)),'sha256':before})
    source=backup/'epsxe001.mcr';data=source.read_bytes()
    if sha256(data)!='ab68aa740dd7a93b8b01b4b4b9cf1a57dab11c9900052879bfbc665499bf120f' or len(data)!=131072 or not data.startswith(b'MC'):raise ValueError('Unexpected full armor source card')
    directory=data[128:256];checksum=0
    for b in directory[:127]:checksum^=b
    if checksum!=directory[127] or directory[10:30].split(b'\0')[0]!=b'BASLUS-00561':raise ValueError('Wrong game directory')
    offset=8192+512+2*42;slot=data[offset:offset+42]
    if (slot[0],slot[1],slot[2],slot[3],slot[4],slot[41])!=(0,48,2,15,255,0):raise ValueError('Wrong source slot progress')
    # US save/load instructions: record+0x29 <-> engine 0x801721F7.
    # The same engine flag selects PL02; armor 0x0F and arm type2 already exist.
    target=bytearray(data);target[offset+41]=1;changed=[i for i,(a,b) in enumerate(zip(data,target)) if a!=b]
    if changed!=[offset+41] or target[offset:offset+41]!=slot[:41]:raise ValueError('Unlock changed unrelated progress')
    (out/'card2_ultimate.mcr').write_bytes(target);shutil.copyfile(backup/'epsxe000.mcr',out/'card1_copy.mcr')
    for r in rows:
        if digest(ROOT/r['source'])!=r['sha256']:raise ValueError('Original save changed')
    report={'task':'ultimate_armor_shibuki','user_request':'내가 얼티밋 아머 치트를 모르거든? 너가 치트활성화를 해줘야할거같은데','method':'isolated memory-card clone; DATA3 Ultimate mode flag only','source_card_sha256':sha256(data),'output_sha256':sha256(target),'card_number':2,'slot_number':3,'changed_card_offsets':changed,'source_slot_hex':slot.hex(),'output_slot_hex':bytes(target[offset:offset+42]).hex(),'originals':rows,'eight_bosses_and_hp_armor_preserved':True,'game_exe_changed':False,'runtime_loaded':False}
    (out/'unlock.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'output':str(out),'changed_offsets':changed,'sha256':sha256(target)}))

if __name__=='__main__':main()
