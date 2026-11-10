"""수용 나나 선택판에 헌터베이스2자원을 누적하고 전체 디스크를 비교한다."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_hunter import PARENT,PARENT_SHA,ART,ART_SHA,PAL,sources,verify
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def validate(art,reproduced):
 if any(not q.resolve().is_relative_to(ART)for q in(art,reproduced)):raise ValueError('Unexpected HQ preparation')
 r=json.loads((art/'recipe.json').read_text('utf8'));r2=json.loads((reproduced/'recipe.json').read_text('utf8'))
 if r!=r2 or r['kind']!='nana_hunter'or r['parent_sha256']!=PARENT_SHA or r['parent_manifest_sha256']!=digest(PARENT/'manifest.json'):raise ValueError('HQ identity/parent/reproduction differs')
 if ROOT/r['generated_source']!=ART/'generated.png'or r['generated_sha256']!=ART_SHA or digest(ART/'generated.png')!=ART_SHA:raise ValueError('HQ generated art changed')
 if ROOT/r['prompt']!=ART/'prompt.txt'or digest(ART/'prompt.txt')!=r['prompt_sha256']:raise ValueError('HQ prompt changed')
 names={p.name for p in art.iterdir()if p.is_file()}
 if names!={p.name for p in reproduced.iterdir()if p.is_file()}:raise ValueError('HQ reproduction set differs')
 for n in names:
  if(art/n).read_bytes()!=(reproduced/n).read_bytes():raise ValueError('HQ reproduction differs: '+n)
 if(art/'palette.bin').read_bytes()!=PAL:raise ValueError('HQ palette changed')
 m,records,original=sources();new={};replacements=[]
 if len(r['files'])!=2:raise ValueError('HQ file scope changed')
 for rec,item in zip(records,r['files']):
  n=rec['name'].split(';')[0]
  if item['source']!=rec or item['file']!=n:raise ValueError('HQ source binding differs')
  data=(art/n).read_bytes()
  if sha256(data)!=item['sha256']or len(data)!=rec['size']:raise ValueError('HQ resource hash/length differs')
  new[n]=data;replacements.append((rec,data))
 world={n:np.array(Image.open(art/f'world_{n:02}.png'))for n in range(12)}
 if any(a.shape!=(144,256)or a.dtype!=np.uint8 or a.max()>15 for a in world.values()):raise ValueError('HQ world format differs')
 v=verify(original,new,world)
 if json.loads(json.dumps(v))!=r['verification']:raise ValueError('HQ verification claims differ')
 return m,r,replacements,v,sorted(names)

def build(art,reproduced):
 m,r,replacements,v,names=validate(art,reproduced);protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
 def protect():
  if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Parent changed')
  for q in protection['files']:
   if digest(ROOT/q['path'])!=q['expected_sha256']:raise ValueError('Protected input changed: '+q['path'])
 protect();out=ROOT/'out/ver_rin_nana'/('nana_hunter_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',replacements,PARENT_SHA);changed={q['lba']for q in result['changed_sectors']};count=0
 with(PARENT/'rin_nana.bin').open('rb')as a,(out/'rin_nana.bin').open('rb')as b:
  while True:
   x,y=a.read(2352),b.read(2352)
   if not x:
    if y:raise ValueError('Output longer')
    break
   if len(x)!=len(y)or(x!=y)!=(count in changed):raise ValueError('Undeclared disc change')
   if count in changed:
    if x[:24]!=y[:24]or not any(q['lba']<=count<q['lba']+(q['size']+2047)//2048 for q,data in replacements):raise ValueError('Change outside HQ sectors')
    validate_checks(y)
   count+=1
 with(out/'rin_nana.bin').open('rb')as f:
  d=DiscReader(f,result['size']);iso={q['path']:q for q in d.inspect()['files']}
  for q,data in replacements:
   if d.read(q['lba'],q['size'])!=data:raise ValueError('HQ readback differs')
  for n,path in(('PL00_U.ARC','modified.arc'),('PL01_U.ARC','PL01_U.ARC'),('PL02_U.ARC','PL02_U.ARC')):
   q=iso['/ARC/'+n+';1']
   if d.read(q['lba'],q['size'])!=(PARENT/path).read_bytes():raise ValueError('Gameplay ARC changed')
 protect()
 for n in('rin_nana.cue','modified.arc','PL01_U.ARC','PL02_U.ARC'):shutil.copyfile(PARENT/n,out/n)
 for n in('menu_icon','inherited_small_ui','portrait'):shutil.copytree(PARENT/n,out/n)
 shutil.copytree(art,out/'hunter');v.update(all_disc_sectors_compared=count,changed_sectors=len(changed),edc_ecc_checked=True,all_other_parent_sectors_exact=True,ui_readback_identical=True,three_gameplay_arcs_exact=True,protected_files=len(protection['files']),independent_preparation_files=names)
 manifest={**m,'kind':'nana_hunter','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,'verification':v,'inherited_verification':m['verification'],'inherited_manifest':(PARENT/'manifest.json').relative_to(ROOT).as_posix(),'hunter_overlay':{'recipe':(out/'hunter/recipe.json').relative_to(ROOT).as_posix(),'runtime_verified':False,'user_accepted':False},'runtime_verified':False}
 for n,data in(('manifest.json',manifest),('verification.json',v),('preservation.json',protection),('reproducibility.json',{'candidate':art.relative_to(ROOT).as_posix(),'reproduced':reproduced.relative_to(ROOT).as_posix(),'files_identical':names})):(out/n).write_text(json.dumps(data,indent=2)+'\n','utf8')
 pointer={'project':'ver_rin_nana','task':'x_nana','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'cumulative_base_references':220,'ui_user_accepted':True,'selection_portrait_user_accepted':True,'hunter_user_accepted':False,'runtime_verified':False,'user_vehicle_accepted':True};(ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed),'protected':len(protection['files']),'independent_files':len(names)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);a=p.parse_args();build(a.art.resolve(),a.reproduced.resolve())
