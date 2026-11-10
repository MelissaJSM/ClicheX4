"""Create a separate two-archive capsule correction with whole-disc verification."""
import sys,json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from src.psx_disc import file_hash,write_archive_copies
from src.psx_sector import validate_checks
def load(p):return json.loads(p.read_text('utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ptr=load(D/'before/current_build.json');assert ptr==load(ROOT/'projects/ver_buki_riko/current_build.json')
 source=(ROOT/ptr['cue']).with_suffix('.bin');assert file_hash(source)==ptr['sha256']
 protected=load(D/'protection_before.json')['files']
 for n,q in protected.items():assert file_hash(ROOT/n)==q['sha256'],n
 gpu=load(D/'native_gpu_prepared.json');timeline=load(D/'native_timeline.json');assert gpu['all_match'] and timeline['passed']
 replacements={n:(D/'prepared'/n).read_bytes()for n in ['PL00_U.ARC','PL02_U.ARC']};original,records=read_disc(source,list(replacements))
 for n,b in replacements.items():assert original[n]==(D/'before'/n).read_bytes() and gpu['archive_sha256'][n]==sha(b)
 out=ROOT/'out/ver_buki_riko/capsule_outline_20261109_v1';out.mkdir(exist_ok=False);target=out/'shibuki_riko.bin'
 result=write_archive_copies(source,target,[({**records[n],'sha256':sha(original[n])},b)for n,b in replacements.items()],ptr['sha256'])
 declared={s['lba']for s in result['changed_sectors']};actual=set()
 with source.open('rb')as f,target.open('rb')as t:
  for lba in range(result['size']//2352):
   a,b=f.read(2352),t.read(2352)
   if a!=b:assert lba in declared and a[:24]==b[:24];validate_checks(b);actual.add(lba)
 assert actual==declared and read_disc(target,list(replacements))[0]==replacements
 assert file_hash(source)==ptr['sha256'];(out/'shibuki_riko.cue').write_bytes((ROOT/ptr['cue']).read_bytes())
 save(out/'sector_changes.json',result);review=out/'review';review.mkdir();recipe=review/'recipe';recipe.mkdir()
 for p in D.glob('*.py'):shutil.copyfile(p,recipe/p.name)
 for n in ['recipe.json','force_recipe.json','comparison.png','force_comparison.png']:shutil.copyfile(D/'prepared'/n,review/n)
 for n in ['audit.json','force_combinations.json','native_timeline.json','native_gpu_prepared.json']:shutil.copyfile(D/n,review/n)
 manifest={'task':'shibuki_capsule_outline_20261109','parent':ptr['cue'],'parent_sha256':ptr['sha256'],
  'modified_bin':{k:v for k,v in result.items()if k!='changed_sectors'},'changed_files':list(replacements),'changed_sectors':len(actual),
  'all_disc_sectors_compared':result['size']//2352,'EDC_ECC_checked':True,'readback_exact':True,'all_other_sectors_exact':True,
  'only_capsule_banks_in_two_archives_changed':True,'gameplay_sprites_illustrations_EXE_palettes_timing_saves_unchanged':True,
  'ultimate':load(D/'prepared/recipe.json'),'force':load(D/'prepared/force_recipe.json'),
  'native_render_cases':len(gpu['cases']),'native_decoder_banks':gpu['native_decoder_banks_exact_and_guarded'],
  'native_acquisition_timeline_cases':len(timeline['cases']),'actual_gameplay_verified':False,'user_accepted':False}
 save(out/'manifest.json',manifest)
 for n,q in protected.items():assert file_hash(ROOT/n)==q['sha256'],n
 result={'cue':(out/'shibuki_riko.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'changed_sectors':len(actual)}
 save(D/'build.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
