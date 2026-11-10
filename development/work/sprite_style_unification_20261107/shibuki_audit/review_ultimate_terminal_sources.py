"""다음 Ultimate 승리/귀환의 실제 부모와 수용 기본형을 읽기 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from src.psx_player import composition_frame
from scripts.prepare_shibuki_ultimate_production import records
from pack_shibuki_hurt import raw

def main():
 d=H/'ultimate_terminal_sources01';need(not d.exists(),'Fresh source review');d.mkdir()
 p=H/'prepared_ultimate_arrival_partial01/PL02_U.ARC';b=H/'prepared_hurt_base01/PL00_U.ARC';need(sha(p.read_bytes())=='3e55b972c007731a8446c8478336c6def303e0dc5ed4ab5d6a52856471327138','Current candidate changed');need(sha(b.read_bytes())=='87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b','Base source changed');a=Archive(p.read_bytes());base=Archive(b.read_bytes());refs=(156,157,158,204,205,206,207);rows=[]
 for n in refs:
  f=a.banks[0]['frames'][n];ls={};forms={}
  for bank in(0,5,6,7,8):
   arr=a.layer(n,bank)[0];ps=composition_frame(a.c,bank,n)['parts'];ls[str(bank)]={'opaque':int(np.count_nonzero(arr)),'sha256':sha(arr.tobytes()),'record_sha256':sha(records(a.c,bank,n)),'parts':ps}
  for form,mask in(('before',15),('after',0)):
   im=a.composite(n,mask)[0];im.save(d/f'{form}_{n:03}.png');forms[form]=metrics(im)
  rows.append({'ref':n,'raw_sha256':sha(raw(a,0,n)),'tile_count':f['tile_count'],'shared_raw_refs':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],'layers':ls,'forms':forms})
 for form,mask in(('before',15),('after',0)):
  for group,ns in(('victory',(204,205,206,207)),('return',(156,157,158))):
   pics=[]
   for n in ns:pics.extend([(f'{n} accepted base',base.composite(n,0)[0]),(f'{n} old ultimate {form}',a.composite(n,mask)[0])])
   page(pics,a.composite(0,mask)[0],d/f'{form}_{group}_comparison.png',cols=2,scale=4)
 md=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json').read_text('utf8'));seq=[s for s in md['animations']if any(q['frame']in refs for q in s['steps'])]
 write(d/'report.json',{'source':str(p.relative_to(ROOT)),'source_sha256':sha(p.read_bytes()),'base_pose_source':str(b.relative_to(ROOT)),'base_pose_sha256':sha(b.read_bytes()),'refs':rows,'using_animation_metadata':seq,'actual_exe_step_reverification_pending':True,'new_art_generated':False,'arc_written':False,'shared_current_body_is_original_US_relation':False,'notes':['수용 기본형의 새자세는 다음 의상 제작의 좌표 참고다. 실제 원US Ultimate와 동일한 원시/조립 관계라고 가정하지 않는다.','새 등장8 후보가 아직 최종 동결되지 않았으므로 다음 제작 부모는 동결 후 다시 고정한다.']})
 print(json.dumps({'refs':list(refs),'animations':[s['id']for s in seq],'report':sha((d/'report.json').read_bytes())}))
if __name__=='__main__':main()
