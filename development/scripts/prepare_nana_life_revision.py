"""잔기 전용 완전한 얼굴을 생성 원화에서 변환해 기존 얼굴 타일만 수정한다."""
import argparse,json,sys,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_hud_emblems import all_compositions,composed,render_pixels,require
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from scripts.project import digest
from src.psx_ui_atlas import local_composition,tile_pixels
from src.psx_static_effect import patch_static
PARENT=ROOT/'out/ver_rin_nana/nana_personal_effects_20261030T045511203984Z'
PARENT_SHA='3222cfd27db05d2c03dbc401895993e65f7daac0b2dd0febe957be3c27ae3d00'
ART=ROOT/'work/ver_rin_nana/nana_personal_effects_v1'
SOURCE=ART/'head_generated.png';PROMPT=ART/'head_prompt_used.txt'
STATIC={1,2,3,4,*range(9,22)}
BUBBLES={464,465,466}

def sources():
 require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Personal effect parent changed')
 m=json.loads((PARENT/'manifest.json').read_text('utf8'));raw={};records={}
 with(PARENT/'rin_nana.bin').open('rb')as f:
  d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size);iso={r['path']:r for r in d.inspect()['files']}
  for n,disk in(('PL00_U.ARC','modified.arc'),('PL02_U.ARC','PL02_U.ARC')):
   r=iso['/ARC/'+n+';1'];a=d.read(r['lba'],r['size']);require(a==(PARENT/disk).read_bytes(),'Player readback differs');raw[n]=a;records[n]={**r,'sha256':sha256(a)}
  r=iso['/ARC/COL00_0X.ARC;1'];pal=entry(d.read(r['lba'],r['size']),5)[352:384]
 require(pal==entry(raw['PL00_U.ARC'],9)[:32],'Life color table differs')
 return m,records,raw,pal

