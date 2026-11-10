"""검증된 에뮬레이터와 카드의 읽기 전용 원천에서 두 번째 버전 전용 사본 준비."""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.emulator_session import EXE_HASH,EMULATOR

def main():
    source=EMULATOR.parent;dest=ROOT/'work/ver_rin_nana/emulator';cards=ROOT/'work/ver_rin_nana/test_cards/idle_v1'
    if dest.exists() or cards.exists():raise ValueError('Existing isolated emulator/cards must not be overwritten')
    if digest(EMULATOR)!=EXE_HASH:raise ValueError('Unverified emulator')
    before={str(p.relative_to(source)):digest(p) for folder in ('memcards','sstates') for p in (source/folder).rglob('*') if p.is_file()}
    dest.mkdir(parents=True);cards.mkdir(parents=True)
    for p in source.iterdir():
        if p.is_file():shutil.copy2(p,dest/p.name)
        elif p.name in ('bios','config','plugins','shaders'):shutil.copytree(p,dest/p.name)
        else:(dest/p.name).mkdir()
    copies=[]
    for index,name in enumerate(('epsxe000.mcr','epsxe001.mcr')):
        path=source/'memcards'/name
        if path.stat().st_size!=131072:raise ValueError('Unexpected source card')
        output=cards/name;shutil.copy2(path,output)
        if digest(output)!=digest(path):raise ValueError('Card copy mismatch')
        copies.append({'slot':index,'source':str(path.relative_to(ROOT)),'copy':str(output.relative_to(ROOT)),'sha256':digest(output)})
    for relative,value in before.items():
        if digest(source/relative)!=value:raise ValueError('Source save changed')
    report={'exe_sha256':digest(dest/'ePSXe.exe'),'isolated_executable':str((dest/'ePSXe.exe').relative_to(ROOT)),'cards':copies,'protected_saves':before,'original_saves_preserved':True,'save_states_copied':False,'registry_modified':False}
    (dest/'provision.json').write_text(json.dumps(report,indent=2)+'\n','utf-8')
    print(json.dumps({'emulator':str(dest),'cards':copies,'protected_source_files':len(before)}))

if __name__=='__main__':main()
