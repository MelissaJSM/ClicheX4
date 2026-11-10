"""선택/저장 도트4자원만 누적하고 전체 디스크·게임 플레이 자원을 검사한다."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_ui_small import PARENT,PARENT_SHA,ARC_SHA,CONFIG,MAPPING,SHIFT_Y,read_sources,verify
from scripts.prepare_nana_idle_shot import PILOT,write
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks
def validate(art,reproduced):
 for p in(art,reproduced):
  if not p.resolve().is_relative_to(ROOT/'work/ver_rin_nana/nana_ui_small'):raise ValueError('Unexpected Nana UI preparation')
 m,arc,records,originals=read_sources();r=json.loads((art/'recipe.json').read_text('utf8'));r2=json.loads((reproduced/'recipe.json').read_text('utf8'))
 if r!=r2 or r['kind']!='nana_selection_save_small'or r['parent_sha256']!=PARENT_SHA or r['parent_arc_sha256']!=ARC_SHA or Path(r['parent'])!=PARENT.relative_to(ROOT):raise ValueError('UI identity, parent or reproduction differs')
 if r['parent_manifest_sha256']!=digest(PARENT/'manifest.json')or r['config_sha256']!=digest(CONFIG):raise ValueError('UI source metadata changed')
 if r['master_sha256']!=digest(PILOT/'nana_000_indexed.png')or r['palette_sha256']!=digest(PILOT/'palette.bin'):raise ValueError('Nana style changed')
 if r['mapping']!={str(k):v for k,v in MAPPING.items()}or r['selection_shift_y']!={str(k):v for k,v in SHIFT_Y.items()}or r['selection_mirrored']!=[19,20]:raise ValueError('UI mapping changed')
 if len(r['files'])!=4:raise ValueError('UI file scope changed')
 names={p.name for p in art.iterdir()if p.is_file()};other={p.name for p in reproduced.iterdir()if p.is_file()}
 if names!=other:raise ValueError('Reproduced file set differs')
 for name in names:
  if(art/name).read_bytes()!=(reproduced/name).read_bytes():raise ValueError('Prepared file reproduction differs: '+name)
 edited={};replacements=[]
 for rec,item in zip(records,r['files']):
  name=rec['path'].split('/')[-1].split(';')[0]
  if item['source']!=rec or item['file']!=name:raise ValueError('UI source binding changed')
  data=(art/name).read_bytes()
  if sha256(data)!=item['sha256']:raise ValueError('Prepared UI hash changed')
  edited[name]=data;replacements.append((rec,data))
 v=verify(originals,edited,arc)
 if r['verification']!=v:raise ValueError('Verification claims differ')
 return m,arc,r,replacements,v,sorted(names)
def build(art,reproduced):
 m,arc,r,replacements,v,names=validate(art,reproduced);protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
 def protect():
  if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Parent changed')
  for q in protection['files']:
   if digest(ROOT/q['path'])!=q['expected_sha256']:raise ValueError('Protected input changed: '+q['path'])
 protect();out=ROOT/'out/ver_rin_nana'/('nana_ui_small_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',replacements,PARENT_SHA);changed={q['lba']for q in result['changed_sectors']};count=0
 with(PARENT/'rin_nana.bin').open('rb')as a,(out/'rin_nana.bin').open('rb')as b:
  while True:
   x,y=a.read(2352),b.read(2352)
   if not x:
    if y:raise ValueError('Output longer')
    break
   if len(x)!=len(y)or(x!=y)!=(count in changed):raise ValueError('Undeclared sector change')
   if count in changed:
    if x[:24]!=y[:24]or not any(rec['lba']<=count<rec['lba']+(rec['size']+2047)//2048 for rec,data in replacements):raise ValueError('Change outside UI sectors')
    validate_checks(y)
   count+=1
 with(out/'rin_nana.bin').open('rb')as f:
  disc=DiscReader(f,result['size']);iso={q['path']:q for q in disc.inspect()['files']}
  for rec,data in replacements:
   if disc.read(rec['lba'],rec['size'])!=data:raise ValueError('UI readback differs')
  for name,path in(('PL00_U.ARC','modified.arc'),('PL01_U.ARC','PL01_U.ARC'),('PL02_U.ARC','PL02_U.ARC')):
   q=iso['/ARC/'+name+';1']
   if disc.read(q['lba'],q['size'])!=(PARENT/path).read_bytes():raise ValueError('Gameplay ARC changed')
 protect()
 for name in('rin_nana.cue','modified.arc','PL01_U.ARC','PL02_U.ARC'):shutil.copyfile(PARENT/name,out/name)
 shutil.copytree(PARENT/'menu_icon',out/'menu_icon');shutil.copytree(art,out/'ui')
 v.update(all_disc_sectors_compared=count,changed_sectors=len(changed),edc_ecc_checked=True,all_other_parent_sectors_exact=True,ui_readback_identical=True,three_gameplay_arcs_exact=True,protected_files=len(protection['files']),independent_preparation_files=names)
 manifest={**m,'kind':'nana_selection_save_small','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,'verification':v,'inherited_verification':m['verification'],'inherited_manifest':(PARENT/'manifest.json').relative_to(ROOT).as_posix(),'ui_overlay':{'recipe':(out/'ui/recipe.json').relative_to(ROOT).as_posix(),'selection_frames':sorted(MAPPING),'save_frame':44,'user_accepted':False,'runtime_verified':False},'runtime_verified':False}
 for name,data in(('manifest.json',manifest),('verification.json',v),('preservation.json',protection)):write(out/name,data)
 write(out/'reproducibility.json',{'candidate':art.relative_to(ROOT).as_posix(),'reproduced':reproduced.relative_to(ROOT).as_posix(),'files_identical':names})
 write(ROOT/'projects/ver_rin_nana/current_build.json',{'project':'ver_rin_nana','task':'x_nana','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'cumulative_base_references':220,'ui_selection_frames':sorted(MAPPING),'ui_save_frames':[44],'runtime_verified':False,'ui_user_accepted':False,'user_vehicle_accepted':True})
 print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed),'protected':len(protection['files']),'independent_files':len(names)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);a=p.parse_args();build(a.art.resolve(),a.reproduced.resolve())
