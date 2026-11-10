"""Build a loader-only correction; no input, saves, or accepted release changes."""
import sys,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime import ROOT,H,entry,sha,psx_arc
from scripts.c01_audio_build import read_disc
from src.psx_disc import file_hash,write_archive_copies
from src.psx_sector import validate_checks
F=H/'fix_v3'
def load(p):return json.loads(p.read_text('utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
protection=load(H/'protection_before.json')['files'];snapshot={n:{'size':(ROOT/n).stat().st_size,'sha256':file_hash(ROOT/n)}for n in protection};save(F/'protection_before.json',{'files':snapshot})
results=[]
for mode in ['ver_rin_nana']:
 d=H/mode;ptr=load(F/'baseline'/mode/'current_build.json');assert load(ROOT/'projects'/mode/'current_build.json')==ptr
 source=(ROOT/ptr['cue']).with_suffix('.bin');assert file_hash(source)==ptr['sha256']
 prep=d/'prepared';cpu=load(prep/'cpu_verification.json');assert cpu['passed'] and cpu['native_task_tables_preserved']
 replacements={n:(prep/n).read_bytes()for n in ['ST0D_0X.ARC']}
 originals,records=read_disc(source,list(replacements)+['SLUS_005.61']);assert originals['SLUS_005.61']==(prep/'SLUS_005.61').read_bytes()
 for n,new in replacements.items():
  old=originals[n];assert old==(F/'baseline'/mode/'prepared'/n).read_bytes();assert len(old)==len(new);assert sha(new)==cpu['archive_sha256'][n]
  assert psx_arc(old)[0]['offset']==psx_arc(new)[0]['offset']
  for e in psx_arc(old):
   k=int(e['type'],16)
   if k!=13:assert entry(old,k)==entry(new,k)
  assert entry(old,13)[:96]==entry(new,13)[:96]
 stem='rin_nana'if mode=='ver_rin_nana'else'shibuki_riko';out=ROOT/'out'/mode/'hq_armor_20261109_v3';out.mkdir(exist_ok=False);target=out/(stem+'.bin')
 result=write_archive_copies(source,target,[({**records[n],'sha256':sha(originals[n])},v)for n,v in replacements.items()],ptr['sha256'])
 declared={x['lba']for x in result['changed_sectors']};actual=set()
 with source.open('rb')as f,target.open('rb')as t:
  for lba in range(result['size']//2352):
   a,b=f.read(2352),t.read(2352)
   if a!=b:assert lba in declared and a[:24]==b[:24];validate_checks(b);actual.add(lba)
 assert actual==declared and read_disc(target,list(replacements))[0]==replacements and file_hash(source)==ptr['sha256']
 (out/(stem+'.cue')).write_bytes((ROOT/ptr['cue']).read_bytes());save(out/'sector_changes.json',result)
 shutil.copytree(d/'review',out/'review');recipe=out/'review/recipe';recipe.mkdir()
 for p in H.glob('*.py'):shutil.copyfile(p,recipe/p.name)
 for p in F.glob('*.py'):shutil.copyfile(p,recipe/p.name)
 for n in ['preparation.json','cpu_verification.json','render_verification.json']:shutil.copyfile(prep/n,out/'review'/n)
 manifest={'task':'hq_force_art_review_20261109','mode':mode,'parent':ptr['cue'],'parent_sha256':ptr['sha256'],'modified_bin':{k:v for k,v in result.items()if k!='changed_sectors'},'changed_files':list(replacements),'changed_sectors':len(actual),'all_disc_sectors_compared':result['size']//2352,'EDC_ECC_checked':True,'readback_exact':True,'all_other_parent_sectors_exact':True,'archive_lengths_and_LBA_preserved':True,'only_resource13_container_changed':True,'exe_runtime_palettes_text_sounds_and_saves_unchanged':True,'art_audit':load(F/'art_audit.json'),'native_cpu':cpu,'runtime_verified':False,'user_accepted':False,'review':'review/index.html'}
 save(out/'manifest.json',manifest);r={'mode':mode,'cue':(out/(stem+'.cue')).relative_to(ROOT).as_posix(),'sha256':result['sha256'],'changed_sectors':len(actual)};results.append(r);print(json.dumps(r),flush=True)
for n,q in snapshot.items():assert file_hash(ROOT/n)==q['sha256'],n
save(F/'builds.json',results)
