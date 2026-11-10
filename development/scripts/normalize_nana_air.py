"""공중 원화를 수용 팔레트·같은 배율·대기 눈 기준에 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label,find_objects
from scripts.normalize_nana_run import quantize
from scripts.prepare_nana_idle_shot import PILOT,INV,write
from scripts.extract_zero import save_image
from scripts.project import digest

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 root=ROOT/'work/ver_rin_nana/nana_art/air_v1'
 if not args.source.resolve().is_relative_to(root) or not args.output.resolve().is_relative_to(root) or args.output.exists():raise ValueError('Fresh isolated Nana air paths required')
 im=Image.open(args.source).convert('RGBA');lab,_=label(np.array(im.getchannel('A'))>=192);sizes=np.bincount(lab.flat)
 objs=[(idx,(s[1].start,s[0].start,s[1].stop,s[0].stop)) for idx,s in enumerate(find_objects(lab),1) if sizes[idx]>1000];objs.sort(key=lambda q:(int(((q[1][1]+q[1][3])/2)*3/im.height),q[1][0]))
 if len(objs)!=12:raise ValueError(f'Expected 11 air and 1 calibration pose, got {len(objs)}')
 scale=45/(objs[-1][1][3]-objs[-1][1][1]);words=struct.unpack('<16H',(PILOT/'palette.bin').read_bytes());rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
 inv=json.loads(INV.read_text('utf8'));out=args.output;out.mkdir(parents=True);records=[];board=Image.new('RGB',(6*264,2*280),'#222630');draw=ImageDraw.Draw(board)
 native0=np.array(Image.open(INV.parent/'base_000.png'));f0=np.isin(native0,[3,4]);f0[25:]=False;native_eye0=float(np.median(np.nonzero(f0)[0])+inv['base_frames'][0]['bounds'][1])
 for i,(n,(idx,bb)) in enumerate(zip(range(33,55,2),objs)):
  crop=im.crop(bb);a=np.array(crop);a[lab[bb[1]:bb[3],bb[0]:bb[2]]!=idx,3]=0;crop=Image.fromarray(a)
  size=(round(crop.width*scale*.9),round(crop.height*scale));v=quantize(crop,size,rgb);eyes=v==14;eyes[size[1]//2:]=False;ey,ex=np.nonzero(eyes)
  if not len(ex):raise ValueError(f'Green eye absent: {n}')
  ex,ey=float(np.median(ex)),float(np.median(ey));x=round(44-ex)
  native=np.array(Image.open(INV.parent/f'base_{n:03d}.png'));f=np.isin(native,[3,4]);f[25:]=False;native_eye=float(np.median(np.nonzero(f)[0])+inv['base_frames'][n]['bounds'][1])
  y=round(28+native_eye-native_eye0-ey) if n<49 else 63-size[1]
  canvas=np.zeros((80,96),np.uint8);canvas[y:y+size[1],x:x+size[0]]=v
  save_image(canvas.tobytes(),(96,80),words,out/f'run_{n:03d}.png')
  pic=Image.open(out/f'run_{n:03d}.png').convert('RGBA').crop((12,4,78,67)).resize((264,252),Image.Resampling.NEAREST);px,py=i%6*264,i//6*280;board.paste(pic,(px,py+24),pic);draw.text((px+8,py+5),f'air {n:03d}',fill='white')
  records.append({'frame':n,'image':f'run_{n:03d}.png','source_box':list(bb),'native_size':list(size),'position':[x-48,y-40],'eye':[round(ex+x),round(ey+y)],'opaque_pixels':int(np.count_nonzero(canvas)),'registration':'fixed idle eye X; native relative face Y; landing soles Y22'})
 idle=ROOT/'out/ver_rin_nana/nana_idle_shot_20261029T055257544069Z/art/frame_000.png';pic=Image.open(idle).convert('RGBA').crop((12,4,78,67)).resize((264,252),Image.Resampling.NEAREST);board.paste(pic,(1320,304),pic);draw.text((1328,285),'accepted idle 000',fill='white');board.save(out/'family_4x.png')
 write(out/'art.json',{'task':'x_nana','scope':'air','source':args.source.as_posix(),'source_sha256':digest(args.source),'source_inventory':INV.relative_to(ROOT).as_posix(),'scale':scale,'common_width_factor':.9,'per_frame_scale':False,'frames':records,'palette_words':list(words),'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'runtime_verified':False});print(json.dumps({'output':str(out),'scale':scale,'frames':[(r['frame'],r['native_size'],r['eye']) for r in records]}))
if __name__=='__main__':main()
