"""Recompose native title typography with the existing logo, palette and menu."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_cliche_logo import image_indices
from scripts.prepare_cliche_logo_v4 import old_records,pack_bank,grid_parts
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels,write_tile
from src.psx_static_effect import compose_static
from src.psx_korean_typography import render_mask,profile_metadata
sha=lambda b:hashlib.sha256(b).hexdigest()
NAMES={'ver_buki_riko':'텐코 시부키 · 유즈하 리코','ver_rin_nana':'하나코 나나 · 아오쿠모 린'}
TARGETS={0,17,*range(10,17)}
def decode(g,p,n):
 px,sz,bb,_=compose_static(g,local_composition(aliased_composition(p,0,n)))
 return np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]).copy(),bb
def lettering(text,profile,size,warm=False):
 mask=np.asarray(render_mask(text,profile,size,slant=.12 if warm else .18));h,w=mask.shape
 out=np.zeros((h+1,w+1),np.uint8);ink=mask>=65;out[1:,1:][ink]=1
 ramp=np.where(mask>=200,14 if warm else 8,np.where(mask>=128,13 if warm else 7,12 if warm else 6)).astype(np.uint8)
 if not warm:
  for y in range(h):
   if y>=h*.55:ramp[y,mask[y]>=200]=15 if y<h*.8 else 7
 out[:h,:w][ink]=ramp[ink]
 return out
for project,names in NAMES.items():
 d=W/project;out=d/'candidate03';assert not out.exists();out.mkdir();old=(d/'before_ST0E_U0.ARC').read_bytes();g=entry(old,0x10002);p=struct.pack('<I',4)+entry(old,0x12);frames=old_records(p,0)
 combined,bb=decode(g,p,0);assert combined.shape==(88,240)and bb==(-104,-56,136,32);master=combined[24:88].copy()
 words=struct.unpack_from('<16H',entry((d/'before_COL0E_U0.ARC').read_bytes(),5));reserved={q['page']*256+q['tile']for n in range(35)if n not in TARGETS for q in aliased_composition(p,0,n)['parts']}
 free=iter(i for i in range(len(g)//128)if i not in reserved);patterns={tile_pixels(g,t):t for t in sorted(reserved)};ng=bytearray(g)
 def allocate(px):
  if px not in patterns:
   t=next(free,None);assert t is not None,'Title atlas capacity';patterns[px]=t;write_tile(ng,t,px)
  return patterns[px]
 canvas=np.zeros((112,240),np.uint8);canvas[24:88]=master
 fan=lettering('스텔라이브 팬 모드','menu',11,True)
 left,right=[lettering(t,'title',12)for t in names.split(' · ')];h=max(left.shape[0],right.shape[0]);subtitle=np.zeros((h,left.shape[1]+right.shape[1]+12),np.uint8)
 subtitle[h-left.shape[0]:,:left.shape[1]]=left;subtitle[h-right.shape[0]:,left.shape[1]+12:]=right
 cx=left.shape[1]+6;cy=h//2;subtitle[cy,cx]=14
 for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):subtitle[cy+dy,cx+dx]=13
 assert fan.shape[0]<=15 and subtitle.shape[0]<=15
 fx=(240-fan.shape[1])//2;nx=(240-subtitle.shape[1])//2
 canvas[6:6+fan.shape[0],fx:fx+fan.shape[1]]=fan
 canvas[92:92+subtitle.shape[0],nx:nx+subtitle.shape[1]]=subtitle
 # Short silver-blue rules and restrained gold endcaps repeat the logo palette.
 fy=6+fan.shape[0]//2
 for left,right in((fx-24,fx-7),(fx+fan.shape[1]+7,fx+fan.shape[1]+24)):
  canvas[fy,left:right]=5;canvas[fy,left:left+2]=13;canvas[fy,right-2:right]=7
 frames[0]=grid_parts(canvas,(-104,-64),0,allocate);frames[17]=frames[0]
 targets={0:(canvas,(-104,-64)),17:(canvas,(-104,-64))}
 for n in range(10,17):
  a,b=decode(g,p,n);frames[n]=grid_parts(a,(b[0],b[1]-8),0,allocate);targets[n]=(a,(b[0],b[1]-8))
 bank,capacity=pack_bank(frames,len(p)-4);new=replace_entry(replace_entry(old,0x10002,bytes(ng)),0x12,bank);np_=struct.pack('<I',4)+entry(new,0x12)
 protected=[]
 for n in range(35):
  a,b=decode(entry(new,0x10002),np_,n)
  if n not in TARGETS:
   aa,bb=decode(g,p,n);assert np.array_equal(a,aa)and b==bb and frames[n]==old_records(p,0)[n];protected.append(n)
  else:
   expected,origin=targets[n];full=np.zeros_like(expected);dx,dy=b[0]-origin[0],b[1]-origin[1];assert dx>=0 and dy>=0 and dx+a.shape[1]<=full.shape[1]and dy+a.shape[0]<=full.shape[0];full[dy:dy+a.shape[0],dx:dx+a.shape[1]]=a;assert np.array_equal(full,expected)
 assert np.array_equal(canvas[24:88],master)
 image_indices(canvas,words).resize((720,336),Image.Resampling.NEAREST).save(out/'logo_3x.png')
 screen=Image.new('RGBA',(320,240),(0,0,0,255));screen.alpha_composite(image_indices(canvas,words),(40,8))
 for n,y,row in((2,128,6),(29,144,7),(30,160,7)):
  px,b=decode(g,p,n);pal=struct.unpack_from('<16H',entry((d/'before_COL0E_U0.ARC').read_bytes(),5),row*32);screen.alpha_composite(image_indices(px,pal),(160+b[0],y+b[1]))
 screen.resize((960,720),Image.Resampling.NEAREST).save(out/'layout_3x.png');(out/'ST0E_U0.ARC').write_bytes(new);np.save(out/'expected_title_indices.npy',canvas)
 report={'project':project,'parent':json.loads((d/'source.json').read_text('utf8'))['pointer'],'before_sha256':sha(old),'after_sha256':sha(new),'length':len(new),'notice':'스텔라이브 팬 모드','subtitle':names,'mode_suffix_removed':True,'title_anchor':[144,72],'title_bounds':[40,8,280,120],'main_logo_shift_y':-8,'main_logo_pixels_and_palette_preserved':True,'font_profiles':{k:profile_metadata(k)for k in('title','menu')},'notice_bounds':[40+fx,14,40+fx+fan.shape[1],14+fan.shape[0]],'subtitle_bounds':[40+nx,100,40+nx+subtitle.shape[1],100+subtitle.shape[0]],'protected_frames':protected,'changed_frames':sorted(TARGETS),'bank':capacity,'new_parts':len(frames[0]),'allowed_entries':[65538,18],'exe_changed':False,'other_resources_changed':False,'runtime_verified':False}
 (out/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({k:report[k]for k in('project','notice_bounds','subtitle_bounds','new_parts','bank')}))
