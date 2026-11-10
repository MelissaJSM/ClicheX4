"""수용 나나 축척으로 피격 몸을 등록하고 원작 피격 효과 실루엣을 변환한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects
from scripts.normalize_nana_run import quantize
from scripts.prepare_nana_idle_shot import PILOT,INV,write
from scripts.project import digest
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from scripts.solve_sprite_cover import cover
PARENT=ROOT/'out/ver_rin_nana/nana_wall_20261029T224356693137Z'

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=ROOT/'work/ver_rin_nana/nana_art/hurt_v1'
 if not a.source.resolve().is_relative_to(root) or not a.output.resolve().is_relative_to(root) or a.output.exists():raise ValueError('Fresh isolated Nana hurt paths required')
 src=Image.open(a.source).convert('RGBA');lab,_=label(np.array(src.getchannel('A'))>=192);sizes=np.bincount(lab.flat);objs=[(i,(s[1].start,s[0].start,s[1].stop,s[0].stop))for i,s in enumerate(find_objects(lab),1)if sizes[i]>1000];objs.sort(key=lambda q:q[1][0])
 if len(objs)!=3:raise ValueError('Expected idle calibration and two hurt figures')
 scale=45/(objs[0][1][3]-objs[0][1][1]);pal=list(struct.unpack('<16H',(PILOT/'palette.bin').read_bytes()));rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31]for w in pal],np.int32);out=a.output;out.mkdir(parents=True);records=[]
 for n,(idx,bb) in zip((106,110),objs[1:]):
  crop=np.array(src.crop(bb));crop[lab[bb[1]:bb[3],bb[0]:bb[2]]!=idx,3]=0;crop=Image.fromarray(crop);size=(round(crop.width*scale*.9),round(crop.height*scale));v=quantize(crop,size,rgb);ys,xs=np.nonzero(v);left=round((46 if n==106 else 48)-(xs.min()+xs.max())/2);top=(63 if n==106 else 60)-int(ys.max());canvas=np.zeros((80,96),np.uint8)
  if left<0 or top<0 or left+size[0]>96 or top+size[1]>80:raise ValueError('Hurt sprite clipped')
  canvas[top:top+size[1],left:left+size[0]]=v;save_image(canvas.tobytes(),(96,80),pal,out/f'frame_{n:03d}.png');records.append({'frame':n,'image':f'frame_{n:03d}.png','source_box':list(bb),'native_size':list(size),'position':[left-48,top-40],'registration':'original recoil body center, boot bottom 63/60','opaque_pixels':int(np.count_nonzero(canvas))})
 arc=(PARENT/'modified.arc').read_bytes();e=next(e for e in psx_arc(arc)if int(e['type'],16)==9);pal2=list(struct.unpack('<16H',arc[e['offset']+64:e['offset']+96]));inv=json.loads(INV.read_text('utf8'))
 def original(n):
  v=np.array(Image.open(INV.parent/f'base_{n:03d}.png'));bb=inv['base_frames'][n]['bounds'];canvas=np.zeros((80,96),np.uint8);ys,xs=np.nonzero(v);canvas[ys+bb[1]+40,xs+bb[0]+48]=v[ys,xs]%16;return canvas
 def dilate(mask):
  pad=np.pad(mask,1);return np.logical_or.reduce([pad[dy:dy+80,dx:dx+96]for dy,dx in ((1,1),(0,1),(2,1),(1,0),(1,2))])
 normal=np.array(Image.open(out/'frame_106.png'));launch=np.array(Image.open(out/'frame_110.png'));old=original(110)!=0;new=launch!=0;flash=np.zeros_like(normal);flash[dilate(normal!=0)]=9;flash[normal!=0]=13;targets={109:flash}
 for n in (112,113,114):
  v=original(n);v[dilate(dilate(old))]=0
  if n==114:v[np.isin(v,[3,5])]=0
  if n==112:v[dilate(new)]=6;v[new]=14
  elif n==113:v[dilate(new)]=1
  else:
   v[dilate(new)]=1;v[new]=3;v[np.isin(launch,[1,2,4,8,15])]=5;v[np.isin(launch,[6,9])]=1
  labels,_=label(v!=0);sz=np.bincount(labels.ravel());v[(sz[labels]<4)&(labels!=0)]=0;targets[n]=v
 for n,v in targets.items():
  save_image(v.tobytes(),(96,80),pal if n==109 else pal2,out/f'frame_{n:03d}.png');records.append({'frame':n,'image':f'frame_{n:03d}.png','derived_from':106 if n==109 else 110,'effect_conversion':'new body silhouette; native outside flame rays and CLUT preserved'})
 records.sort(key=lambda q:q['frame']);write(out/'art.json',{'task':'x_nana','scope':'base_hurt_9','source':a.source.as_posix(),'source_sha256':digest(a.source),'source_inventory':INV.relative_to(ROOT).as_posix(),'scale':scale,'common_width_factor':.9,'per_frame_scale':False,'palette_words':pal,'effect_palette_words':pal2,'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'frames':records,'runtime_verified':False})
 plan=json.loads((root/'plan.json').read_text('utf8'));layouts=[]
 for q in plan['groups']:
  n=q['frame'];layout=cover(np.array(Image.open(out/f'frame_{n:03d}.png'))!=0,len(q['writable']),15);layout['frame']=n;layouts.append(layout);print({'frame':n,'fits':layout['fits'],'rectangles':len(layout['rects'])},flush=True)
 write(out/'layout.json',layouts)
 board=Image.new('RGB',(4*288,2*264),'#222630');draw=ImageDraw.Draw(board)
 for i,n in enumerate((0,106,110,109,112,113,114)):
  path=ROOT/'out/ver_rin_nana/nana_idle_shot_20261029T055257544069Z/art/frame_000.png' if n==0 else out/f'frame_{n:03d}.png';im=Image.open(path).convert('RGBA').resize((288,240),Image.Resampling.NEAREST);x=i%4*288;y=i//4*264;board.paste(im,(x,y+24),im);draw.text((x+8,y+5),'accepted idle' if n==0 else str(n),fill='white')
 board.save(out/'family_3x.png');print(json.dumps({'output':str(out),'scale':scale,'body':records[:3]}))
if __name__=='__main__':main()