def head(pal):
 im=Image.open(SOURCE).convert('RGBA');box=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox();require(box is not None,'Empty image');im=im.crop(box)
 scale=min(16/im.width,16/im.height);size=(round(im.width*scale),round(im.height*scale));a=np.array(im);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in struct.unpack('<16H',pal)],np.int32);labels=np.zeros(a.shape[:2],np.uint8)
 for y in range(len(a)):
  delta=a[y,:,:3].astype(np.int32)[:,None,:]-rgb[None,1:,:];labels[y]=1+(delta*delta).sum(2).argmin(1)
  r,g,b=a[y,:,:3].astype(np.int32).T;labels[y,(g>=60)&(g>r+20)&(g>b+20)]=14
 votes=np.stack([np.array(Image.fromarray(np.where(labels==i,a[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX))for i in range(1,16)]);alpha=np.array(im.getchannel('A').resize(size,Image.Resampling.BOX));small=(1+votes.argmax(0)).astype(np.uint8);small[alpha<128]=0
 # Retain one actual green-color vote for each eye, with no invented coordinates.
 eye=votes[13].copy();eye[alpha<128]=0;coords=[]
 for lo,hi in((0,size[0]//2),(size[0]//2,size[0])):
  e=eye[:,lo:hi];y,x=np.unravel_index(e.argmax(),e.shape);require(e[y,x]>=8,'Generated eye lacks native color coverage');small[y,x+lo]=14;coords.append([int(x+lo),int(y)])
 canvas=np.zeros((16,16),np.uint8);x=(16-size[0])//2;y=(16-size[1])//2;canvas[y:y+size[1],x:x+size[0]]=small
 return canvas,{'crop':list(box),'scaled_size':list(size),'uniform_scale':scale,'eyes':coords,'opaque_pixels':int(np.count_nonzero(canvas)),'skin_pixels':int(np.count_nonzero(np.isin(canvas,[10,11,12,13])))}

def patch(raw,h):
 require(h.shape==(16,16)and h.dtype==np.uint8 and h.max()<=15,'Invalid head indices')
 tex=entry(raw,0x10206);parts=entry(raw,3);comps=all_compositions(parts);cps={};targets={};report=[]
 for n in range(89,99):
  c=comps[3,n];ps=[p for p in c['parts']if p['page']*256+p['tile']not in BUBBLES]
  require(all(p['clut']==0 for p in c['parts']),'Unexpected pickup CLUT')
  if not ps:continue
  cp=local_composition({**c,'parts':ps});a,sz,bb,cov=composed(tex,cp);side=16 if n in (89,96,97,98)else 14 if n<=92 else 10 if n==93 else 6
  tiny=np.array(Image.fromarray(h).resize((side,side),Image.Resampling.NEAREST));cov=np.array([bool(v)for v in cov]).reshape(a.shape);candidates=[];cx=-side//2-bb[0];cy=-side//2-bb[1]
  for y in range(max(0,cy-2),min(sz[1]-side,cy+2)+1):
   for x in range(max(0,cx-2),min(sz[0]-side,cx+2)+1):
    v=np.zeros_like(a);v[y:y+side,x:x+side]=tiny
    if not np.any((v>0)&~cov):candidates.append(((x-cx)**2+(y-cy)**2,x,y,v))
  require(bool(candidates),f'Complete face does not fit frame {n}')
  _,x,y,v=min(candidates,key=lambda q:q[:3]);cps[n]=cp;targets[n]=(v.tobytes(),sz);report.append({'frame':n,'size':[side,side],'origin':[bb[0]+x,bb[1]+y],'opaque_pixels':int(np.count_nonzero(v)),'clipped_pixels':0})
 require(len(cps)==9,'Unexpected face count');nt=patch_static(tex,cps,targets);changed={t for t in range(len(tex)//128)if tile_pixels(tex,t)!=tile_pixels(nt,t)};count=0
 for k,c in comps.items():
  if k[0]==3 and k[1]in cps:
   v,sz,bb,_=composed(nt,cps[k[1]]);require((v.tobytes(),sz)==targets[k[1]],'Face roundtrip differs')
   # Verify the complete face remains visible in the final bubble composite.
   full,fs,fb,_=composed(nt,c);ys,xs=np.nonzero(v);require(np.array_equal(full[ys+bb[1]-fb[1],xs+bb[0]-fb[0]],v[ys,xs]),f'Bubble occludes new face {k[1]}')
  else:
   require(not changed&{p['page']*256+p['tile']for p in c['parts']},'Face tile aliases another frame')
   if k[0]in STATIC:
    a,sz,bb,_=composed(tex,c);b,ns,nb,_=composed(nt,c);require(sz==ns and bb==nb and np.array_equal(a,b),'Other static image changed');count+=1
 result=replace_entry(raw,0x10206,nt);e=next(e for e in psx_arc(raw)if e['type']=='0x10206');lo,hi=e['offset'],e['offset']+e['size'];require(raw[:lo]==result[:lo]and raw[hi:]==result[hi:],'Other player data changed')
 return result,{'faces':report,'changed_tiles':sorted(changed),'other_static_frames_exact':count,'all_other_compositions_exact':True,'final_face_not_occluded':True,'parts_palettes_body_menu_death_bubbles_exact':True}

def prepare(out):
 out=out.resolve();require(out.is_relative_to(ART)and out!=ART and not out.exists(),'Fresh isolated path required')
 m,recs,raw,pal=sources();h,normalization=head(pal);new={};checks={}
 for n,a in raw.items():new[n],checks[n]=patch(a,h)
 out.mkdir();Image.fromarray(h).save(out/'head_indices.png');render_pixels(h,pal).save(out/'native_head.png');render_pixels(h,pal).resize((192,192),Image.Resampling.NEAREST).save(out/'head_12x.png');board=Image.new('RGB',(600,260),'#242633');draw=ImageDraw.Draw(board)
 for n,a in new.items():(out/n).write_bytes(a)
 for i,n in enumerate(range(89,99)):
  a=new['PL00_U.ARC'];v,sz,bb,_=composed(entry(a,0x10206),all_compositions(entry(a,3))[3,n]);im=render_pixels(v,pal);im.save(out/f'pickup_{n}.png');p=im.resize((sz[0]*3,sz[1]*3),Image.Resampling.NEAREST);x,y=i%5*120,i//5*130;board.paste(p,(x,y+23),p);draw.text((x+3,y+3),str(n),fill='white')
 board.save(out/'pickups.png');r={'kind':'nana_life_face_revision','parent_sha256':PARENT_SHA,'parent_manifest_sha256':digest(PARENT/'manifest.json'),'image_sha256':digest(SOURCE),'prompt_sha256':digest(PROMPT),'palette_sha256':sha256(pal),'normalization':normalization,'checks':checks,'files':[{'file':n,'source':recs[n],'sha256':sha256(a)}for n,a in new.items()],'runtime_verified':False};(out/'recipe.json').write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'normalization':normalization,'checks':checks}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
