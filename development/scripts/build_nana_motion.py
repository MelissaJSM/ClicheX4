"""나나 대기/정지 사격을 수용 공통판 사본에 적용하고 전체 디스크를 검사한다."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import PARENT,PARENT_SHA,PILOT,IDS
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
def validate(candidate,reproduced):
    for p in (candidate,reproduced):
        if not p.resolve().is_relative_to(ROOT/'work/ver_rin_nana/nana_production'):raise ValueError('Expected isolated Nana production input')
    recipe=json.loads((candidate/'recipe.json').read_text('utf8'));again=json.loads((reproduced/'recipe.json').read_text('utf8'))
    if recipe!=again or recipe['task']!='x_nana' or recipe['scope']!='idle_and_standing_10' or recipe['parent_sha256']!=PARENT_SHA or recipe['frames']!=list(IDS):raise ValueError('Recipe identity or reproduction differs')
    if digest(PILOT/'nana_000_indexed.png')!=recipe['master_sha256'] or digest(PILOT/'palette.bin')!=recipe['palette_sha256']:raise ValueError('Approved style changed')
    arc=(candidate/'modified.arc').read_bytes()
    if sha256(arc)!=recipe['modified_archive_sha256'] or arc!=(reproduced/'modified.arc').read_bytes():raise ValueError('Modified archive changed')
    for n,h in recipe['frame_sha256'].items():
        if digest(candidate/f'frame_{int(n):03d}.png')!=h or digest(reproduced/f'frame_{int(n):03d}.png')!=h:raise ValueError('Frame art changed')
    rec=json.loads((PARENT/'common/proposal.json').read_text('utf8'))['records']['PL00_U.ARC']
    if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Parent game changed')
    with (PARENT/'rin_nana.bin').open('rb') as f:
        original=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size).read(rec['lba'],rec['size'])
    if sha256(original)!=recipe['parent_archive_sha256'] or len(original)!=len(arc):raise ValueError('Source archive changed')
    return recipe,arc,{**rec,'sha256':sha256(original)}

def build(candidate,reproduced):
    candidate=candidate.resolve();reproduced=reproduced.resolve();recipe,arc,rec=validate(candidate,reproduced)
    protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protected():
        for q in protection['files']:
            if digest(ROOT/q['path'])!=q['expected_sha256']:raise ValueError('Protected file changed: '+q['path'])
        if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Parent changed')
    protected();out=ROOT/'out/ver_rin_nana'/('nana_idle_shot_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',[(rec,arc)],PARENT_SHA)
    changes={q['lba'] for q in result['changed_sectors']};count=0
    with (PARENT/'rin_nana.bin').open('rb') as a,(out/'rin_nana.bin').open('rb') as b:
        while True:
            x,y=a.read(2352),b.read(2352)
            if not x:
                if y:raise ValueError('Output grew')
                break
            if len(x)!=len(y) or (x!=y)!=(count in changes):raise ValueError('Undeclared sector difference')
            if count in changes:
                if x[:24]!=y[:24] or not rec['lba']<=count<rec['lba']+(rec['size']+2047)//2048:raise ValueError('Changed sector escaped X archive')
                validate_checks(y)
            count+=1
    with (out/'rin_nana.bin').open('rb') as f:
        if DiscReader(f,result['size']).read(rec['lba'],rec['size'])!=arc:raise ValueError('Readback differs')
    protected();shutil.copyfile(PARENT/'rin_nana.cue',out/'rin_nana.cue');(out/'modified.arc').write_bytes(arc)
    shutil.copyfile(PARENT/'modified.arc',out/'PL01_U.ARC');shutil.copytree(candidate,out/'art')
    verification={'all_disc_sectors_compared':count,'changed_sectors':len(changes),'edc_ecc_checked':True,'readback_equal':True,
        'protected_files':len(protection['files']),'independent_arc_reproduction':True,'checked_bitmap_references':recipe['checked_bitmap_references'],
        'changed_frames':list(IDS),'rin_and_common_assets_preserved':True,'only_X_archive_changed':True,'runtime_verified':False}
    manifest={'project':'ver_rin_nana','task':'x_nana','kind':'nana_idle_and_standing','stage':'EXPANSION','parent':PARENT.relative_to(ROOT).as_posix(),
        'parent_sha256':PARENT_SHA,'modified_bin':result,'modified_archive_sha256':sha256(arc),'archive':rec,
        'frames':list(IDS),'art':'art','verification':verification,'inherited_rin_manifest':(PARENT/'manifest.json').relative_to(ROOT).as_posix(),
        'style_approved':True,'new_animation_user_accepted':False,'runtime_verified':False,'known_limit':recipe['known_limit']}
    for name,data in [('manifest.json',manifest),('verification.json',verification),('preservation.json',protection)]:write(out/name,data)
    write(ROOT/'projects/ver_rin_nana/current_build.json',{'project':'ver_rin_nana','task':'x_nana','build':out.relative_to(ROOT).as_posix(),
        'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'frames':list(IDS),'art':(out/'art').relative_to(ROOT).as_posix(),
        'rin_inherited_from':PARENT.relative_to(ROOT).as_posix(),'runtime_verified':False})
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changes),'protected':len(protection['files'])}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);a=p.parse_args();build(a.candidate,a.reproduced)
