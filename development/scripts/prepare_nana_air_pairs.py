"""공중 몸을 공유하고 원화의 사격 팔/권총을 원작 발사점에 등록한다."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects
from scripts.prepare_nana_idle_shot import INV,write
from scripts.normalize_nana_run import quantize
from scripts.extract_zero import save_image
from scripts.project import digest

def main():
 p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();d=args.art;out=args.output;root=ROOT/'work/ver_rin_nana/nana_art/air_v1'
 if not d.resolve().is_relative_to(root) or not out.resolve().is_relative_to(root) or out.exists():raise ValueError('Fresh isolated air pair output required')
 art=json.loads((d/'art.json').read_text('utf8'));inv=json.loads(INV.read_text('utf8'));words=art['palette_words'];colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
 source=root/'firing_generated.png';im=Image.open(source).convert('RGBA');labels,_=label(np.array(im.getchannel('A'))>=192);sizes=np.bincount(labels.flat);objects=[(idx,(s[1].start,s[0].start,s[1].stop,s[0].stop)) for idx,s in enumerate(find_objects(labels),1) if sizes[idx]>1000];objects.sort(key=lambda q:(int(((q[1][1]+q[1][3])/2)*3/im.height),q[1][0]))
 if len(objects)!=12:raise ValueError('Expected 12 shot figures')
 sc=45/(objects[-1][1][3]-objects[-1][1][1]);out.mkdir(parents=True);records=[];sheet=Image.new('RGB',(6*264,4*280),'#222630');draw=ImageDraw.Draw(sheet);yy,xx=np.indices((80,96))
 for i,r in enumerate(art['frames']):
  n=r['frame'];idx,bb=objects[i];crop=im.crop(bb);pixels=np.array(crop);pixels[labels[bb[1]:bb[3],bb[0]:bb[2]]!=idx,3]=0;crop=Image.fromarray(pixels)
  s=quantize(crop,(round(crop.width*sc*.9),round(crop.height*sc)),colors);eye=(s==14);eye[s.shape[0]//2:]=False;ey0,ex0=map(lambda x:int(round(np.median(x))),np.nonzero(eye));sy,sx=np.indices(s.shape)
  arm=np.where((sx<=ex0+2)&(sy>=ey0-3)&(sy<ey0+10),s,0).astype(np.uint8)
  # Exclude generated head pixels; retain the authored hand and sleeve below it.
  arm[(sx>=ex0-3)&(sy<ey0+4)]=0
  ys,xs=np.nonzero(arm);left,right=xs.min(),xs.max()+1
  top=int(np.nonzero(arm[:,left])[0].min());arm=arm[top:top+7,left:right]
  ax=np.indices(arm.shape)[1];arm[(ax>=8)&~np.isin(arm,[1,2,3,4])]=0
  original=np.array(Image.open(INV.parent/f'base_{n+1:03d}.png'));b=inv['base_frames'][n+1]['bounds'];m=original!=0;m[:5]=False;m[28:]=False;y0,x0=np.nonzero(m);mx=int(x0.min());my=float(np.median(np.nonzero(m[:,mx])[0]));mx,my=mx+b[0],my+b[1]
  a=np.array(Image.open(d/r['image']));ex,ey=r['eye'];gx,gy=round(mx)+48,round(my)+40-1;end=ex+4;gun=np.zeros_like(a)
  # Keep gun/hand at native pixel size. Fit only the authored dark sleeve span.
  fixed=min(8,arm.shape[1]-2);width=end-gx-fixed
  if width<1:raise ValueError('Arm registration reversed')
  sleeve=np.array(Image.fromarray(arm[:,fixed:]).resize((width,arm.shape[0]),Image.Resampling.NEAREST));reg=np.concatenate((arm[:,:fixed],sleeve),axis=1)
  for col in range(reg.shape[1]):
   # In a crouch the shoulder lowers while the native muzzle stays above it.
   # Register the authored sleeve along that diagonal instead of severing it
   # at the protected face region.
   dy=round((ey+4-gy)*max(0,col-fixed)/max(1,reg.shape[1]-fixed-1))
   gun[gy+dy:gy+dy+reg.shape[0],gx+col]=reg[:,col]
  gun[(xx>=ex-3)&(yy<ey+4)]=0
  mask=(xx<ex+1)&(yy>=np.where(xx<ex-3,ey+2,ey+5))&(yy<ey+15)
  shot=a.copy();shot[mask]=0;shot[gun!=0]=gun[gun!=0]
  if np.any(shot[yy>=ey+15]!=a[yy>=ey+15]):raise ValueError('Arm touches lower body')
  for name,v in [('run',a),('shoot',shot),('common',np.where(a==shot,a,0).astype(np.uint8)),('shoot_body',np.where(a!=shot,shot,0).astype(np.uint8)),('gun',gun)]:save_image(v.tobytes(),(96,80),words,out/f'{name}_{n:03d}.png')
  records.append({'run':n,'shoot':n+1,'common_rects':[],'run_arm_rect':[0,0],'gun_rect':[0,0],'original_muzzle':[mx,my],'registered_arm_bounds':[gx,gy,end,gy+reg.shape[0]],'body_shared_except_forward_arm':True})
  for j,name in enumerate(('run','shoot')):
   pic=Image.open(out/f'{name}_{n:03d}.png').convert('RGBA').crop((12,4,78,67)).resize((264,252),Image.Resampling.NEAREST);x,y=i%6*264,(i//6*2+j)*280;sheet.paste(pic,(x,y+24),pic);draw.text((x+5,y+4),f'{name} {n+j:03d}',fill='white')
 sheet.save(out/'paired_4x.png');write(out/'pairs.json',{'task':'x_nana','scope':'air','frames':records,'palette_words':words,'body_art':d.as_posix(),'body_manifest_sha256':digest(d/'art.json'),'arm_source':source.relative_to(ROOT).as_posix(),'arm_source_sha256':digest(source),'runtime_verified':False});print(out)
if __name__=='__main__':main()
