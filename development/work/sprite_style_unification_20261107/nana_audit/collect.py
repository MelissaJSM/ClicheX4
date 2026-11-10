"""현재 Nana 자원의 읽기 전용 미술 비교. 새 픽셀을 제작하지 않는다."""
import hashlib, importlib.util, json, sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,GROUPS,metrics,animation_map
from scripts.discover_inputs import DiscReader
OUT=Path(__file__).parent
SOURCE=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin'
EXPECTED='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720'
spec=importlib.util.spec_from_file_location('review_helpers',ROOT/'work/sprite_reaudit_20261106/nana/prepare_review.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(path):
 with path.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert digest(SOURCE)==EXPECTED
 with SOURCE.open('rb')as f:
  d=DiscReader(f,SOURCE.stat().st_size);records={r['name'].split(';')[0]:r for r in d.inspect()['files']if not r['directory']}
  assets={n:d.read(records[n]['lba'],records[n]['size'])for n in('PL00_U.ARC','PL02_U.ARC','SLUS_005.61')}
 arcs={n:Archive(assets[n])for n in('PL00_U.ARC','PL02_U.ARC')};ims={};frames=[];sheets=[];arms=[]
 animations,refs=animation_map(assets['SLUS_005.61'])
 for form,label,name,mask in helper.FORMS:
  for ref in range(237):
   effective=15 if form=='ultimate_after'and 217<=ref<=230 else mask
   try:im,_=arcs[name].composite(ref,effective,2)
   except(ValueError,IndexError):
    assert ref in(105,*range(175,183));im=Image.new('RGBA',(384,384))
   ims[form,ref]=im
   frames.append({'form':form,'ref':ref,'rgba_sha256':sha(im.tobytes()),'mask':effective,'animations':refs.get(ref,[]),**metrics(im)})
 for group,rr in GROUPS.items():
  for start in range(0,len(rr),12):
   subset=rr[start:start+12];p=OUT/'all_motion'/f'{group}_{start//12:02}.png';p.parent.mkdir(exist_ok=True)
   rows=[(label,[('idle 0',ims[form,0])]+[(str(r),ims[form,r])for r in subset])for form,label,_,_ in helper.FORMS]
   rec=helper.grid(rows,p,2);rec.update(group=group,refs=subset,sha256=digest(p));sheets.append(rec)
 groups={'run_face':[0,1,7,15,25,31], 'shoot_arm':[0,85,2,12,26,62],
         'air_dash':[0,33,41,53,69,77], 'special':[0,95,98,100,103,231],
         'ceremony':[0,133,137,141,142,156], 'ladder_vehicle':[0,144,148,150,162,184],
         'low_hover':[0,106,120,204,217,223]}
 for group,rr in groups.items():
  p=OUT/'focus'/f'{group}.png';p.parent.mkdir(exist_ok=True)
  rows=[(label,[(str(r),ims[form,r])for r in rr])for form,label,_,_ in helper.FORMS]
  rec=helper.grid(rows,p,4);rec.update(group=group,refs=rr,sha256=digest(p));sheets.append(rec)
 for ref in range(237):
  if ref in(105,*range(175,183)):continue
  for mask in range(16):
   a=arcs['PL00_U.ARC'].composite(ref,mask,1)[0];b=arcs['PL00_U.ARC'].composite(ref,mask,2)[0]
   if a.tobytes()!=b.tobytes():arms.append([ref,mask])
 partial_refs=[0,1,12,62,85,95,100,120,133,141,148,156,162,183,217,231]
 for start in range(0,len(partial_refs),4):
  rr=partial_refs[start:start+4];rows=[(f'ref {ref}',[(f'{mask:X}',arcs['PL00_U.ARC'].composite(ref,mask,2)[0])for mask in range(16)])for ref in rr]
  p=OUT/'partial'/f'masks_{start//4:02}.png';p.parent.mkdir(exist_ok=True)
  rec=helper.grid(rows,p,2);rec.update(group='partial',refs=rr,sha256=digest(p));sheets.append(rec)
 report={'source':SOURCE.relative_to(ROOT).as_posix(),'sha256':EXPECTED,'assets':{n:sha(b)for n,b in assets.items()},'frames':frames,'sheets':sheets,'arm1_vs_arm2_all_3648_equal':not arms,'arm_differences':arms,'static_only':True,'created_art':False,'game_changes':False}
 (OUT/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 assert digest(SOURCE)==EXPECTED
 print(json.dumps({'frames':len(frames),'sheets':len(sheets),'arm_differences':arms}))
if __name__=='__main__':main()
