"""Source-authored detail registration pilots, no generated artwork or game writes."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
from scipy.ndimage import label,distance_transform_edt
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(Path(__file__).parent.parent)]
from collect import SOURCE,EXPECTED,helper
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import DiscReader
from scripts.prepare_nana_pilot import normalize
OUT=Path(__file__).parent
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
def need(ok,msg):
 if not ok:raise ValueError(msg)
def data():
 need(digest(SOURCE)==EXPECTED,'BIN hash')
 with SOURCE.open('rb')as f:
  d=DiscReader(f,SOURCE.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files']}
  return {n:d.read(rs[n]['lba'],rs[n]['size'])for n in('PL00_U.ARC','PL02_U.ARC')},rs
def merged(a,n):
 r=a.layer(n)[0].copy()
 for pb in(8,5,7,6):
  q=a.layer(n,pb)[0];r[q>0]=q[q>0]
 return r
def rgb(a):return np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.int32)
def rows(mask):
 xs=np.flatnonzero(mask);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def largest(crop):
 a=np.array(crop);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;k=labs==sizes.argmax();a[~k,3]=0;ys,xs=np.nonzero(k);return Image.fromarray(a).crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
def fourth(a):
 src=ROOT/'work/ver_rin_nana/nana_fourth_armor/ladder_v1/generated.png';need(digest(src)=='fd94d7760e97fa596a1f75d58cf721531026800f25178dd62c35f71daf97a0f6','Source SHA')
 meta=json.loads((ROOT/'work/ver_rin_nana/nana_fourth_armor/ladder_art_v5/layers.json').read_text('utf8'));im=Image.open(src).convert('RGBA');pal=rgb(a);targets={};proof=[];sheet=[]
 for n in(144,146,149,151):
  q=next(q for q in meta['registration']if q['frame']==n);i=q['source_cell'];cell=im.crop((i%3*im.width//3,i//3*im.height//3,(i%3+1)*im.width//3,(i//3+1)*im.height//3));crop=cell.crop(q['source_box']);w,h=q['native_size'];dx,dy=q['placement'];indexed=normalize(crop,h,pal,width=w);auth=np.zeros((384,384),np.uint8);auth[dy+80:dy+h+80,dx+80:dx+w+80]=indexed
  old=a.layer(n,8)[0];full=merged(a,n);target=old.copy();changes=[];lower=q['lower_y']+80
  for y in range(lower,384):
   dst=rows(np.isin(old[y],(10,11,12,13)))
   srcrows=rows(np.isin(auth[y],(10,11,12,13)))
   if not dst or not srcrows:continue
   for dr in dst:
    sr=min(srcrows,key=lambda r:abs(float(r.mean()-dr.mean())))
    if abs(float(sr.mean()-dr.mean()))>6:continue
    for k,x in enumerate(dr):
     # Match the scanline material interior; every value comes from this
     # pose's pre-overwrite indexed source, never an invented gradient.
     sx=int(sr[round(k*(len(sr)-1)/max(1,len(dr)-1))]);v=int(auth[y,sx])
     if v==old[y,x]:continue
     target[y,x]=v;changes.append({'world':[int(x-160),int(y-160)],'before':int(old[y,x]),'after':v,'source_registered_world':[sx-160,y-160]})
  need(np.array_equal(old>0,target>0),'Skin alpha changed');targets[n]=target;proof.append({'ref':n,'source_image':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'registration':q,'changes':changes,'changed_pixels':len(changes),'source_native_sha256':sha(auth.tobytes())});Image.fromarray(auth).save(OUT/f'fourth_source_{n:03}.png');Image.fromarray(target).save(OUT/f'fourth_target_{n:03}.png')
  rendered=full.copy();changed=target!=old;rendered[changed]=target[changed]
  sheet.append((f'포스 {n}',[('idle',a.composite(0,15)[0]),('현재',a.composite(n,15)[0]),('원화 명암 등록',a.rgba(rendered,16)),('원화 축소/행덮기 전',a.rgba(auth,16))]))
 helper.grid(sheet,OUT/'fourth_ladder_preview_v1.png',5);write(OUT/'fourth_registration_v1.json',{'parent_sha256':EXPECTED,'arc_sha256':sha(a.data),'changes':proof,'new_art_generated':False})
 return targets
def labels_for(im,pal):
 arr=np.array(im);labs=np.zeros(arr.shape[:2],np.uint8)
 for y in range(len(arr)):
  diff=arr[y,:,:3].astype(np.int32)[:,None,:]-pal[None,1:,:];labs[y]=1+(diff*diff).sum(2).argmin(1)
 labs[arr[:,:,3]<192]=0;return labs
def ultimate(a):
 src=ROOT/'work/ver_rin_nana/nana_ultimate_armor/dash_hair_v1/generated.png';need(digest(src)=='7ece63bddcbc747996d281c8626f177082e3c450e664fc97a4c1499dda99dbea','Hair source SHA')
 im=Image.open(src).convert('RGBA');meta=json.loads((ROOT/'work/ver_rin_nana/nana_ultimate_armor/dash_hair_packed_v3/registration.json').read_text('utf8'));targets={};proof=[];sheet=[];pal=rgb(a)
 for n in(67,69,71,75,77,79,81,83):
  i=next(j for j,q in enumerate(meta)if q['frames'][0]==n);q=meta[i];ex,ey=q['eye'];old=merged(a,n);crop=largest(im.crop((i%4*im.width//4,i//4*im.height//2,(i%4+1)*im.width//4,(i//4+1)*im.height//2)));ca=np.array(crop).astype(np.int32);ys,xs=np.indices(ca.shape[:2]);gm=(ca[:,:,1]>ca[:,:,0]+5)&(ca[:,:,1]>ca[:,:,2]+5)&(ca[:,:,3]>=192)&(ys<crop.height*.65);gy,gx=np.nonzero(gm);cx,cy=float(np.median(gx)),float(np.median(gy));scale=16/(cy+.5)
  labs=labels_for(crop,pal);start,top,end,bottom=q['hair_edit_box'];sx0=(start-ex)/scale+cx;sy0=(top-ey)/scale+cy;sy1=(bottom-ey)/scale+cy
  candidates=(labs>=5)&(labs<=9)&(xs>=sx0)&(ys>=sy0)&(ys<sy1);need(candidates.any(),'Missing original hair');sx1=float(xs[candidates].max()+1)
  sourcebox=(sx0,sy0,sx1,sy1);size=(end-start,bottom-top);votes=[]
  for color in range(5,10):
   mask=Image.fromarray(np.where((labs==color)&candidates,255,0).astype(np.uint8));votes.append(np.array(mask.resize(size,Image.Resampling.BOX,box=sourcebox)))
  votes=np.stack(votes);direct=(5+votes.argmax(0)).astype(np.uint8);valid=votes.max(0)>=32
  authored=np.zeros((384,384),np.uint8);authored[top+80:bottom+80,start+80:end+80]=np.where(valid,direct,0)
  prior_mask=Image.open(ROOT/'work/ver_rin_nana/nana_ultimate_armor/dash_hair_packed_v3'/q['hair_mask_file']);pm=np.zeros_like(old,bool);pm[80:240,80:240]=np.array(prior_mask)>0
  # The full source head is registered once at the same eye/ear height.
  # Source RGB555 labels, existing alpha and non-hair pixels are authoritative.
  # The rear hair alone keeps its approved reach; the front uses the eye scale.
  hx0,hx1=ex-14,start;hy0,hy1=ey-17,ey+3
  full_votes=[]
  for color in range(5,10):
   mask=Image.fromarray(np.where(labs==color,255,0).astype(np.uint8));padded=Image.new('L',(mask.width+512,mask.height+512));padded.paste(mask,(256,256));full_votes.append(np.array(padded.resize((hx1-hx0,hy1-hy0),Image.Resampling.BOX,box=(256+(hx0-ex)/scale+cx,256+(hy0-ey)/scale+cy,256+(hx1-ex)/scale+cx,256+(hy1-ey)/scale+cy))))
  full_votes=np.stack(full_votes);head=(5+full_votes.argmax(0)).astype(np.uint8);head[full_votes.max(0)<32]=0
  authored[hy0+80:hy1+80,hx0+80:hx1+80]=head
  pm[hy0+80:hy1+80,hx0+80:hx1+80]=True
  permitted=pm&np.isin(old,(5,6,7,8,9))&(authored>0);new=old.copy();new[permitted]=authored[permitted];changes=[]
  for y,x in np.argwhere(new!=old):
   lx,ly=int(x-80-start),int(y-80-top);color=int(new[y,x]);ishead=x<start+80
   if ishead:
    samplex=(x-80-ex+.5)/scale+cx;sampley=(y-80-ey+.5)/scale+cy;original=np.argwhere(labs==color);coverage=int(full_votes[color-5,y-80-hy0,x-80-hx0])
   else:
    samplex=sx0+(lx+.5)*(sx1-sx0)/size[0];sampley=sy0+(ly+.5)*(sy1-sy0)/size[1];original=np.argwhere((labs==color)&candidates);coverage=int(votes[color-5,ly,lx])
   delta=((original-[sampley,samplex])**2).sum(1);oy,ox=original[delta.argmin()]
   changes.append({'world':[int(x-160),int(y-160)],'before':int(old[y,x]),'after':color,'source_crop_pixel':[int(ox),int(oy)],'source_filter_coverage':coverage,'region':'source_head'if ishead else'source_rear_hair'})
  need(np.array_equal(new>0,old>0),'Hair alpha changed');targets[n]=new;Image.fromarray(new).save(OUT/f'ultimate_target_{n:03}.png');Image.fromarray(authored).save(OUT/f'ultimate_source_{n:03}.png')
  proof.append({'ref':n,'source_image':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'source_cell':i,'source_crop_size':list(crop.size),'source_box_after_eye_scale':sourcebox,'same_eye_world':[ex-80,ey-80],'destination_world':[start-80,top-80,end-80,bottom-80],'changes':changes,'changed_pixels':len(changes),'method':'single source-area vote directly into original hair box; retain established alpha and protect all nonhair pixels','new_art_generated':False})
  sheet.append((f'재킷 {n}',[('idle',a.composite(0,15)[0]),('현재',a.composite(n,15)[0]),('원화 직접등록',a.rgba(new,16)),('등록원화만',a.rgba(authored,16))]))
 helper.grid(sheet,OUT/'ultimate_dash_preview_v1.png',5);write(OUT/'ultimate_registration_v1.json',{'parent_sha256':EXPECTED,'arc_sha256':sha(a.data),'changes':proof,'new_art_generated':False})
 return targets
def main():
 assets,_=data();f=fourth(Archive(assets['PL00_U.ARC']));u=ultimate(Archive(assets['PL02_U.ARC']));print(json.dumps({'fourth':{n:int(np.count_nonzero(v))for n,v in f.items()},'ultimate':list(u)}))
if __name__=='__main__':main()
