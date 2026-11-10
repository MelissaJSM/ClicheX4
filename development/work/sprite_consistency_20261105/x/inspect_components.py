import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import *
from scipy.ndimage import label,find_objects

records=[]
for character in SOURCES:
 out=OUT/character;manifest=json.loads((out/'manifest.json').read_text('utf8'))
 for r in manifest['frames']:
  if r['form'].startswith('capsule') or r['status']!='rendered':continue
  a=np.array(Image.open(ROOT/r['path']));lab,count=label(a[:,:,3]>0,np.ones((3,3)));sizes=np.bincount(lab.flat);sizes[0]=0
  tiny=[]
  for ident,sl in enumerate(find_objects(lab),1):
   if sl is None or ident==sizes.argmax() or sizes[ident]>8:continue
   yy,xx=np.nonzero(lab==ident)
   tiny.append({'size':int(sizes[ident]),'world_pixels':[[int(x)-160,int(y)-160] for y,x in zip(yy,xx)],'colors':np.unique(a[lab==ident,:3],axis=0).tolist()})
  if tiny:records.append({'character':character,'form':r['form'],'ref':r['ref'],'group':r['group'],'components':tiny})
 # Original pixels on a pale background expose isolated black dots hidden by navy.
 arc=Archive((TASK/character/'PL00_U.ARC').read_bytes());items=[]
 for n in (0,115,116,117,118,119):
  for mask in (0,4,8,12,15):
   im,_=arc.composite(n,mask,2);items.append((f'ref {n} mask{mask:X}',im))
 b=(128,125,195,185);w,h=268,240;pic=Image.new('RGB',(w*5,(h+24)*6),'#b9c6c9');dr=ImageDraw.Draw(pic)
 for i,(txt,im) in enumerate(items):
  x=i%5*w;y=i//5*(h+24);dr.text((x+3,y+2),txt,font=FONT,fill='black');im=im.crop(b).resize((w,h),Image.Resampling.NEAREST);pic.paste(im,(x,y+24),im)
 pic.save(out/'idle_component_review.png')
write(TASK/'components.json',records)
arc=Archive((TASK/'nana/PL00_U.ARC').read_bytes());partial=[]
for n in (0,115,116,117,118,119):
 im,_=arc.composite(n,8,2);a=np.asarray(im);labs,count=label(a[:,:,3]>0,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0
 for ident in range(1,count+1):
  if ident==sizes.argmax():continue
  yy,xx=np.nonzero(labs==ident);leg,meta=arc.layer(n,8)
  partial.append({'ref':n,'mask':8,'bank':8,'size':int(sizes[ident]),'world_pixels':[[int(x)-160,int(y)-160] for y,x in zip(yy,xx)],'indices':[int(leg[y,x]) for y,x in zip(yy,xx)],'stream_offset':meta['stream_offset'],'composition_parts':meta['parts']})
write(TASK/'nana_partial_idle_components.json',partial)
print(json.dumps([{k:v for k,v in r.items() if k!='composition_parts'} for r in partial],ensure_ascii=False))
