"""수용된 작은 UI판에 나나 큰 선택 그림2자원만 누적한다."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_selection_portrait import PARENT,PARENT_SHA,ART,GENERATED_SHA,RGB,sources,verify
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def validate(art,reproduced):
 if any(not q.resolve().is_relative_to(ART)for q in(art,reproduced)):raise ValueError('Unexpected portrait preparation')
 r=json.loads((art/'recipe.json').read_text('utf8'));r2=json.loads((reproduced/'recipe.json').read_text('utf8'))
 if r!=r2 or r['kind']!='nana_selection_portrait'or r['parent_sha256']!=PARENT_SHA or r['parent_manifest_sha256']!=digest(PARENT/'manifest.json'):raise ValueError('Portrait identity/parent/reproduction differs')
 source=(ROOT/r['generated_source']).resolve()
 if source!=ART/'generated_v2.png'or r['generated_sha256']!=GENERATED_SHA or digest(source)!=GENERATED_SHA:raise ValueError('Portrait art changed')
 for key,name in(('prompt','prompt.txt'),('correction_prompt','opacity_prompt.txt')):
  if ROOT/r[key]!=ART/name or digest(ART/name)!=r[key+'_sha256']:raise ValueError('Portrait prompt changed')
 if r['palette_rgb']!=[list(q)for q in RGB]or r['size']!=[192,160]or r['bounds']!=[-96,-80,96,80]or not r['faces_right']:raise ValueError('Portrait style/geometry changed')
 names={p.name for p in art.iterdir()if p.is_file()}
 if names!={p.name for p in reproduced.iterdir()if p.is_file()}:raise ValueError('Portrait reproduction file set differs')
 for n in names:
  if(art/n).read_bytes()!=(reproduced/n).read_bytes():raise ValueError('Portrait reproduction differs: '+n)
 m,records,original=sources();new={};replacements=[]
 if len(r['files'])!=len(records):raise ValueError('Portrait resource scope differs')
 for rec,item in zip(records,r['files']):
  name=rec['path'].split('/')[-1].split(';')[0]
  if rec!=item['source']or name!=item['file']:raise ValueError('Portrait source binding differs')
  data=(art/name).read_bytes()
  if sha256(data)!=item['sha256']or len(data)!=rec['size']:raise ValueError('Portrait resource hash/length differs')
  new[name]=data;replacements.append((rec,data))
 v=verify(original,new,(art/'indices.bin').read_bytes(),(art/'palette.bin').read_bytes())
 if v!=r['verification']:raise ValueError('Portrait verification claims differ')
 return m,r,replacements,v,sorted(names)

def build(art,reproduced):
 m,r,replacements,v,names=validate(art,reproduced);protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
 def protect():
  if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Parent changed')
  for q in protection['files']:
   if digest(ROOT/q['path'])!=q['expected_sha256']:raise ValueError('Protected file changed: '+q['path'])
 protect();out=ROOT/'out/ver_rin_nana'/('nana_select_portrait_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',replacements,PARENT_SHA);changed={q['lba']for q in result['changed_sectors']};count=0
 with(PARENT/'rin_nana.bin').open('rb')as a,(out/'rin_nana.bin').open('rb')as b:
  while True:
   x,y=a.read(2352),b.read(2352)
   if not x:
    if y:raise ValueError('Output longer')
    break
   if len(x)!=len(y)or(x!=y)!=(count in changed):raise ValueError('Undeclared sector change')
   if count in changed:
    if x[:24]!=y[:24]or not any(q['lba']<=count<q['lba']+(q['size']+2047)//2048 for q,data in replacements):raise ValueError('Change outside portrait sectors')
    validate_checks(y)
   count+=1
 with(out/'rin_nana.bin').open('rb')as f:
  d=DiscReader(f,result['size']);iso={q['path']:q for q in d.inspect()['files']}
  for q,data in replacements:
   if d.read(q['lba'],q['size'])!=data:raise ValueError('Portrait readback differs')
  for name,path in(('PL00_U.ARC','modified.arc'),('PL01_U.ARC','PL01_U.ARC'),('PL02_U.ARC','PL02_U.ARC')):
   q=iso['/ARC/'+name+';1']
   if d.read(q['lba'],q['size'])!=(PARENT/path).read_bytes():raise ValueError('Gameplay ARC changed')
 protect()
 for name in('rin_nana.cue','modified.arc','PL01_U.ARC','PL02_U.ARC'):shutil.copyfile(PARENT/name,out/name)
 shutil.copytree(PARENT/'menu_icon',out/'menu_icon');shutil.copytree(PARENT/'ui',out/'inherited_small_ui');shutil.copytree(art,out/'portrait')
 v.update(all_disc_sectors_compared=count,changed_sectors=len(changed),edc_ecc_checked=True,all_other_parent_sectors_exact=True,ui_readback_identical=True,three_gameplay_arcs_exact=True,protected_files=len(protection['files']),independent_preparation_files=names)
 manifest={**m,'kind':'nana_selection_portrait','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,'verification':v,'inherited_verification':m['verification'],'inherited_manifest':(PARENT/'manifest.json').relative_to(ROOT).as_posix(),'portrait_overlay':{'recipe':(out/'portrait/recipe.json').relative_to(ROOT).as_posix(),'runtime_verified':False,'user_accepted':False},'runtime_verified':False}
 for name,data in(('manifest.json',manifest),('verification.json',v),('preservation.json',protection),('reproducibility.json',{'candidate':art.relative_to(ROOT).as_posix(),'reproduced':reproduced.relative_to(ROOT).as_posix(),'files_identical':names})):(out/name).write_text(json.dumps(data,indent=2)+'\n','utf8')
 pointer={'project':'ver_rin_nana','task':'x_nana','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'cumulative_base_references':220,'ui_user_accepted':True,'selection_portrait_user_accepted':False,'runtime_verified':False,'user_vehicle_accepted':True}
 (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed),'protected':len(protection['files']),'independent_files':len(names)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);a=p.parse_args();build(a.art.resolve(),a.reproduced.resolve())
