"""Authenticated HQ-only disc write, complete sector comparison and readback."""
import json,shutil,struct
from runtime import ROOT,H,entry,sha,off,HOOK,hook,psx_arc
from scripts.c01_audio_build import read_disc
from src.psx_disc import file_hash,write_archive_copies
from src.psx_sector import validate_checks

def load(p):return json.loads(p.read_text('utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
protected=load(ROOT/'work/pause_variants_20261109/protection_before.json')['files']
snapshot={n:{'size':(ROOT/n).stat().st_size,'sha256':file_hash(ROOT/n)}for n in protected};save(H/'protection_before.json',{'files':snapshot})
results=[]
for mode in ['ver_rin_nana','ver_buki_riko']:
 d=H/mode;ptr=load(d/'pointer.json');assert load(ROOT/'projects'/mode/'current_build.json')==ptr
 source=(ROOT/ptr['cue']).with_suffix('.bin');assert file_hash(source)==ptr['sha256']
 prep=d/'prepared';cpu=load(prep/'cpu_verification.json');render=load(prep/'render_verification.json');art=load(d/'compiled/report.json')
 assert cpu['passed'] and render['passed'] and art['all_216_frames_exact']
 replacements={n:(prep/n).read_bytes()for n in ['ST0D_0X.ARC','ST0D_0Z.ARC','SLUS_005.61']}
 assert sha(replacements['SLUS_005.61'])==cpu['exe_sha256']
 for n in ['ST0D_0X.ARC','ST0D_0Z.ARC']:assert sha(replacements[n])==cpu['archive_sha256'][n]
 originals,records=read_disc(source,list(replacements))
 for n in replacements:assert originals[n]==(d/'originals'/n).read_bytes()
 oe=originals['SLUS_005.61'];ne=replacements['SLUS_005.61'];assert ne[:off(HOOK)]==oe[:off(HOOK)] and ne[off(HOOK)+28:]==oe[off(HOOK)+28:] and ne[off(HOOK):off(HOOK)+28]==hook()
 for char in 'XZ':
  old=originals[f'ST0D_0{char}.ARC'];new=replacements[f'ST0D_0{char}.ARC'];allowed={12}if char=='Z'else{12,13,10,0x10102}
  for e in psx_arc(old):
   k=int(e['type'],16)
   if k not in allowed:assert entry(old,k)==entry(new,k)
  if char=='X':assert entry(old,13)==entry(new,13)[:96]
  assert len(old)==len(new)
 stem='rin_nana'if mode=='ver_rin_nana'else'shibuki_riko';out=ROOT/'out'/mode/'hq_armor_20261109_v1';out.mkdir(exist_ok=False);target=out/(stem+'.bin')
 result=write_archive_copies(source,target,[({**records[n],'sha256':sha(originals[n])},b)for n,b in replacements.items()],ptr['sha256'])
 declared={q['lba']for q in result['changed_sectors']};actual=set();permitted={lba for n in replacements for lba in range(records[n]['lba'],records[n]['lba']+(records[n]['size']+2047)//2048)}
 with source.open('rb')as f,target.open('rb')as t:
  for lba in range(result['size']//2352):
   a,b=f.read(2352),t.read(2352)
   if a!=b:assert lba in declared and lba in permitted and a[:24]==b[:24];validate_checks(b);actual.add(lba)
 assert actual==declared and read_disc(target,list(replacements))[0]==replacements and file_hash(source)==ptr['sha256']
 (out/(stem+'.cue')).write_bytes((ROOT/ptr['cue']).read_bytes());save(out/'sector_changes.json',result)
 shutil.copytree(d/'review',out/'review');recipe=out/'review/recipe';recipe.mkdir()
 for p in H.glob('*.py'):shutil.copyfile(p,recipe/p.name)
 for n in ['preparation.json','cpu_verification.json','render_verification.json']:shutil.copyfile(prep/n,out/'review'/n)
 manifest={'task':'hq_armor_20261109','mode':mode,'parent':ptr['cue'],'parent_sha256':ptr['sha256'],'modified_bin':{k:v for k,v in result.items()if k!='changed_sectors'},'changed_files':list(replacements),'changed_sectors':len(actual),'all_disc_sectors_compared':result['size']//2352,'EDC_ECC_checked':True,'readback_exact':True,'all_other_parent_sectors_exact':True,'archive_lengths_and_LBA_preserved':True,'x_states':18,'frames_per_state':12,'non_X_composed_frames_preserved':52,'original_x12_pixels_exact':True,'original_Zero_graphics_exact':True,'palette_background_audio_animation_text_pause_dialogue_resources_exact':True,'native_cpu':cpu,'native_renderer':render,'art':art,'container':load(d/'compiled/container.json'),'review':'review/index.html','runtime_verified':False,'user_accepted':False}
 save(out/'manifest.json',manifest);r={'mode':mode,'cue':(out/(stem+'.cue')).relative_to(ROOT).as_posix(),'sha256':result['sha256'],'changed_sectors':len(actual)};results.append(r);print(json.dumps(r),flush=True)
for n,q in snapshot.items():assert file_hash(ROOT/n)==q['sha256'],n
save(H/'builds.json',results)
