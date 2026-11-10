"""현PL02 이동사격16의 실제 총구/앞8열과 모든 아머마스크를 읽기 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
SRC=N/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC'
EXPECTED='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'
from src.psx_player import composition_frame
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'fire_constraints_v1';out.mkdir(exist_ok=False);Y,X=np.indices((384,384));rows=[];records=[]
 for n in range(2,33,2):
  v=a.layer(n)[0];ys,xs=np.nonzero(v);mx=int(xs.min());my=float(np.median(ys[xs==mx]));y0=int(np.floor(my))-2;y1=int(np.ceil(my))+4;mask=(X>=mx)&(X<mx+8)&(Y>=y0)&(Y<y1);gun=np.where(mask,v,0).astype(np.uint8);need(gun.max()<16,'Effect within gun');Image.fromarray(gun).save(out/f'case_{n:03}.png');checks=[]
  for armor in range(16):
   for arm in(1,2):
    im=np.array(a.composite(n,armor,arm)[0]);crop=im[y0:y1,mx:mx+8];checks.append({'mask':armor,'arm':arm,'case_rgba_sha256':sha(crop.tobytes())})
  variants=len({x['case_rgba_sha256']for x in checks})
  vis=a.composite(n,15)[0];ImageDraw.Draw(vis).rectangle((mx-1,y0-1,mx+8,y1),outline=(255,80,40,255));rows.append((f'Ultimate shot {n}',[('original shot / gun window',vis),('actual 8 columns',a.rgba(gun,16)),('paired old body',a.composite(n-1,15)[0])]))
  records.append({'ref':n,'pair':n-1,'muzzle_world':[mx-160,my-160],'window_world':[mx-160,y0-160,mx+8-160,y1-160],'case_indexed_sha256':sha(gun.tobytes()),'mask_checks':checks,'existing_color_variants':variants,'source_parts':{str(pb):len(composition_frame(a.c,pb,n)['parts'])for pb in(0,5,6,7,8)},'source_stream_offset':a.banks[0]['frames'][n]['offset'],'semantic_window_review_pending':True})
 for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',6)
 write(out/'manifest.json',{'parent_arc_sha256':EXPECTED,'frames':records,'source_mask_checks':len(records)*32,'native_packed':False,'runtime_verified':False,'scope':'현PL02 이동사격16의 앞8열을 원총구/사랑이 보호조건으로 추출. 각8열이 권총 본체인지 실제 비교판 열람 후 입력에 사용한다.'});print(json.dumps({q['ref']:q['muzzle_world']for q in records}))
if __name__=='__main__':main()
