"""포스아머 저장·캡슐 그래픽3자원을 별도 BIN에 적용하고 전 섹터를 검증한다."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_fourth_ui import PARENT,PARENT_SHA,SOURCES,read_sources,verify
from scripts.prepare_nana_fourth_pilot import require,write
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def validate(art,reproduced):
    for p in (art,reproduced):require(p.resolve().is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_ui'),'Unexpected prepared path')
    original,records=read_sources();r=json.loads((art/'recipe.json').read_text('utf8'));r2=json.loads((reproduced/'recipe.json').read_text('utf8'));require(r==r2,'Recipe reproduction differs')
    require(r['parent_sha256']==PARENT_SHA and r['parent']==PARENT.relative_to(ROOT).as_posix() and r['kind']=='nana_fourth_save_capsule' and r['task']=='fourth_armor_nana','Wrong parent/scope')
    require(r['sources']==records and r['save_frames']==[45,46,47,48] and set(r['files'])==set(SOURCES),'Source metadata changed')
    names={p.name for p in art.iterdir() if p.is_file()};require(names=={p.name for p in reproduced.iterdir() if p.is_file()},'Reproduction file set differs')
    for name in names:require((art/name).read_bytes()==(reproduced/name).read_bytes(),'Reproduction differs: '+name)
    edited={name:(art/name).read_bytes() for name in SOURCES}
    for name,data in edited.items():require(sha256(data)==r['files'][name],'Prepared hash differs')
    proof=verify(original,edited);require(proof==r['verification'],'Prepared claims differ');return r,records,edited,proof,names

def build(art,reproduced):
    r,records,edited,proof,names=validate(art.resolve(),reproduced.resolve());pointer=ROOT/'projects/ver_rin_nana/current_build.json';before=pointer.read_bytes();current=json.loads(before);require(current['sha256']==PARENT_SHA,'Active build changed')
    protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protect():
        require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent changed')
        for q in protection['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed: '+q['path'])
    protect();out=ROOT/'out/ver_rin_nana'/('nana_fourth_ui_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();replacements=[(q,edited[q['name'].split(';')[0]]) for q in records];result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',replacements,PARENT_SHA);changed={q['lba'] for q in result['changed_sectors']};total=(PARENT/'rin_nana.bin').stat().st_size//2352
    with (PARENT/'rin_nana.bin').open('rb') as a,(out/'rin_nana.bin').open('rb') as b:
        for lba in range(total):
            x,y=a.read(2352),b.read(2352);require(len(x)==len(y)==2352 and (x!=y)==(lba in changed),'Unexpected changed/truncated sector')
            if lba in changed:
                require(x[:24]==y[:24] and any(q['lba']<=lba<q['lba']+(q['size']+2047)//2048 for q in records),'Change outside intended resources');validate_checks(y)
        require(not b.read(1),'Output grew')
    with (out/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,result['size']);iso={q['name']:q for q in d.inspect()['files']}
        for q,data in replacements:require(d.read(q['lba'],q['size'])==data,'Resource readback differs')
        for name in ('PL01_U.ARC','PL02_U.ARC'):
            q=iso[name+';1'];require(d.read(q['lba'],q['size'])==(PARENT/name).read_bytes(),'Rin/Ultimate changed')
    protect()
    for name in ('rin_nana.cue','PL01_U.ARC','PL02_U.ARC'):shutil.copyfile(PARENT/name,out/name)
    (out/'modified.arc').write_bytes(edited['PL00_U.ARC']);shutil.copytree(art,out/'fourth_ui');write(out/'previous_current_build.json',json.loads(before));write(out/'preservation.json',protection)
    v={**proof,'all_disc_sectors_compared':total,'changed_sectors':sorted(changed),'edc_ecc_checked':True,'three_resources_readback_identical':True,'all_other_disc_bytes_preserved':True,'protected_files':len(protection['files']),'independent_preparation_files':len(names),'runtime_verified':False}
    m=json.loads((PARENT/'manifest.json').read_text('utf8'));m.update(kind='nana_fourth_save_capsule',task='fourth_armor_nana',parent=PARENT.relative_to(ROOT).as_posix(),parent_sha256=PARENT_SHA,modified_bin=result,modified_archive_sha256=sha256(edited['PL00_U.ARC']),inherited_manifest=(PARENT/'manifest.json').relative_to(ROOT).as_posix(),inherited_verification=m['verification'],verification=v,runtime_verified=False,added_fourth_armor_frames=[],fourth_ui_recipe=(out/'fourth_ui/recipe.json').relative_to(ROOT).as_posix());write(out/'manifest.json',m);write(out/'verification.json',v)
    require(pointer.read_bytes()==before,'Active pointer changed during build');current.update(build=out.relative_to(ROOT).as_posix(),cue=(out/'rin_nana.cue').relative_to(ROOT).as_posix(),sha256=result['sha256'],current_session=None,runtime_verified=False,fourth_armor_vehicle_user_accepted=True,fourth_ui_user_accepted=False,fourth_ui_report='docs/NANA_FOURTH_UI.md',next_scope='Fourth Armor save UI/capsule runtime review; then completion review and Ultimate pilot');write(pointer,current)
    print(json.dumps({'build':out.relative_to(ROOT).as_posix(),'sha256':result['sha256'],'changed_sectors':len(changed),'independent_files':len(names)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);a=p.parse_args();build(a.art,a.reproduced)
