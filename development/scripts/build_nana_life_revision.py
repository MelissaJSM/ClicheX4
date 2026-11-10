"""나나 잔기 얼굴14타일만 적용하고 수용한 개인 효과를 보존한다."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_life_revision import ART,PARENT,PARENT_SHA,SOURCE,PROMPT,sources,head,patch,require
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def validate(art,repro):
 require(art!=repro and all(p.is_relative_to(ART)and p!=ART and p.is_dir()for p in(art,repro)),'Independent isolated directories required')
 names=sorted(p.name for p in art.iterdir());require(names==sorted(p.name for p in repro.iterdir())and all((art/n).read_bytes()==(repro/n).read_bytes()for n in names),'Independent files differ')
 m,recs,old,pal=sources();r=json.loads((art/'recipe.json').read_text('utf8'));h,norm=head(pal)
 require(r['parent_sha256']==PARENT_SHA and r['parent_manifest_sha256']==digest(PARENT/'manifest.json')and r['image_sha256']==digest(SOURCE)and r['prompt_sha256']==digest(PROMPT)and r['palette_sha256']==sha256(pal)and r['normalization']==norm,'Art binding differs')
 require(len(r['files'])==2 and {q['file']for q in r['files']}==set(old),'Resource scope differs')
 replacements=[]
 for q in r['files']:
  n=q['file'];data,v=patch(old[n],h);require(q['source']==recs[n]and data==(art/n).read_bytes()and sha256(data)==q['sha256']and v==r['checks'][n],'Candidate differs from bounded face edit');replacements.append((recs[n],data))
 return m,r,replacements,names

def build(art,repro):
 m,r,replacements,names=validate(art,repro);protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
 def protect():
  for q in protection['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed: '+q['path'])
 protect();out=ROOT/'out/ver_rin_nana'/('nana_life_face_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',replacements,PARENT_SHA);changed={q['lba']for q in result['changed_sectors']};count=0
 with(PARENT/'rin_nana.bin').open('rb')as a,(out/'rin_nana.bin').open('rb')as b:
  while True:
   x,y=a.read(2352),b.read(2352)
   if not x:require(not y,'Output grew');break
   require(len(x)==len(y)and(x!=y)==(count in changed),'Undeclared sector change')
   if count in changed:require(x[:24]==y[:24]and any(q['lba']<=count<q['lba']+(q['size']+2047)//2048 for q,_ in replacements),'Outside face resource');validate_checks(y)
   count+=1
 with(out/'rin_nana.bin').open('rb')as f:
  d=DiscReader(f,result['size'])
  for q,a in replacements:require(d.read(q['lba'],q['size'])==a,'Face readback differs')
 protect()
 for n in('rin_nana.cue','PL01_U.ARC'):shutil.copyfile(PARENT/n,out/n)
 shutil.copyfile(art/'PL00_U.ARC',out/'modified.arc');shutil.copyfile(art/'PL02_U.ARC',out/'PL02_U.ARC')
 for n in('menu_icon','inherited_small_ui','portrait','hunter','dialogue','pause','weapon_get','hud_theme','personal_effects'):shutil.copytree(PARENT/n,out/n)
 shutil.copytree(art,out/'life_face');v={**r['checks'],'all_disc_sectors_compared':count,'changed_sectors':len(changed),'edc_ecc_checked':True,'all_other_parent_sectors_exact':True,'readback_equal':True,'protected_files':len(protection['files']),'independent_files':names,'rin_exe_palettes_bubbles_death_trails_exact':True,'runtime_verified':False}
 manifest={**m,'kind':'nana_life_face_revision','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,'modified_archive_sha256':digest(out/'modified.arc'),'verification':v,'inherited_verification':m['verification'],'inherited_manifest':(PARENT/'manifest.json').relative_to(ROOT).as_posix(),'life_face_overlay':{'recipe':(out/'life_face/recipe.json').relative_to(ROOT).as_posix(),'runtime_verified':False,'user_accepted':False},'runtime_verified':False}
 for n,d in(('manifest.json',manifest),('verification.json',v),('preservation.json',protection),('reproducibility.json',{'candidate':art.relative_to(ROOT).as_posix(),'reproduced':repro.relative_to(ROOT).as_posix(),'files_identical':names})):(out/n).write_text(json.dumps(d,indent=2)+'\n','utf8')
 p=ROOT/'projects/ver_rin_nana/current_build.json';ptr=json.loads(p.read_text('utf8'));ptr.update(build=out.relative_to(ROOT).as_posix(),cue=(out/'rin_nana.cue').relative_to(ROOT).as_posix(),sha256=result['sha256'],runtime_verified=False,personal_effects_except_life_user_accepted=True,life_face_user_accepted=False,personal_effects_acceptance_quote='일단 지금 잔기이외에는 수정이 잘되었어 참고해');p.write_text(json.dumps(ptr,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed),'files':len(names)}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);a=p.parse_args();build(a.art.resolve(),a.reproduced.resolve())
