"""Register complete new sprites; never replace their heads with old artwork."""
from pathlib import Path
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).parent

def crop_cell(im,i):
 a=np.array(im);mask=a[:,:,3]>=128;labs,_=label(mask,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0
 objects=[]
 for k in np.flatnonzero(counts>1000):
  y,x=np.nonzero(labs==k);box=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1));objects.append((float(y.mean())>im.height/2,float(x.mean()),int(k),box))
 if len(objects)!=4:raise ValueError('Four separate source figures required')
 _,_,k,box=sorted(objects)[i];a[labs!=k,3]=0
 return Image.fromarray(a).crop(box),box

def register(crop,size,palette,method):
 a=np.array(crop);opaque=a[:,:,3]>=128;rgb=a[:,:,:3].astype(np.float32);alpha=a[:,:,3].astype(np.float32)/255;labels=np.zeros(a.shape[:2],np.uint8)
 for y in range(a.shape[0]):labels[y]=1+((rgb[y,:,None,:]-palette[None,1:,:])**2).sum(2).argmin(1)
 green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&opaque;green[crop.height//2:]=False;labels[green]=14
 votes=np.stack([np.array(Image.fromarray(np.where(labels==i,alpha,0).astype(np.float32),'F').resize(size,Image.Resampling.BOX))for i in range(1,16)]);coverage=np.array(Image.fromarray(alpha,'F').resize(size,Image.Resampling.BOX));out=1+votes.argmax(0).astype(np.uint8)
 if method=='area_rgb':
  channels=np.stack([np.array(Image.fromarray(rgb[:,:,i]*alpha,'F').resize(size,Image.Resampling.BOX))for i in range(3)],axis=2);channels/=np.maximum(coverage,.0001)[:,:,None];out=1+((channels[:,:,None,:]-palette[None,None,1:,:])**2).sum(3).argmin(2).astype(np.uint8)
 out[coverage<.5]=0
 eyes=votes[13].copy();eyes[coverage<.5]=0;eyes[size[1]//2:]=0
 if eyes.max()>.015:out[np.unravel_index(eyes.argmax(),eyes.shape)]=14
 return out

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--folder',required=True);parser.add_argument('--refs',type=int,nargs=4,required=True);args=parser.parse_args();folder=D/args.folder;im=Image.open(folder/'generated.png').convert('RGBA');a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'));need(sha(a.data)==plan['source_arc_sha256'],'Parent ARC');palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);record=[];sheets=[]
 for i,n in enumerate(args.refs):
  current=a.layer(n)[0];p=next(p for p in plan['frames']if p['ref']==n);crop,box=crop_cell(im,i);x0,y0,x1,y1=p['bbox_world'];size=(x1-x0,y1-y0);cols=[('대기',a.composite(0,0)[0]),('현재',a.composite(n,0)[0])];methods={}
  for method in('area_vote','area_rgb'):
   native=register(crop,size,palette,method);target=np.zeros((384,384),np.uint8);target[y0+160:y1+160,x0+160:x1+160]=native;Image.fromarray(target).save(folder/f'{method}_{n:03}.png');a.rgba(target).save(folder/f'{method}_{n:03}_rgba.png');cols.append((method,a.rgba(target)));y,x=np.nonzero((target==14)&(np.indices(target.shape)[0]<160));methods[method]={'indexed_sha256':sha(target.tobytes()),'eye_world':[float(np.median(x)-160),float(np.median(y)-160)]if len(x)else None,'size':size,'old_pixels_reused':0}
  record.append({'ref':n,'source_cell':i,'source_crop':box,'world_bbox':p['bbox_world'],'methods':methods});sheets.append((f'ref {n}',cols))
 helper.grid(sheets,folder/'native_comparison.png',6);write(folder/'registration.json',{'source_image_sha256':digest(folder/'generated.png'),'source_arc_sha256':sha(a.data),'source_palette_sha256':sha(a.p),'methods':'현재 전체bbox에 새 원화 전체를 단1회 등록; palette-area vote와 areaRGB 양자화를 비교. 기존머리/신체 재덮기 없음.','frames':record,'native_packed':False,'runtime_verified':False});print(json.dumps({'folder':args.folder,'refs':args.refs,'native_comparison':str(folder/'native_comparison.png')}))

if __name__=='__main__':main()
