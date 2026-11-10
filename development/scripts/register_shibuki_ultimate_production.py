"""Register generated jacket materials on accepted native Shibuki poses."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation,binary_closing
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D
from scripts.prepare_riko_ui import entry
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition

def bbox(mask):
 y,x=np.nonzero(mask)
 return (int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)) if len(x) else None

def component(mask):
 labs,num=label(mask,np.ones((3,3)))
 if not num:return mask
 counts=np.bincount(labs.ravel());counts[0]=0;return labs==counts.argmax()

def quantize(im,size,colors):
 a=np.array(im);labels=np.zeros(a.shape[:2],np.uint8)
 for y in range(im.height):
  diff=a[y,:,:3].astype(np.int32)[:,None,:]-colors[1:][None,:,:]
  labels[y]=(diff*diff).sum(2).argmin(1)+1
 votes=[np.array(Image.fromarray(np.where(labels==k,a[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX)) for k in range(1,16)]
 v=(np.argmax(np.stack(votes),axis=0)+1).astype(np.uint8)
 v[np.array(im.getchannel('A').resize(size,Image.Resampling.BOX))<128]=0
 return v

def main(out):
 out=out.resolve()
 if not out.is_relative_to(D) or out.exists():raise ValueError('Fresh task output required')
 out.mkdir();art=D/'production_art';groups=json.loads((art/'master_groups.json').read_text())
 arc=(D/'base_fix02/PL02_U.ARC').read_bytes();g,c,pal=[entry(arc,k) for k in (2,3,9)]
 if sha256(arc)!='2ea5ed73ec35549f571591008748c45dc31598d02128089a966073a5ff8650ef':raise ValueError('Wrong source')
 bank=graphics_bank(g,0,allow_bank_aliases=True);words=list(struct.unpack_from('<16H',pal,32));bw=list(struct.unpack_from('<16H',pal));rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in words],np.int32)
 bases={n:np.array(Image.open(art/f'base_{n:03}.png')) for n in range(237) if n not in {105,*range(175,183)}}
 # Hover's accepted feet were moved to the leg layer. Recover that geometry.
 parc=(D/'analysis/parent_PL00_U.ARC').read_bytes();pg,pc,pp=[entry(parc,k) for k in (2,3,9)];pb=graphics_bank(pg,0,allow_bank_aliases=True)
 for n in range(221,231):
  f=pb['frames'][n];raw=decode_stream(pg,f['offset'],f['limit'],f['tile_count']*128).data
  legs=canvas_from_parts(raw,f['tile_count'],local_composition(composition_frame(pc,8,n)))
  # Native geometry only; the new garment samples below replace all leg material.
  bases[n]=np.where(legs,legs,bases[n]).astype(np.uint8)
 sources={};provenance=[]
 for name,frames in groups.items():
  path=art/f'{name}_generated.png';sheet=Image.open(path).convert('RGBA');provenance.append({'file':str(path.relative_to(ROOT)),'sha256':sha256(path.read_bytes())})
  for i,n in enumerate(frames):
   im=sheet.crop((round(i%4*sheet.width/4),round(i//4*sheet.height/4),round((i%4+1)*sheet.width/4),round((i//4+1)*sheet.height/4)))
   a=np.array(im);mask=component(a[:,:,3]>=200);a[:,:,3]=np.where(mask,a[:,:,3],0);im=Image.fromarray(a).crop(bbox(mask));bb=bbox(bases[n]>0)
   v=np.zeros((160,160),np.uint8);v[bb[1]:bb[3],bb[0]:bb[2]]=quantize(im,(bb[2]-bb[0],bb[3]-bb[1]),rgb);sources[n]=v
   save_image(v.tobytes(),(160,160),words,out/f'master_{n:03}.png')
 yy,xx=np.indices((160,160));targets={};report=[]
 def choose(n):
  if n in sources:return n
  if 1<=n<=32:return n-1 if n%2==0 else n
  if 33<=n<=84:pool=groups['air_dash']
  elif 144<=n<=153:pool=[144,145,146,148,151,152,153]
  elif 217<=n<=220:return 217
  elif 221<=n<=230:return 221 if n<225 else 39
  elif 120<=n<=125:return 120
  elif 162<=n<=174 or n>=233:pool=[100,143,154,162,174]
  else:pool=[*groups['action'],*groups['back_other'][:-2]]
  b=bases[n]
  return min(pool,key=lambda k:int(np.count_nonzero((b>0)!=(bases[k]>0))*2+np.count_nonzero((b>0)&(bases[k]>0)&(b!=bases[k]))))
 for n,b in bases.items():
  if n in (0,115,116,117,118,119):continue
  f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
  cp=local_composition(composition_frame(c,5,n))
  try:old=canvas_from_parts(raw,f['tile_count'],cp)
  except ValueError:
   if n!=220:raise
   old=np.ones_like(b) # The full aura extends beyond the 160px preview canvas.
  if not np.any(old):
   targets[n]=np.zeros_like(b);report.append({'frame':n,'mode':'original_transparent_armor'});continue
  if 184<=n<=203:
   target=np.where(np.isin(b,[4,10,11]),4,0).astype(np.uint8);targets[n]=target;report.append({'frame':n,'mode':'small_ride_head'});continue
  master=choose(n);sb=bases[master];gen=sources[master];box=bbox(b>0);sbox=bbox(sb>0)
  reg=np.zeros_like(b);reg[box[1]:box[3],box[0]:box[2]]=np.array(Image.fromarray(gen).crop(sbox).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.NEAREST))
  haircore=component(binary_closing(np.isin(b,[5,8,14]),structure=np.ones((2,2))))
  hy,hx=np.nonzero(haircore);ht=int(hy.min()) if len(hy) else box[1];cx=int(np.median(hx)) if len(hx) else (box[0]+box[2])//2
  neck=ht+20;face=component(np.isin(b,[12,13])&(yy<ht+25)&(yy>ht+7))
  fy,fx=np.nonzero(face)
  back=n in (144,145,146,147,151,152,153,183)
  if len(fx)>7 and not back:neck=max(ht+16,min(ht+22,int(fy.max())+1));cx=int(np.median(fx))+3
  hip=neck+12
  hair=haircore&np.isin(b,[5,8,14]);hair|=binary_dilation(haircore)&np.isin(b,[2,15])
  hair|=np.isin(b,[5,8,14])&((yy<neck)|((xx>cx+6)&(yy<hip+4)))
  head=(xx>=cx-12)&(xx<=cx+11)&(yy<neck)
  skin=np.isin(b,[12,13])&((yy<neck+5)|((xx<cx-7)|(xx>cx+9)))
  garment=(b>0)&~hair&~head&~skin
  if n in (217,218,219,220):garment=(b>0)&~hair&~head&~skin
  # Keep isolated effects from the accepted base outside its body silhouette.
  if n in (88,107,108,111,136,141,142,157,235,236):garment&=binary_dilation(sb>0,iterations=2)
  coords=np.argwhere((reg>0)&~np.isin(reg,[5,8,14]));mapped=np.zeros_like(b)
  for y,x in np.argwhere(garment):
   cost=(coords[:,0]-y)**2*3+(coords[:,1]-x)**2;sy,sx=coords[cost.argmin()];mapped[y,x]=reg[sy,sx]
  # Preserve the one-pixel accepted outer contour, with the pilot's navy ink.
  edge=(b>0)&~(np.roll(b>0,1,0)&np.roll(b>0,-1,0)&np.roll(b>0,1,1)&np.roll(b>0,-1,1))
  mapped[garment&edge&np.isin(b,[1,2,15])]=2
  ornament=np.isin(b,[4,10,11])&(yy<neck-2)&(yy>=ht+4)&(xx>cx+3)
  mapped[ornament]=4
  if n in range(217,231):
   # Armor-only states never use an unarmored body. Entire target is Shibuki.
   mapped=np.where(mapped,mapped,b).astype(np.uint8)
  targets[n]=mapped;report.append({'frame':n,'master':master,'neck':neck,'hip':hip,'cx':cx,'mode':'generated_material_on_accepted_geometry','pixels':int(np.count_nonzero(mapped))})
 # Shared game poses retain exactly the same registered clothing, including
 # mirrored ladder steps and frames that differ only by sparks or blink pixels.
 for dst,src in ((73,71),(74,72),(88,89),(107,106),(108,106),(111,110),(145,144),(147,146),(149,148),(152,151),(163,162),(164,162),(165,162),(167,166),(168,166),(169,166),(171,170),(172,170),(173,170),(157,156)):
  best=None
  for flip in (False,True) if dst in (145,147,152) else (False,):
   source=bases[src][:,::-1] if flip else bases[src]
   for dy in range(-5,6):
    for dx in range(-8,9):
     shifted=np.roll(np.roll(source,dy,0),dx,1);same=(shifted>0)&(bases[dst]>0)
     score=int(np.count_nonzero(same&(shifted==bases[dst]))*3-np.count_nonzero((shifted>0)!=(bases[dst]>0)))
     candidate=(score,-abs(dx)-abs(dy),not flip,dx,dy,flip)
     if best is None or candidate>best:best=candidate
  _,_,_,dx,dy,flip=best;v=targets[src][:,::-1] if flip else targets[src]
  targets[dst]=np.roll(np.roll(v,dy,0),dx,1)
 # Paired shots use identical clothing on unchanged pixels, preventing jitter.
 for n in sorted(targets):
  if (2<=n<=84 and n%2==0) or (222<=n<=230 and n%2==0):
   if n-1 in targets:
    same=(bases[n]==bases[n-1])&(bases[n]>0);targets[n][same]=targets[n-1][same]
 # Nova Strike stores the old armored body together with its expanding aura.
 # Identify that body from the body-only phase 217 and retain only effect pixels
 # outside its registered silhouette in the subsequent phases.
 oldnova={}
 for n in (217,218,219,220):
  f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
  oldnova[n]=canvas_from_parts(raw,f['tile_count'],local_composition(composition_frame(c,5,n)),size=(256,160))
 body=np.zeros((160,256),np.uint8);body[:,:160]=targets[217]
 for n in (217,218,219,220):
  if n==217:result=body.copy();dx=dy=0
  elif n==219:
   silhouette=binary_dilation(body>0,iterations=2);result=np.where(silhouette,7,0).astype(np.uint8);result[body>0]=6;dx=dy=0
  else:
   best=None
   for dy in range(-4,5):
    for dx in range(-12,13):
     source=np.roll(np.roll(oldnova[217],dy,0),dx,1);score=int(np.count_nonzero((source>0)&(source==oldnova[n])))
     q=(score,-abs(dx)-abs(dy),dx,dy)
     if best is None or q>best:best=q
   _,_,dx,dy=best;mask=np.roll(np.roll(oldnova[217]>0,dy,0),dx,1)
   result=oldnova[n].copy();result[binary_dilation(mask,iterations=1)]=0
   newbody=np.roll(np.roll(body,dy,0),dx,1);result[newbody>0]=newbody[newbody>0]
  targets[n]=result
  report.append({'frame':n,'mode':'nova_body_replace_and_preserved_outer_aura','body_source':217,'offset':[dx,dy]})
 for n,v in targets.items():
  save_image(v.tobytes(),(v.shape[1],v.shape[0]),words,out/f'overlay_{n:03}.png')
  full=save_image(bases[n].tobytes(),(160,160),bw,out/f'base_{n:03}.png').convert('RGBA')
  if n in (217,218,219,220):full=Image.new('RGBA',(256,160))
  full.alpha_composite(Image.open(out/f'overlay_{n:03}.png').convert('RGBA'));full.save(out/f'full_{n:03}.png')
 frames=sorted(targets)
 for start in range(0,len(frames),48):
  sheet=Image.new('RGB',(1440,1104),'#253546');draw=ImageDraw.Draw(sheet)
  for i,n in enumerate(frames[start:start+48]):
   im=Image.open(out/f'full_{n:03}.png').crop((30,30,130,122)).resize((180,166),Image.Resampling.NEAREST);x=i%8*180;y=i//8*184;sheet.paste(im,(x,y+18),im);draw.text((x+8,y+2),str(n),fill='white')
  sheet.save(out/f'review_{start//48}.png')
 (out/'art.json').write_text(json.dumps({'frames':frames,'palette_words':words,'source_arc_sha256':sha256(arc),'generated_sources':provenance,'registration':report,'runtime_verified':False},indent=2))
 print(json.dumps({'output':str(out),'frames':len(frames)}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
