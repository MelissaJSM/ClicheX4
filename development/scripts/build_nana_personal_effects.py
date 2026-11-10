"""나나 잔기·사망·잔상을 수용 HUD 빌드에 누적하며 디스크 전체를 대조한다."""
import argparse,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_personal_effects import ART,PARENT,PARENT_SHA,sources,head_from_accepted,player,preserve_rin_death,entry,replace_entry,trail_palette,require
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def validate(art,reproduced):
 art=art.resolve();reproduced=reproduced.resolve()
 require(art!=reproduced and all(p.is_relative_to(ART)and p!=ART and p.is_dir()for p in(art,reproduced)),'Independent isolated prepared paths required')
 names=sorted(p.name for p in art.iterdir());require(names==sorted(p.name for p in reproduced.iterdir()),'Independent file list differs')
 require(all((art/n).is_file()and (art/n).read_bytes()==(reproduced/n).read_bytes()for n in names),'Independent files differ')
 m,recs,old=sources();r=json.loads((art/'recipe.json').read_text('utf8'))
 require(r['parent_sha256']==PARENT_SHA and r['parent_manifest_sha256']==digest(PARENT/'manifest.json'),'Recipe parent differs')
 head=head_from_accepted(old['PL00_U.ARC']);pal=entry(old['PL00_U.ARC'],9)[:32];expected={};checks={}
 for n in('PL00_U.ARC','PL02_U.ARC'):expected[n],checks[n]=player(old[n],head)
 expected['PL01_U.ARC'],checks['rin_death_compensation']=preserve_rin_death(old['PL01_U.ARC'])
 exe=old['SLUS_005.61'];expected['SLUS_005.61']=exe[:0xbb67c]+bytes([0])+exe[0xbb67d:]
 for n,a in old.items():
  if n.startswith('COL'):
   p=entry(a,5);expected[n]=replace_entry(a,5,p[:352]+pal+p[384:416]+trail_palette(pal,reference_index=8)+p[512:])
 require(set(expected)=={q['file']for q in r['files']}and len(r['files'])==28,'Prepared resource scope differs')
 require(json.loads(json.dumps(checks))==r['checks'],'Static verification differs')
 replacements=[]
 for q in r['files']:
  n=q['file'];data=(art/n).read_bytes();require(q['source']==recs[n]and data==expected[n]and sha256(data)==q['sha256'],'Candidate escaped bounded change: '+n);replacements.append((recs[n],data))
 return m,r,replacements,names

def build(art,reproduced):
 m,r,replacements,names=validate(art,reproduced);protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
 def protect():
  for q in protection['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed: '+q['path'])
 protect();out=ROOT/'out/ver_rin_nana'/('nana_personal_effects_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
 result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',replacements,PARENT_SHA);changed={q['lba']for q in result['changed_sectors']};count=0
 with(PARENT/'rin_nana.bin').open('rb')as a,(out/'rin_nana.bin').open('rb')as b:
  while True:
   x,y=a.read(2352),b.read(2352)
   if not x:require(not y,'Output grew');break
   require(len(x)==len(y)and(x!=y)==(count in changed),'Undeclared disc difference')
   if count in changed:
    require(x[:24]==y[:24]and any(q['lba']<=count<q['lba']+(q['size']+2047)//2048 for q,_ in replacements),'Unexpected sector/header change');validate_checks(y)
   count+=1
 with(out/'rin_nana.bin').open('rb')as f:
  d=DiscReader(f,result['size'])
  for q,a in replacements:require(d.read(q['lba'],q['size'])==a,'Readback differs')
 protect();shutil.copyfile(PARENT/'rin_nana.cue',out/'rin_nana.cue')
 for n,dst in(('PL00_U.ARC','modified.arc'),('PL01_U.ARC','PL01_U.ARC'),('PL02_U.ARC','PL02_U.ARC')):shutil.copyfile(art/n,out/dst)
 for n in('menu_icon','inherited_small_ui','portrait','hunter','dialogue','pause','weapon_get','hud_theme'):shutil.copytree(PARENT/n,out/n)
 shutil.copytree(art,out/'personal_effects')
 v={'player':r['checks'],'all_disc_sectors_compared':count,'changed_sectors':len(changed),'edc_ecc_checked':True,'all_other_parent_sectors_exact':True,'readback_archives':len(replacements),'protected_files':len(protection['files']),'independent_files':names,'exe_change':r['exe_change'],'runtime_verified':False}
 manifest={**m,'kind':'nana_personal_effects','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,'modified_archive_sha256':digest(out/'modified.arc'),'verification':v,'inherited_verification':m['verification'],'inherited_manifest':(PARENT/'manifest.json').relative_to(ROOT).as_posix(),'personal_effects_overlay':{'recipe':(out/'personal_effects/recipe.json').relative_to(ROOT).as_posix(),'runtime_verified':False,'user_accepted':False},'runtime_verified':False}
 for n,d in(('manifest.json',manifest),('verification.json',v),('preservation.json',protection),('reproducibility.json',{'candidate':art.relative_to(ROOT).as_posix(),'reproduced':reproduced.relative_to(ROOT).as_posix(),'files_identical':names})):(out/n).write_text(json.dumps(d,indent=2)+'\n','utf8')
 p=ROOT/'projects/ver_rin_nana/current_build.json';ptr=json.loads(p.read_text('utf8'));ptr.update(build=out.relative_to(ROOT).as_posix(),cue=(out/'rin_nana.cue').relative_to(ROOT).as_posix(),sha256=result['sha256'],runtime_verified=False,personal_effects_user_accepted=False);p.write_text(json.dumps(ptr,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed),'independent_files':len(names)}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);a=p.parse_args();build(a.art.resolve(),a.reproduced.resolve())
