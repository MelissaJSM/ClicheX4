"""얼티밋 초기10참조를 별도 검증 BIN에 적용. 수용본 포인터는 보존한다."""
import json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.verify_nana_ultimate_start import validate
from scripts.prepare_nana_ultimate_start import D,PARENT,PARENT_SHA,FRAMES,require,write
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def main():
    art=D/'start_v2';repro=D/'start_v2_repro';proof=validate(art);names={p.name for p in art.iterdir()};require(names=={p.name for p in repro.iterdir()},'Reproduction set differs')
    for n in names:require((art/n).read_bytes()==(repro/n).read_bytes(),'Reproduction differs')
    prior=json.loads((D/'start_verification.json').read_text('utf8'));require(all(prior[k]==v for k,v in proof.items()),'Verification changed')
    analysis=json.loads((D/'analysis_v2/analysis.json').read_text('utf8'));require(analysis['parent_sha256']==PARENT_SHA,'Analysis parent changed')
    recipe=json.loads((art/'recipe.json').read_text('utf8'));records=[analysis['resources'][n] for n in recipe['files']];edited={n:(art/n).read_bytes() for n in recipe['files']}
    pointer=ROOT/'projects/ver_rin_nana/current_build.json';before=pointer.read_bytes();require(json.loads(before)['sha256']==PARENT_SHA,'Stable build changed')
    protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protect():
        require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent changed')
        for q in protection['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed: '+q['path'])
    protect()
    with (PARENT/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size)
        for q in records:require(sha256(d.read(q['lba'],q['size']))==q['sha256'],'Source record differs')
    out=ROOT/'out/ver_rin_nana'/('nana_ultimate_start_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    replacements=[(q,edited[q['name'].split(';')[0]]) for q in records];result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',replacements,PARENT_SHA);changed={q['lba'] for q in result['changed_sectors']};total=result['size']//2352
    with (PARENT/'rin_nana.bin').open('rb') as a,(out/'rin_nana.bin').open('rb') as b:
        for lba in range(total):
            x,y=a.read(2352),b.read(2352);require(len(x)==len(y)==2352 and (x!=y)==(lba in changed),'Unexpected sector change')
            if lba in changed:
                require(x[:24]==y[:24] and any(q['lba']<=lba<q['lba']+(q['size']+2047)//2048 for q in records),'Change outside allowed data');validate_checks(y)
        require(not b.read(1),'Output grew')
    with (out/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,result['size']);iso={q['name']:q for q in d.inspect()['files']}
        for q,data in replacements:require(d.read(q['lba'],q['size'])==data,'Resource readback differs')
        for name,file in [('PL00_U.ARC','modified.arc'),('PL01_U.ARC','PL01_U.ARC')]:
            q=iso[name+';1'];require(d.read(q['lba'],q['size'])==(PARENT/file).read_bytes(),'Accepted Nana/Rin changed')
    protect();require(pointer.read_bytes()==before,'Stable pointer changed')
    for n in ('rin_nana.cue','PL01_U.ARC','modified.arc'):shutil.copyfile(PARENT/n,out/n)
    (out/'PL02_U.ARC').write_bytes(edited['PL02_U.ARC']);shutil.copytree(art,out/'ultimate_start');write(out/'preservation.json',protection);write(out/'previous_current_build.json',json.loads(before))
    v={**prior,'all_disc_sectors_compared':total,'changed_sectors':sorted(changed),'edc_ecc_checked':True,'three_resources_readback_identical':True,'all_other_disc_bytes_preserved':True,'protected_files':len(protection['files']),'runtime_verified':False}
    m=json.loads((PARENT/'manifest.json').read_text('utf8'));m.update(kind='nana_ultimate_start',task='ultimate_armor_nana',parent=PARENT.relative_to(ROOT).as_posix(),parent_sha256=PARENT_SHA,modified_bin=result,modified_archive_sha256=sha256(edited['PL02_U.ARC']),inherited_manifest=(PARENT/'manifest.json').relative_to(ROOT).as_posix(),inherited_verification=m['verification'],verification=v,runtime_verified=False,full_ultimate_complete=False,implemented_ultimate_references=FRAMES,pre_acquisition_base_references=214,ultimate_recipe=(out/'ultimate_start/recipe.json').relative_to(ROOT).as_posix());write(out/'manifest.json',m);write(out/'verification.json',v)
    candidate=ROOT/'projects/ver_rin_nana/nana_ultimate_candidate.json';c=json.loads(candidate.read_text('utf8'));c.update(stage='ULTIMATE_START_RUNTIME_PENDING',private_test_build=out.relative_to(ROOT).as_posix(),private_test_bin_sha256=result['sha256'],implemented_ultimate_references=FRAMES,full_ultimate_complete=False);write(candidate,c)
    print(json.dumps({'build':out.relative_to(ROOT).as_posix(),'sha256':result['sha256'],'changed_sectors':len(changed),'stable_pointer_preserved':True}))

if __name__=='__main__':main()
