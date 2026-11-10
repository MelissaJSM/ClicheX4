"""나나 벽 자세를 공통 배율·원작 손 접점·얼굴 높이에 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects
from scripts.normalize_nana_run import quantize
from scripts.prepare_nana_idle_shot import PILOT,INV,write
from scripts.extract_zero import save_image
from scripts.project import digest

def components(im):
 lab,_=label(np.array(im.getchannel('A'))>=192);sizes=np.bincount(lab.flat)
 objs=[(i,(s[1].start,s[0].start,s[1].stop,s[0].stop))for i,s in enumerate(find_objects(lab),1)if sizes[i]>1000]
 objs.sort(key=lambda q:(int(((q[1][1]+q[1][3])/2)*2/im.height),q[1][0]))
 if len(objs)!=8:raise ValueError(f'Expected 6 wall and 2 calibration poses, got {len(objs)}')
 return lab,objs

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();root=ROOT/'work/ver_rin_nana/nana_art/wall_v1'
 if not args.source.resolve().is_relative_to(root)or not args.output.resolve().is_relative_to(root)or args.output.exists():raise ValueError('Fresh isolated wall paths required')
 im=Image.open(args.source).convert('RGBA');lab,objs=components(im);sc=45/(objs[-1][1][3]-objs[-1][1][1]);words=struct.unpack('<16H',(PILOT/'palette.bin').read_bytes());rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31]for w in words],np.int32);inv=json.loads(INV.read_text('utf8'));out=args.output;out.mkdir(parents=True);records=[]
 def native(n):
  a=np.array(Image.open(INV.parent/f'base_{n:03d}.png'));b=inv['base_frames'][n]['bounds'];f=np.isin(a,[3,4]);ys,xs=np.nonzero(f);return a,b,float(np.median(xs)+b[0]),float(np.median(ys)+b[1]),float(np.median(ys))
 _,_,nx0,ny0,_=native(0)
 board=Image.new('RGB',(4*288,2*320),'#222630');draw=ImageDraw.Draw(board)
 for i,(n,(idx,bb))in enumerate(zip(range(55,67,2),objs)):
  crop=np.array(im.crop(bb));crop[lab[bb[1]:bb[3],bb[0]:bb[2]]!=idx,3]=0;crop=Image.fromarray(crop);size=(round(crop.width*sc*.9),round(crop.height*sc));v=quantize(crop,size,rgb);e=v==14;e[round(size[1]*.6):]=False;ey,ex=map(lambda q:int(round(np.median(q))),np.nonzero(e));a,b,nx,ny,ey_native=native(n);y=round(28+ny-ny0-ey);x=round(44+nx-nx0-ex);contact=None
  if n in (57,59):x=44-ex
  if n in (55,61,63,65):
   sy,sx=np.indices(v.shape);skin=np.isin(v,[10,11,12,13])&(sx>ex+5)&(sy<ey+10);ys,xs=np.nonzero(skin)
   if not len(xs):raise ValueError('No authored wall hand')
   ay,ax=np.indices(a.shape);native_upper=(a!=0)&(ay<ey_native+10)&(ax>nx-b[0]+3);wx=int(np.nonzero(native_upper)[1].max()+b[0]);x=48+wx-int(xs.max());contact={'world_x':wx,'art_hand_max_x':int(xs.max()),'upper_body_native_right_edge':True}
  if x<0 or y<0 or x+size[0]>96 or y+size[1]>80:raise ValueError('Clipped registration')
  canvas=np.zeros((80,96),np.uint8);canvas[y:y+size[1],x:x+size[0]]=v;save_image(canvas.tobytes(),(96,80),words,out/f'run_{n:03d}.png')
  records.append({'frame':n,'image':f'run_{n:03d}.png','source_box':list(bb),'native_size':list(size),'position':[x-48,y-40],'eye':[ex+x,ey+y],'wall_contact':contact,'opaque_pixels':int(np.count_nonzero(canvas))})
  pic=Image.open(out/f'run_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);px,py=i%4*288,i//4*320;board.paste(pic,(px,py+25),pic);draw.text((px+8,py+6),f'wall {n}',fill='white')
 for i,(name,path)in enumerate([('accepted idle',ROOT/'out/ver_rin_nana/nana_idle_shot_20261029T055257544069Z/art/frame_000.png'),('air 39 reused',ROOT/'out/ver_rin_nana/nana_air_20261029T070014731019Z/art/frame_039.png')],6):
  pic=Image.open(path).convert('RGBA').resize((288,240),Image.Resampling.NEAREST);px,py=i%4*288,320;board.paste(pic,(px,py+25),pic);draw.text((px+8,py+6),name,fill='white')
 board.save(out/'family_3x.png');write(out/'art.json',{'task':'x_nana','scope':'wall','source':args.source.as_posix(),'source_sha256':digest(args.source),'source_inventory':INV.relative_to(ROOT).as_posix(),'scale':sc,'common_width_factor':.9,'per_frame_scale':False,'frames':records,'palette_words':list(words),'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'runtime_verified':False});print(json.dumps({'output':str(out),'frames':records}))
if __name__=='__main__':main()
