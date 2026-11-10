"""맨팔 원화의 갈색 명암이 분홍 머리색으로 양자화된 지점만 재등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,digest,sha,need,helper
def register_votes(crop,size,pal):
 a=np.array(crop);rgb=a[:,:,:3].astype(np.float32);alpha=a[:,:,3].astype(np.float32)/255
 labs=np.zeros(a.shape[:2],np.uint8)
 for y in range(len(a)):labs[y]=1+((rgb[y,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
 # Measured author skin-edge colors are warm brown, e.g.145/83/75.
 # Actual saturated rose hair has much less green and is excluded.
 brown=(a[:,:,3]>=128)&(rgb[:,:,0]>95)&(rgb[:,:,0]<220)&(rgb[:,:,1]>=rgb[:,:,0]*.45)&(rgb[:,:,1]<=rgb[:,:,0]*.78)&(rgb[:,:,2]<=rgb[:,:,1]*1.10)&(rgb[:,:,0]>rgb[:,:,2]+20)
 allowed=np.array([1,2,3,4,10,11,12,13]);near=allowed[((rgb[:,:,None,:]-pal[allowed][None,None,:,:])**2).sum(3).argmin(2)];labs[brown]=near[brown]
 votes=np.stack([np.array(Image.fromarray(np.where(labs==i,alpha,0).astype(np.float32),'F').resize(size,Image.Resampling.BOX))for i in range(1,16)]);coverage=np.array(Image.fromarray(alpha,'F').resize(size,Image.Resampling.BOX));out=1+votes.argmax(0).astype(np.uint8);out[coverage<.5]=0
 bcover=np.array(Image.fromarray(np.where(brown,alpha,0).astype(np.float32),'F').resize(size,Image.Resampling.BOX))
 return out,bcover,brown
def main():
 a=Archive((N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes());src=D/'firing_b_after_registered_v1';meta=json.loads((src/'registration.json').read_text('utf8'));out=D/'firing_b_after_skin_registration_v2';out.mkdir(exist_ok=False);pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);rows=[];proof=[]
 for q in meta['frames']:
  n=q['ref'];im=Image.open(src/f'source_{n:03}.png');w,h=q['native_size'];split=q['source_upper_height'];hu=q['native_upper_height'];upper,uc,um=register_votes(im.crop((0,0,im.width,split)),(w,hu),pal);lower,lc,lm=register_votes(im.crop((0,split,im.width,im.height)),(w,h-hu),pal);new=np.concatenate((upper,lower));cov=np.concatenate((uc,lc));ox,oy=q['native_position'];old=np.array(Image.open(src/f'after_{n:03}.png'));registered=np.zeros_like(old);registered[oy+160:oy+160+h,ox+160:ox+160+w]=new;coverage=np.zeros_like(old,np.float32);coverage[oy+160:oy+160+h,ox+160:ox+160+w]=cov
  mask=np.array(Image.open(D/'firing_b_after_joint_probe_v4'/f'source_arm_mask_{n:03}.png'))>0;gate=mask&np.isin(old,(5,6,7,8,9))&np.isin(registered,(1,2,3,4,10,11,12,13))&(coverage>.15);target=old.copy();target[gate]=registered[gate];need(np.array_equal(target>0,old>0),'Alpha');changes=[]
  rgba=np.array(im);brownmask=np.concatenate((um,lm))
  for y,x in np.argwhere(gate):
   lx=x-160-ox;ly=y-160-oy;sx=(lx+.5)*im.width/w-.5
   sy=(ly+.5)*split/hu-.5 if ly<hu else split+(ly-hu+.5)*(im.height-split)/(h-hu)-.5
   pts=np.argwhere(brownmask);py,px=pts[((pts-[sy,sx])**2).sum(1).argmin()];changes.append({'world':[int(x-160),int(y-160)],'before':int(old[y,x]),'after':int(target[y,x]),'brown_area_coverage':float(coverage[y,x]),'source_crop_pixel':[int(px),int(py)],'source_rgba':rgba[py,px].tolist(),'source_sampling_center':[sx,sy]})
  Image.fromarray(target).save(out/f'after_{n:03}.png');Image.fromarray(gate.astype(np.uint8)*255).save(out/f'changed_{n:03}.png');proof.append({'ref':n,'original_native_sha256':digest(src/f'after_{n:03}.png'),'source_crop_sha256':digest(src/f'source_{n:03}.png'),'changes':changes,'result_sha256':sha(target.tobytes()),'alpha_exact':True});rows.append((f'source skin quantization {n}',[('global palette',a.rgba(old)),('source brown material',a.rgba(target))]))
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'source_art_sha256':meta['source_art_sha256'],'frames':proof,'source_quantization_only':True,'new_art_generated':False,'new_palette_colors':False,'native_packed':False});print(json.dumps({q['ref']:len(q['changes'])for q in proof}))
if __name__=='__main__':main()
