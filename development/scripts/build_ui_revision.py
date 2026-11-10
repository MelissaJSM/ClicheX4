"""Build the hash-bound UI/capsule revision and approved one-byte death CLUT fix."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_ui_revision import PARENT,PARENT_SHA,D
from scripts.discover_inputs import DiscReader,sha256
from scripts.project import digest,working_cue,load_project,inspect_references
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

APPROVAL='수정해도 전혀 문제없으니까 수정 바로진행해도좋아'
EXE_SHA='dae43d44a9f3176208830ddbba0607bb627ebcd7faf9b36fc03dd0ffda34d2e8'
DEATH_OFFSET=0xBB67C

def patch_death_exe(exe):
    if sha256(exe)!=EXE_SHA:raise ValueError('Unsupported executable hash')
    if exe[DEATH_OFFSET:DEATH_OFFSET+4]!=bytes.fromhex('02780224'):raise ValueError('Unexpected death CLUT instruction')
    out=exe[:DEATH_OFFSET]+b'\0'+exe[DEATH_OFFSET+1:]
    if [i for i,(a,b) in enumerate(zip(exe,out)) if a!=b]!=[DEATH_OFFSET]:raise ValueError('Executable change exceeds approval')
    return out

def build(candidate):
    candidate=candidate.resolve()
    if not candidate.is_relative_to(D):raise ValueError('Candidate outside UI work directory')
    recipe=json.loads((candidate/'recipe.json').read_text('utf8'))
    if recipe['parent_bin_sha256']!=PARENT_SHA or not recipe['death_exe_patch_required'] or recipe['gangzi_art_pending']:raise ValueError('Incomplete/wrong candidate')
    if APPROVAL not in (ROOT/'docs/DECISIONS.md').read_text('utf8'):raise ValueError('Executable approval not recorded')
    parent=PARENT/'shibuki_riko.bin';project=load_project(ROOT,'ver_buki_riko');inspect_references(ROOT,project)
    if digest(parent)!=PARENT_SHA or digest(ROOT/project['source_bin'])!=project['source_sha256']:raise ValueError('Game source hash changed')
    if digest(ROOT/'character/dr_light/light.webp')!='be98e4bb8fef1d4b19c5a1d98433422a497e8fe1c581f04ea015789299edfccf':raise ValueError('GangZi reference changed')
    replacements=[];payloads={};arcs={}
    with parent.open('rb') as f:
        reader=DiscReader(f,parent.stat().st_size)
        for item in recipe['files']:
            rec=item['source'];name=item['file'];path=(candidate/name).resolve()
            if path.parent!=candidate:raise ValueError('Invalid candidate file path')
            old=reader.read(rec['lba'],rec['size']);new=path.read_bytes()
            if sha256(old)!=item['parent_sha256'] or sha256(new)!=item['sha256'] or len(new)!=len(old):raise ValueError('Candidate asset binding mismatch')
            replacements.append(({**rec,'sha256':sha256(old)},new));arcs[name]=new
        rec=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text())['executable'];exe=reader.read(rec['lba'],rec['size']);new=patch_death_exe(exe)
        replacements.append((rec,new));arcs['SLUS_005.61']=new
    for rec,new in replacements:
        for i in range((len(new)+2047)//2048):payloads[rec['lba']+i]=new[i*2048:(i+1)*2048]
    out=ROOT/'out/ver_buki_riko'/('ui_colors_gangzi_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(exist_ok=False)
    target=out/'shibuki_riko.bin';result=write_archive_copies(parent,target,replacements,PARENT_SHA);expected={r['lba'] for r in result['changed_sectors']};actual=[]
    with parent.open('rb') as a,target.open('rb') as b:
        for sector in range(result['size']//2352):
            before,after=a.read(2352),b.read(2352)
            if before==after:continue
            if sector not in expected or before[:24]!=after[:24]:raise ValueError('Unexpected raw sector change')
            validate_checks(after);chunk=payloads[sector]
            if after[24:24+len(chunk)]!=chunk or after[24+len(chunk):2072]!=before[24+len(chunk):2072]:raise ValueError('Sector payload mismatch')
            actual.append(sector)
    if set(actual)!=expected:raise ValueError('Sector comparison incomplete')
    with target.open('rb') as f:
        reader=DiscReader(f,target.stat().st_size)
        for rec,data in replacements:
            if reader.read(rec['lba'],rec['size'])!=data:raise ValueError('Disc file readback mismatch')
    if digest(parent)!=PARENT_SHA or digest(ROOT/project['source_bin'])!=project['source_sha256']:raise ValueError('Protected input changed')
    inspect_references(ROOT,project)
    (out/'shibuki_riko.cue').write_text(working_cue((PARENT/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),encoding='ascii')
    for name,data in arcs.items():(out/name).write_bytes(data)
    (out/'modified.arc').write_bytes(arcs['PL00_U.ARC'])
    for name in ['review.png','gangzi_capsule_review.png','hq_registration.png'] :shutil.copyfile(candidate/name,out/name)
    manifest={'project':'ver_buki_riko','task':'x_shibuki_ui','active_tasks':['x_shibuki_ui','zero_riko_ui','gangzi_capsule'],'stage':'EXPANSION','kind':'ui_colors_gangzi_candidate','source_sha256':project['source_sha256'],'parent_build':str(PARENT.relative_to(ROOT)),'parent_bin_sha256':PARENT_SHA,'modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},'modified_archive_sha256':sha256(arcs['PL00_U.ARC']),'resource_count':len(replacements),'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352,'archive_sizes_lbas_preserved':True,'exe_changed':True,'exe_change':{'source_sha256':EXE_SHA,'output_sha256':sha256(arcs['SLUS_005.61']),'file_offset':DEATH_OFFSET,'old_bytes':'02780224','new_bytes':'00780224','changed_bytes':1,'user_quote':APPROVAL},'candidate':str(candidate.relative_to(ROOT)),'runtime_verified':False,'user_review_pending':True}
    for name,obj in [('recipe.json',recipe),('manifest.json',manifest),('sector_changes.json',result)]: (out/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(actual),'full_disc_verified':True}));return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();build(a.candidate)
