"""Build checked Ultimate overlays and bounded save-icon tiles on a preserved disc."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D,SOURCE_SHA
from scripts.project import digest,working_cue
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def main(candidate,repro):
 candidate=candidate.resolve();repro=repro.resolve()
 if any(not p.is_relative_to(D) for p in (candidate,repro)):raise ValueError('Isolated candidates required')
 recipe=json.loads((candidate/'recipe.json').read_text())
 if recipe['kind']!='ultimate_production_overlay_fix' or recipe['base_frames_exact']!=214 or recipe['overlays_exact']!=222 or recipe['checked_layers']!=1140:raise ValueError('Incomplete production validation')
 parent=ROOT/'out/ver_buki_riko/shibuki_ultimate_base_fix_20261027T105534656587Z';source=parent/'shibuki_riko.bin';parent_sha='af885c18568aceb787adb2eeb0e87c0b1722d37e89238891d6b7e7f92ba3fbe0'
 ui=D/'save_ui_fix03';uicheck=D/'save_ui_fix04_repro';um=json.loads((ui/'recipe.json').read_text())
 records=json.loads((D/'save_ui_observed01/records.json').read_text());records.update(json.loads((D/'analysis/records.json').read_text()))
 if digest(source)!=parent_sha or digest(ROOT/'MegaMan X4.bin')!=SOURCE_SHA:raise ValueError('Wrong input disc')
 files={'PL02_U.ARC':(candidate,repro,recipe['source_arc_sha256'],recipe['modified_arc_sha256'])}
 for name,v in um['files'].items():files[name]=(ui,uicheck,v['before'],v['after'])
 updates=[]
 with source.open('rb') as f:
  reader=DiscReader(f,source.stat().st_size)
  for name,(folder,repeat,before_sha,after_sha) in files.items():
   r=records[name];before=reader.read(r['lba'],r['size']);after=(folder/name).read_bytes()
   if sha256(before)!=before_sha or sha256(after)!=after_sha or after!=(repeat/name).read_bytes() or len(after)!=len(before):raise ValueError('Candidate hash, size or reproduction mismatch')
   updates.append(({**r,'sha256':before_sha},after))
 out=ROOT/'out/ver_buki_riko'/('shibuki_ultimate_production_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
 target=out/'shibuki_riko.bin';result=write_archive_copies(source,target,updates,parent_sha);changed={x['lba'] for x in result['changed_sectors']};actual=set()
 with source.open('rb') as a,target.open('rb') as b:
  for lba in range(result['size']//2352):
   old,new=a.read(2352),b.read(2352)
   if old==new:continue
   if lba not in changed or old[:24]!=new[:24]:raise ValueError('Unexpected sector change')
   hits=[(r,data) for r,data in updates if r['lba']<=lba<r['lba']+(r['size']+2047)//2048]
   if len(hits)!=1:raise ValueError('Sector outside selected resources')
   r,data=hits[0];offset=(lba-r['lba'])*2048;chunk=data[offset:offset+2048]
   if new[24:24+len(chunk)]!=chunk or new[24+len(chunk):2072]!=old[24+len(chunk):2072]:raise ValueError('Unexpected payload')
   validate_checks(new);actual.add(lba)
 if actual!=changed:raise ValueError('Incomplete sector proof')
 with target.open('rb') as f:
  reader=DiscReader(f,target.stat().st_size)
  for r,data in updates:
   if reader.read(r['lba'],r['size'])!=data:raise ValueError('Resource readback differs')
 if digest(source)!=parent_sha or digest(ROOT/'MegaMan X4.bin')!=SOURCE_SHA:raise ValueError('Protected disc modified')
 (out/'shibuki_riko.cue').write_text(working_cue((parent/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),encoding='ascii')
 for name,(folder,_,_,_) in files.items():shutil.copyfile(folder/name,out/name)
 shutil.copyfile(candidate/'recipe.json',out/'recipe.json');shutil.copyfile(ui/'recipe.json',out/'save_ui_recipe.json')
 manifest={'project':'ver_buki_riko','task':'ultimate_armor_shibuki','kind':'ultimate_overlay_production_and_save_ui_fix','source_sha256':SOURCE_SHA,'parent_build':str(parent.relative_to(ROOT)),'parent_bin_sha256':parent_sha,'modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},'modified_archive_sha256':digest(out/'PL02_U.ARC'),'changed_resources':list(files),'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352,'archive_sizes_lbas_preserved':True,'base_frames_preserved':214,'armor_overlay_frames':228,'exe_changed':False,'animation_timing_preserved':True,'runtime_verified':False,'full_ultimate_complete':False,'user_art_review_pending':True}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2));(out/'sector_changes.json').write_text(json.dumps(result,indent=2));print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(actual)}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);a=p.parse_args();main(a.candidate,a.repro)
