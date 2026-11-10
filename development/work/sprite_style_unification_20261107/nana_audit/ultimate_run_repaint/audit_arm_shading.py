"""새 맨팔 원화의 명암 면적과 고정 셀 양자화 결과를 비교한다."""
from pathlib import Path
import json,sys,math
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,write
def main():
 out=D/'arm_shading_audit_v2';out.mkdir(exist_ok=False);a=Archive((D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC').read_bytes());pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);meta=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'));rows=[];recs=[]
 for n in range(2,33,2):
  page='abcd'[(n-2)//8];version='v1'if page=='b'else'v2';rd=D/f'firing_{page}_after_registered_{version}';reg=json.loads((rd/'registration.json').read_text('utf8'));r=next(q for q in reg['frames']if q['ref']==n);art=D/f'firing_{page}_after_{version}/generated.png';im=Image.open(art).convert('RGBA');box=r['source_crop'];crop=im.crop(box);pix=np.array(crop);rgb=pix[:,:,:3].astype(np.float32);alpha=pix[:,:,3].astype(np.float32)/255
  labels=np.empty(alpha.shape,np.uint8)
  for y in range(rgb.shape[0]):labels[y]=1+((rgb[y,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
  votes=np.stack([np.array(Image.fromarray(np.where(labels==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)]);dx,dy=r['translation'];votes=np.roll(votes,(dy,dx),(1,2));world=np.zeros((15,384,384),np.float32);world[:,112:208,112:208]=votes
  s=np.array(Image.open(rd/f'after_{n:03}.png'));f=np.array(Image.open(D/f'firing_after_cleanup_v1/after_{n:03}.png'));q=next(z for z in meta['frames']if z['ref']==n);ex,ey=r['eye_world'];wx0,wy0,wx1,wy1=q['window_world'];roi=(wx1,wy0,min(ex-3,wx1+23),wy0+13);x0,y0,x1,y1=roi;sl=np.s_[y0+160:y1+160,x0+160:x1+160];vis=f[sl]>0
  stat={str(i):{'native_source_pixels':int(((s[sl]==i)&vis).sum()),'final_registered_pixels':int(((f[sl]==i)&vis).sum()),'source_equivalent_area_pixels':round(float(world[i-1][sl][vis].sum()),3)}for i in [1,2,3,4,10,11,12,13]}
  candidates=[]
  for y,x in np.argwhere((f==12)&(world[9]>=.12)&(world[10]>=.12)):
   if x0+160<=x<x1+160 and y0+160<=y<y1+160:candidates.append({'xy':[int(x-160),int(y-160)],'native':12,'source_vote10':float(world[9,y,x]),'source_vote11':float(world[10,y,x]),'source_vote12':float(world[11,y,x])})
  sx0=(x0+48-dx)*crop.width/96;sy0=(y0+48-dy)*crop.height/96;sx1=(x1+48-dx)*crop.width/96;sy1=(y1+48-dy)*crop.height/96;sourcecrop=crop.crop((int(sx0),int(sy0),int(sx1),int(sy1)))
  sourcecrop.save(out/f'{n:03}_source_arm.png');a.rgba(s).crop((x0+160,y0+160,x1+160,y1+160)).save(out/f'{n:03}_registered_arm.png')
  recs.append({'ref':n,'source_art':art.relative_to(ROOT).as_posix(),'source_sha256':digest(art),'crop':box,'native_translation':[dx,dy],'arm_roi_world':roi,'palette_index_meaning':{'10':'dark tan','11':'midtone skin','12':'light skin','1..4':'gray outline/shadow'},'counts':stat,'minority_tan_in_light_cells':candidates,'art_changed':False})
  if n in(2,10,16,20,24,28):
   native=a.rgba(s).crop((x0+160,y0+160,x1+160,y1+160));final=a.rgba(f).crop((x0+160,y0+160,x1+160,y1+160));rows.append((n,sourcecrop,native,final))
 sh=Image.new('RGB',(1440,len(rows)*240),'#bbc5cc');dr=ImageDraw.Draw(sh)
 for i,(n,*ims)in enumerate(rows):
  for j,img in enumerate(ims):
   factor=min(440/img.width,190/img.height);pic=img.resize((int(img.width*factor),int(img.height*factor)),Image.Resampling.NEAREST);sh.paste(pic,(j*480+10,i*240+40),pic);dr.text((j*480+10,i*240+5),f'{n} '+['source RGB crop','area-vote native','registered without alpha clipping'][j],fill='black')
 sh.save(out/'source_native_comparison.png');write(out/'report.json',{'scope':'원화 RGB에서 팔 영역의 팔레트별 면적을 고정셀 native와 대조. 이 보고서는 어떤 그림도 수정하지 않는다. 소수 면적이 손실된 셀은 별도 후보로 남긴다.','frames':recs,'source_palette_sha256':digest(D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC'),'art_changed':False});print(out)
if __name__=='__main__':main()
