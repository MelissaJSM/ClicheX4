"""의상 변경용 전신 대신 팔 전용 원화의 의미영역을 등록한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
SRC=D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC'
def main():
 p=argparse.ArgumentParser();p.add_argument('--page',required=True,choices=['a','c','d']);p.add_argument('--version',default='v1');args=p.parse_args()
 out=D/f'firing_{args.page}_after_arm_only_{args.version}';out.mkdir(exist_ok=False);a=Archive(SRC.read_bytes())
 inputs=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'));reg=json.loads((D/f'firing_{args.page}_after_registered_v2/registration.json').read_text('utf8'));regions=json.loads((D/'firing_after_regions_v2.json').read_text('utf8'))
 Y,X=np.indices((384,384));Y-=160;X-=160;rows=[];records=[]
 for rr in reg['frames']:
  n=rr['ref'];q=next(z for z in inputs['frames']if z['ref']==n);bp=ROOT/q['sources']['after']['body_path'];sp=D/f'firing_{args.page}_after_registered_v2/after_{n:03}.png';b=np.array(Image.open(bp));s=np.array(Image.open(sp));need(digest(bp)==q['sources']['after']['body_sha256']and sha(s.tobytes())==rr['index_sha256'],'Input hashes')
  poly=regions[str(n)];poly=poly['polygon']if isinstance(poly,dict)else poly
  mi=Image.new('1',(384,384));ImageDraw.Draw(mi).polygon([(x+160,y+160)for x,y in poly],fill=1);roi=np.array(mi).astype(bool)
  ex,ey=rr['eye_world'];head=(X>=ex-9)&(Y<=ey+4);roi&=~head
  # 팔 전용 생성물의 분홍 몸통은 작업 지시대로 보존된 재킷이다. 몸통 donor로 쓰지 않는다.
  pink=np.isin(s,[5,6,7,8,9]);mask=roi&~pink
  held=np.array(Image.open(ROOT/q['held_gun_path']));mask|=(held>0)&~pink
  t=b.copy();t[mask]=s[mask]
  case=np.array(Image.open(D/f'firing_inputs_v1/after_case_{n:03}.png'));x0,y0,x1,y1=q['window_world'];window=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1);t[window]=case[window]
  need(np.array_equal(t[~(mask|window)],b[~(mask|window)]),'Outside mask');need(np.array_equal(t[window],case[window]),'Original gun');need(np.array_equal(t[mask&~window],s[mask&~window]),'Exact source')
  lab,num=label(t>0,np.ones((3,3)));sz=np.bincount(lab.ravel());small=[{'size':int(sz[k]),'coords':[[int(x-160),int(y-160)]for y,x in zip(*np.nonzero(lab==k))]}for k in range(1,num+1)if sz[k]<10]
  Image.fromarray(t).save(out/f'after_{n:03}.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/f'mask_{n:03}.png')
  records.append({'ref':n,'body_path':bp.relative_to(ROOT).as_posix(),'body_sha256':digest(bp),'source_path':sp.relative_to(ROOT).as_posix(),'source_sha256':digest(sp),'polygon':poly,'excluded_jacket_donor_cells':[[int(x-160),int(y-160)]for y,x in zip(*np.nonzero(roi&pink))],'source_texels_exact':True,'outside_mask_exact':True,'original_case_exact':True,'components':int(num),'small_components':small,'index_sha256':sha(t.tobytes())})
  rows.append((f'run firing {n}',[('accepted after body',a.rgba(b,0)),('arm-only edit donor',a.rgba(s,0)),('local bare-arm candidate',a.rgba(t,0))]))
 for i in(0,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'registration.json',{'scope':'팔 국소 생성물에서 분홍 재킷 몸통을 제외하고 원래 후폼 몸체에 등록한 후보. 색상 채움/몸체 스케일 변경 없음. 미술·공통층 미완료.','frames':records,'runtime_verified':False,'native_packed':False})
 print(json.dumps([{k:r[k]for k in('ref','components','small_components')}for r in records]))
if __name__=='__main__':main()
