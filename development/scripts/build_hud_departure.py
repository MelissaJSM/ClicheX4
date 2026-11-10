"""Apply four same-size ARC repairs to the current hash-bound UI build."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_hud_departure import load,PARENT,PARENT_SHA,D
from scripts.project import digest,working_cue
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

EXPECTED_FILES={'PL00_U.ARC','PL02_U.ARC','ST0D_0X.ARC','ST0D_0Z.ARC'}

def build(candidate):
    candidate=candidate.resolve()
    if not candidate.is_relative_to(D):raise ValueError('Candidate outside task work directory')
    recipe=json.loads((candidate/'recipe.json').read_text('utf8'));items={i['file']:i for i in recipe['files']}
    if recipe['kind']!='hud_departure_v3' or recipe['parent_bin_sha256']!=PARENT_SHA or set(items)!=EXPECTED_FILES or len(recipe['files'])!=4:raise ValueError('Wrong candidate resource set')
    records,original,current=load();replacements=[];payloads={};arcs={}
    for name,item in items.items():
        data=(candidate/name).read_bytes();rec=records[name]
        if item['source']!=rec or item['parent_sha256']!=sha256(current[name]) or sha256(data)!=item['sha256'] or len(data)!=len(current[name]):raise ValueError('Candidate hash/record/size mismatch')
        replacements.append(({**rec,'sha256':sha256(current[name])},data));arcs[name]=data
        for i in range((len(data)+2047)//2048):payloads[rec['lba']+i]=data[i*2048:(i+1)*2048]
    out=ROOT/'out/ver_buki_riko'/('hud_departure_fix_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(exist_ok=False);parent=PARENT/'shibuki_riko.bin';target=out/'shibuki_riko.bin'
    result=write_archive_copies(parent,target,replacements,PARENT_SHA);expected={x['lba'] for x in result['changed_sectors']};actual=[]
    with parent.open('rb') as a,target.open('rb') as b:
        for lba in range(result['size']//2352):
            before,after=a.read(2352),b.read(2352)
            if before==after:continue
            if lba not in expected or before[:24]!=after[:24]:raise ValueError('Unexpected sector mutation')
            validate_checks(after);chunk=payloads[lba]
            if after[24:24+len(chunk)]!=chunk or after[24+len(chunk):2072]!=before[24+len(chunk):2072]:raise ValueError('Unexpected payload')
            actual.append(lba)
    if set(actual)!=expected:raise ValueError('Incomplete sector proof')
    with target.open('rb') as f:
        reader=DiscReader(f,target.stat().st_size)
        for rec,data in replacements:
            if reader.read(rec['lba'],rec['size'])!=data:raise ValueError('Archive readback failed')
    if digest(parent)!=PARENT_SHA or digest(ROOT/'MegaMan X4.bin')!='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b':raise ValueError('Protected game changed')
    (out/'shibuki_riko.cue').write_text(working_cue((PARENT/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),encoding='ascii')
    for name,data in arcs.items():(out/name).write_bytes(data)
    (out/'modified.arc').write_bytes(arcs['PL00_U.ARC'])
    for name in ['review.png','shibuki_departure.png','riko_departure.png']:shutil.copyfile(candidate/name,out/name)
    manifest={'project':'ver_buki_riko','task':'x_shibuki_ui','active_tasks':['x_shibuki_ui','zero_riko_ui'],'stage':'EXPANSION','kind':'hud_departure_fix','source_sha256':'3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b','parent_build':str(PARENT.relative_to(ROOT)),'parent_bin_sha256':PARENT_SHA,'modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},'modified_archive_sha256':sha256(arcs['PL00_U.ARC']),'resource_count':4,'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352,'archive_sizes_lbas_preserved':True,'exe_changed':False,'animation_timing_preserved':True,'candidate':str(candidate.relative_to(ROOT)),'runtime_verified':False,'user_review_pending':True,'active_game_restarted':False}
    for name,obj in [('recipe.json',recipe),('manifest.json',manifest),('sector_changes.json',result)]: (out/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(actual),'full_disc_verified':True}));return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();build(a.candidate)
