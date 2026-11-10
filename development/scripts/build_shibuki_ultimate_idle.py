"""Build only the checked PL02 standing pilot on the accepted integrated disc."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import load,D,PARENT,PARENT_SHA,SOURCE_SHA
from scripts.project import digest,working_cue
from scripts.discover_inputs import DiscReader,sha256
from scripts.prepare_riko_ui import entry
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def validate_candidate(candidate,record,parent):
    candidate=candidate.resolve()
    if not candidate.is_relative_to(D):raise ValueError('Candidate outside task')
    recipe=json.loads((candidate/'recipe.json').read_text());check=json.loads((candidate/'regression.json').read_text());data=(candidate/'PL02_U.ARC').read_bytes()
    if recipe['kind']!='ultimate_idle_pilot' or recipe['parent_bin_sha256']!=PARENT_SHA or recipe['parent_arc_sha256']!=sha256(parent) or recipe['source_record']!=record:raise ValueError('Wrong candidate provenance')
    if sha256(data)!=recipe['modified_arc_sha256'] or len(data)!=record['size'] or len(data)!=len(parent):raise ValueError('Candidate hash/size mismatch')
    if not check['passed'] or check['archive_sha256']!=sha256(data) or check['frame_scope']!=[0,115,116,117,118,119]:raise ValueError('Missing matching regressions')
    if recipe['resources_relocated'] or recipe['exe_changed'] or recipe['timing_changed']:raise ValueError('Unexpected mutation scope')
    return recipe,data

def validate_base_candidate(candidate,record,parent):
    from scripts.prepare_shibuki_ultimate_base import EXCLUDED,PILOT_SHA
    candidate=candidate.resolve()
    if not candidate.is_relative_to(D):raise ValueError('Candidate outside task')
    recipe=json.loads((candidate/'recipe.json').read_text());check=json.loads((candidate/'regression.json').read_text());data=(candidate/'PL02_U.ARC').read_bytes()
    if recipe['kind']!='ultimate_pre_capsule_base_fix' or recipe['pilot_arc_sha256']!=PILOT_SHA or recipe['source_arc_sha256']!='b22ef30ca72594a68c182659ff4a23ce115fe4a353249ec1c6d794e27be8791a':raise ValueError('Wrong base correction provenance')
    if sha256(data)!=recipe['modified_arc_sha256'] or len(data)!=record['size'] or len(data)!=len(parent):raise ValueError('Candidate hash/size mismatch')
    if not check['passed'] or check['archive_sha256']!=sha256(data) or check['frame_scope']!=sorted(set(range(237))-EXCLUDED) or check['base_frames_exact']!=214:raise ValueError('Missing matching base regressions')
    if not recipe['all_armor_layers_preserved'] or not recipe['bank_boundaries_sizes_lbas_preserved'] or not recipe['timing_logic_preserved']:raise ValueError('Unexpected correction scope')
    return recipe,data

def build(candidate,base_fix=False):
    candidate=candidate.resolve()
    records,sources=load();record=records['PL02_U.ARC'];recipe,data=(validate_base_candidate if base_fix else validate_candidate)(candidate,record,sources['parent']['PL02_U.ARC'])
    out=ROOT/'out/ver_buki_riko'/(('shibuki_ultimate_base_fix_' if base_fix else 'shibuki_ultimate_idle_')+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(exist_ok=False)
    target=out/'shibuki_riko.bin';parent=PARENT/'shibuki_riko.bin'
    result=write_archive_copies(parent,target,[({**record,'sha256':sha256(sources['parent']['PL02_U.ARC'])},data)],PARENT_SHA);changed={x['lba'] for x in result['changed_sectors']};actual=[]
    with parent.open('rb') as a,target.open('rb') as b:
        for lba in range(result['size']//2352):
            x,y=a.read(2352),b.read(2352)
            if x==y:continue
            if lba not in changed or x[:24]!=y[:24]:raise ValueError('Unexpected disc mutation')
            off=(lba-record['lba'])*2048;chunk=data[off:off+2048]
            if off<0 or not chunk or y[24:24+len(chunk)]!=chunk or y[24+len(chunk):2072]!=x[24+len(chunk):2072]:raise ValueError('Unexpected sector payload')
            validate_checks(y);actual.append(lba)
    if set(actual)!=changed:raise ValueError('Incomplete sector proof')
    with target.open('rb') as f:
        reader=DiscReader(f,target.stat().st_size)
        if reader.read(record['lba'],record['size'])!=data:raise ValueError('PL02 readback differs')
        base=records['PL00_U.ARC']
        if reader.read(base['lba'],base['size'])!=sources['parent']['PL00_U.ARC']:raise ValueError('Accepted base/Fourth modified')
    if digest(parent)!=PARENT_SHA or digest(ROOT/'MegaMan X4.bin')!=SOURCE_SHA:raise ValueError('Protected game changed')
    (out/'shibuki_riko.cue').write_text(working_cue((PARENT/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),encoding='ascii')
    for name in (('PL02_U.ARC','review.png','recipe.json','regression.json') if base_fix else ('PL02_U.ARC','review.png','idle.gif','recipe.json','regression.json')):shutil.copyfile(candidate/name,out/name)
    manifest={'project':'ver_buki_riko','task':'ultimate_armor_shibuki','stage':'EXPANSION','kind':'ultimate_idle_pilot','source_sha256':SOURCE_SHA,'parent_build':str(PARENT.relative_to(ROOT)),'parent_bin_sha256':PARENT_SHA,'modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},'modified_archive_sha256':sha256(data),'resource':'PL02_U.ARC','resource_count':1,'full_disc_sectors_compared':result['size']//2352,'changed_sectors':len(actual),'candidate':str(candidate.relative_to(ROOT)),'base_fourth_riko_ui_preserved':True,'archive_sizes_lbas_preserved':True,'exe_changed':False,'animation_timing_preserved':True,'runtime_verified':False,'user_review_pending':True,'full_ultimate_complete':False,'standing_only_pilot_not_full_playable_conversion':True}
    if base_fix:manifest.update({'kind':'ultimate_pre_capsule_base_fix','base_frames_exact':214,'base_conversion_complete_for_pre_capsule':True,'standing_only_pilot_not_full_playable_conversion':False,'ultimate_outfit_still_standing_pilot':True,'same_bank_compaction':True})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));(out/'sector_changes.json').write_text(json.dumps(result,indent=2));print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352}));return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--base-fix',action='store_true');a=p.parse_args();build(a.candidate,a.base_fix)
