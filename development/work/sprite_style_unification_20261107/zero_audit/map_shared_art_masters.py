"""Inventory exact authored-shape reuse, never infer reuse from raw sharing alone."""
from pathlib import Path
from collections import defaultdict
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'shared_masters';OUT.mkdir(exist_ok=True)
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
from src.psx_player import graphics_bank
def sha(b):return hashlib.sha256(b).hexdigest()
def crop(a):
 y,x=np.nonzero(a)
 if not len(x):return None,None
 box=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)];return a[box[1]:box[3],box[0]:box[2]],box
def canonical(a):
 flipped=np.fliplr(a);ar,br=a.tobytes(),flipped.tobytes();return (a.shape,sha(min(ar,br))),br<ar
def locate(a,template,mask):
 colors,counts=np.unique(template[mask],return_counts=True);color=int(colors[np.argmin(counts)]);sy,sx=np.argwhere(mask&(template==color))[0];h,w=template.shape;out=[]
 for py,px in np.argwhere(a==color):
  x,y=int(px-sx),int(py-sy)
  if x<0 or y<0 or x+w>384 or y+h>384:continue
  win=a[y:y+h,x:x+w]
  if np.array_equal(win[mask],template[mask]):out.append({'origin_world':[x-160,y-160],'all_opaque_exact':bool(np.array_equal(win[template>0],template[template>0]))})
 return out
