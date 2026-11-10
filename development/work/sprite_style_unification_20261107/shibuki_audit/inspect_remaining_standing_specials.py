"""최신 동결 몸체의85..92/95..97 실제그림·별칭 읽기. 아트/자원 변경 없음."""
from pathlib import Path
import sys,json
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from scripts.prepare_shibuki_ultimate_production import records
from pack_shibuki_hurt import raw
def main():
 o=H/'standing_special_sources02';need(not o.exists(),'Fresh source review');o.mkdir();paths={'PL00_U.ARC':H/'prepared_hurt_base01/PL00_U.ARC','PL02_U.ARC':H/'prepared_ultimate_victory01/PL02_U.ARC'};arcs={k:Archive(p.read_bytes())for k,p in paths.items()};rows=[];plates=[]
 for form,name,mask in [('base','PL00_U.ARC',0),('fourth','PL00_U.ARC',15),('ultimate_before','PL02_U.ARC',15),('ultimate_after','PL02_U.ARC',0)]:
  a=arcs[name]
  for pi,ns in enumerate(((85,86,87,88),(89,90,91,92),(95,96,97))):
   p=o/f'{form}_{pi:02}.png';page([(f'{form} {n}',a.composite(n,mask)[0])for n in ns],a.composite(0,mask)[0],p,cols=2,scale=5);plates.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'form':form,'refs':list(ns),'actually_viewed':False})
   for n in ns:
    pix=a.composite(n,mask)[0];pix.save(o/f'{form}_{n:03}.png');f=a.banks[0]['frames'][n];rows.append({'form':form,'ref':n,'metrics':metrics(pix),'rgba_sha256':sha(pix.tobytes()),'raw_sha256':sha(raw(a,0,n)),'tile_count':f['tile_count'],'raw_aliases':[z['index']for z in a.banks[0]['frames']if z['offset']==f['offset']],'records':{str(b):records(a.c,b,n).hex()for b in (0,5,6,7,8)},'original_motion_role_verified_here':False})
 write(o/'report.json',{'sources':{n:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for n,p in paths.items()},'rows':rows,'plates':plates,'source_scope':'현재동결PL0087e7/PL02ec7a의 기본/포스/Ultimate 전후44표시.93/94는 새공중/대시이므로이번잔여목록에서제외.','art_changed':False,'arc_written':False,'native_or_gameplay_executed':False,'visual_review_pending':True});print(json.dumps({'rows':len(rows),'plates':len(plates),'report_sha256':sha((o/'report.json').read_bytes())}))
if __name__=='__main__':main()
