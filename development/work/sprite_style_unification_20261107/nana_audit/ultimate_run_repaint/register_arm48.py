"""새4/8 팔 원화의 음영·굵기를 고정 셀에서 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
from register_page import register
def main():
 out=D/'arm48_registered_v1';out.mkdir(exist_ok=False);src=D/'arm48_v1/generated.png';gen=json.loads((src.parent/'generation.json').read_text('utf8'));need(digest(src)==gen['generated_sha256'],'Source hash');a=Archive((D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC').read_bytes());pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
 im=Image.open(src).convert('RGBA');meta=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'));regs=json.loads((D/'firing_a_before_registered_v1/registration.json').read_text('utf8'));polys=json.loads((D/'firing_after_regions_v2.json').read_text('utf8'));Y,X=np.indices((384,384));X-=160;Y-=160;rows=[];records=[]
 for i,n in enumerate((4,8)):
  box=(i*im.width//2,0,(i+1)*im.width//2,im.height//2);s=np.zeros((384,384),np.uint8);s[112:208,112:208]=register(im.crop(box),(96,96),pal,'area_vote');r=next(q for q in regs['frames']if q['ref']==n);ex,ey=r['eye_world'];yy,xx=np.nonzero((s==14)&(abs(Y-ey)<4)&(abs(X-ex)<6));need(len(yy)>0,'Eye');sy=int(yy.min()-160);sx=int(np.median(xx[yy==yy.min()])-160);dx,dy=ex-sx,ey-sy;need(abs(dx)<=3 and abs(dy)<=3,'Unexpected drift');s=np.roll(s,(dy,dx),(0,1));q=next(z for z in meta['frames']if z['ref']==n);bp=D/f'firing_after_cleanup_v1/after_{n:03}.png';b=np.array(Image.open(bp));before=np.array(Image.open(D/f'firing_pair_diagnostic_v1/before_{n:03}.png'))
  p=polys[str(n)];poly=p['polygon']if isinstance(p,dict)else p;mi=Image.new('1',(384,384));ImageDraw.Draw(mi).polygon([(x+160,y+160)for x,y in poly],fill=1);roi=np.array(mi).astype(bool)
  body=np.array(Image.open(ROOT/q['sources']['after']['body_path']));head=((X>=ex-12)&(Y<=ey+4)&(body>0))|((X>=ex-10)&(Y<=ey+1));roi&=~head;mask=roi&~np.isin(s,[5,6,7,8,9]);t=b.copy();t[mask]=s[mask]
  x0,y0,x1,y1=q['window_world'];window=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1);case=np.array(Image.open(D/f'firing_inputs_v1/after_case_{n:03}.png'));t[window]=case[window];need(np.array_equal(t[~(mask|window)],b[~(mask|window)]),'Outside arm');need(np.array_equal(t[window],case[window]),'Gun window')
  outside=(t>0)&(before==0);points=[{'xy':[int(x-160),int(y-160)],'index':int(t[y,x])}for y,x in np.argwhere(outside)];num=label(t>0,np.ones((3,3)))[1]
  for name,v in(('after',t),('donor',s),('mask',mask.astype(np.uint8)*255)):Image.fromarray(v).save(out/f'{name}_{n:03}.png')
  records.append({'ref':n,'source_sha256':digest(src),'crop':box,'native_cell':[96,96],'translation':[dx,dy],'base_sha256':digest(bp),'polygon':poly,'source_indices_sha256':sha(s.tobytes()),'target_indices_sha256':sha(t.tobytes()),'outside_common_boundary':points,'connected_components':int(num),'boundary_clipped':False,'outside_arm_exact':True,'original_case_exact':True})
  rows.append((f'new bare-arm local {n}',[('jacket target',a.rgba(before,16)),('previous bare source',a.rgba(b,0)),('new donor',a.rgba(s,0)),('new arm without clipping',a.rgba(t,0))]))
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'scope':'4/8 국소 재작화 고정96셀·동일원점 등록. 외곽 클립은 하지 않았으며 몸체/머리/다리는 이전 새 원화 보존.','frames':records,'native_packed':False,'runtime_verified':False});print(json.dumps(records))
if __name__=='__main__':main()