sources={'riko':('ver_buki_riko','shibuki_riko','21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a'),'rin':('ver_rin_nana','rin_nana','f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720')};maps=json.loads((D/'group_map.json').read_text('utf8'));result={}
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35];rear=np.array(Image.open(ROOT/'work/ver_buki_riko/art_pilot/ladder_v1/rear_head_indexed.png'))
for char,(mode,stem,digest)in sources.items():
 path=ROOT/f'out/{mode}/sprite_reaudit_20261106_v1/{stem}.bin';assert sha(path.read_bytes())==digest;arc=read_disc(path,('PL01_U.ARC',))[0]['PL01_U.ARC'];pal=struct.unpack_from('<16H',entry(arc,9));bodyrefs=set(v for r in maps[char].values()for v in r['body_or_head_refs']);bodyrefs|={'b0_147'};worlds={};groups=defaultdict(list)
 for group,r in maps[char].items():
  for key in r['body_or_head_refs']:groups[key].append(group)
 for b in (0,1):
  for f in graphics_bank(entry(arc,2),b)['frames']:
   n=f['index'];key=f'b{b}_{n:03d}'
   if b==1 and 42<=n<=49:continue
   worlds[key]=render(arc,b,b*5,n)[0]
 whole=defaultdict(list);cloth=defaultdict(list)
 for key in sorted(bodyrefs&worlds.keys()):
  a=worlds[key];small,bb=crop(a)
  if small is None:continue
  h,mir=canonical(small);whole[h].append({'id':key,'origin_world':[bb[0]-160,bb[1]-160],'mirror_to_canonical':mir,'groups':groups[key]})
  # Exact connected LIGHT CLOTH patches are candidates, not a semantic proof.
  if char=='riko':
   labels,count=ndimage.label(np.isin(a,[7,12,15]),np.ones((3,3),int))
   for i in range(1,count+1):
    m=labels==i
    if m.sum()<24:continue
    patch=np.where(m,a,0);cp,cb=crop(patch)
    if min(cp.shape)<3 or max(cp.shape)<8:continue
    ck,cm=canonical(cp);cloth[ck].append({'id':key,'bounds_world':[v-160 for v in cb],'pixels':int(m.sum()),'mirror_to_canonical':cm,'groups':groups[key]})
 exact=[{'shape':list(k[0]),'pixel_sha256':k[1],'refs':v}for k,v in whole.items()if len(v)>1];exact.sort(key=lambda q:-len(q['refs']));clothgroups=[{'shape':list(k[0]),'pixel_sha256':k[1],'instances':v}for k,v in cloth.items()if len({x['id']for x in v})>=3];clothgroups.sort(key=lambda q:(-len(q['instances']),-q['instances'][0]['pixels']))
 masters=[]
 if char=='riko':
  for name,template in [('front',front),('rear',rear)]:
   mask=np.isin(template,[4,8,14]);rows=[]
   for key,a in worlds.items():
    for label,t,m in [('same',template,mask),('mirror',np.fliplr(template),np.fliplr(mask))]:
     for match in locate(a,t,m):rows.append({'id':key,'view':label,**match,'body_classified':key in bodyrefs,'groups':groups[key]})
   masters.append({'name':name,'mask_kind':'all exact green hair pixels','mask_pixels':int(mask.sum()),'template_size':[template.shape[1],template.shape[0]],'matches':rows})
 else:
  # Four round-face keys: tight top-of-head regions stop before the cuff/torso.
  rois={8:(146,140,168,155),14:(149,139,173,154),49:(150,136,173,152),95:(151,139,174,154)}
  for ref,box in rois.items():
   template=worlds[f'b0_{ref:03d}'][box[1]:box[3],box[0]:box[2]];mask=template>0;rows=[]
   for key,a in worlds.items():
    for label,t,m in [('same',template,mask),('mirror',np.fliplr(template),np.fliplr(mask))]:
     for match in locate(a,t,m):rows.append({'id':key,'view':label,**match,'body_classified':key in bodyrefs,'groups':groups[key]})
   masters.append({'name':f'round_head_{ref}','source_box':list(box),'mask_kind':'all opaque pixels inside inspected head ROI; outside alpha is not constrained','mask_pixels':int(mask.sum()),'matches':rows})
 result[char]={'source_bin_sha256':digest,'source_arc_sha256':sha(arc),'display_count':len(worlds),'body_classified_count':len(bodyrefs&worlds.keys()),'body_pose_unique_translation_and_mirror':len(whole),'exact_body_groups':exact,'head_masters':masters,'light_cloth_patch_groups':clothgroups,'limitations':['Color-patch matches require hand/pose/outline visual review before using as a redraw master.','Mirrored equality is geometry evidence only, not permission to mix pose directions.','Partial VRAM b1_42..49 excluded.']}
 # Up to12 largest reusable pose clusters, one representative plus count.
 picks=exact[:12];board=Image.new('RGB',(1280,344*((len(picks)+3)//4)),'#64717b');draw=ImageDraw.Draw(board)
 for i,r in enumerate(picks):
  key=r['refs'][0]['id'];p=rgba(worlds[key],pal).crop((120,112,200,192)).resize((320,320),Image.Resampling.NEAREST);x=i%4*320;y=i//4*344;board.paste(p,(x,y+24),p);draw.text((x+4,y+5),key+' x'+str(len(r['refs'])),fill='white')
 board.save(OUT/f'{char}_body_groups.png')
 if char=='riko':
  picks=clothgroups[:16];board=Image.new('RGB',(1200,220*((len(picks)+3)//4)),'#64717b');draw=ImageDraw.Draw(board)
  for i,r in enumerate(picks):
   rec=r['instances'][0];a=worlds[rec['id']];box=[v+160 for v in rec['bounds_world']];p=rgba(a,pal).crop(box);p=p.resize((p.width*6,p.height*6),Image.Resampling.NEAREST);x=i%4*300;y=i//4*220;board.paste(p,(x+8,y+35),p);draw.text((x+4,y+6),f"{i} {rec['id']} {rec['pixels']}px x{len(r['instances'])}",fill='white')
  board.save(OUT/'riko_cloth_candidates.png')
(OUT/'inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({k:{'body_refs':r['body_classified_count'],'unique':r['body_pose_unique_translation_and_mirror'],'head_masters':{m['name']:len(m['matches'])for m in r['head_masters']},'cloth_groups':len(r['light_cloth_patch_groups'])}for k,r in result.items()}))
