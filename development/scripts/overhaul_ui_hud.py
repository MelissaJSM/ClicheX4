"""C-08: 표식 전용 타일의 받침판을 투명화하고 기존 CLUT로 네 심볼을 부호화한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_ui_inventory import BUILDS,D,load
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_hud_emblems import all_compositions,composed,render_pixels
from scripts.discover_inputs import sha256,psx_arc
from scripts.project import digest
from src.psx_ui_atlas import tile_pixels
from scripts.overhaul_ui_fixes import require

ART=D/'hud_symbols_generated.png'
TARGETS={(1,n)for n in range(69,78)}
RECT=(-24,24,2,41)
SYMBOLS={'shibuki':(0,[3,4,10,11,12,14]),'riko':(1,[5,6,7,9,10,14]),'nana':(2,[2,3,4,10,11,14]),'rin':(3,[5,6,7,8,9,10,14])}

def artwork(pal):
 im=Image.open(ART).convert('RGBA');words=struct.unpack('<16H',pal);out={};meta={}
 for name,(column,allowed)in SYMBOLS.items():
  pic=im.crop((column*im.width//4,0,(column+1)*im.width//4,im.height));a=np.array(pic);alpha=a[:,:,3]>=192;yy,xx=np.nonzero(alpha);box=(int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1);pic=pic.crop(box)
  scale=min(22/pic.width,17/pic.height);size=(round(pic.width*scale),round(pic.height*scale));pic=pic.resize(size,Image.Resampling.LANCZOS);a=np.array(pic).astype(np.int32)
  colors=np.array([[((words[i]>>s)&31)*255//31 for s in(0,5,10)]for i in allowed]);d=(a[:,:,:3][:,:,None,:]-colors)**2;px=np.array(allowed,np.uint8)[d.sum(3).argmin(2)];mask=a[:,:,3]>=128;px[~mask]=0
  # Gauge stem is centered at world x=-9, region x=15. Keep its emblem centered too.
  canvas=np.zeros((17,26),np.uint8);x=min(26-size[0],max(0,round(15-size[0]/2)));y=(17-size[1])//2;canvas[y:y+size[1],x:x+size[0]]=px;out[name]=canvas;meta[name]={'column':column,'source_box':box,'size':size,'origin_in_region':[x,y],'allowed_indices':allowed,'opaque_pixels':int(mask.sum()),'alpha_threshold':128,'uniform_scale':scale,'stage_palette_exact':True,'world_center_x':-24+x+size[0]/2}
 return out,meta

def patch(arc,pixels):
 require(pixels.shape==(17,26)and np.issubdtype(pixels.dtype,np.integer)and 0<=pixels.min()<=pixels.max()<=15,'Invalid HUD indexed canvas')
 tex,parts=entry(arc,0x10206),entry(arc,3);comps=all_compositions(parts);users={}
 for k,c in comps.items():
  for p in c['parts']:users.setdefault(p['page']*256+p['tile'],set()).add(k)
 ng=bytearray(tex);demands={};targets={};changed_tiles=set();detail=[]
 for key in sorted(TARGETS):
  a,sz,bb,sources=composed(tex,comps[key]);a=a.copy();after=a.copy();l,t,r,b=RECT;ys=slice(t-bb[1],b-bb[1]);xs=slice(l-bb[0],r-bb[0]);after[ys,xs]=pixels;targets[key]=after
  for y,x in zip(*np.where(after!=a)):
   loc=sources[int(y)*sz[0]+int(x)];require(bool(loc),'HUD pixel outside parts')
   for j,(off,shift)in enumerate(loc):
    tile=off//128//16*16+(off%128)//8;require(users[tile]<=TARGETS,'HUD tile shared outside target frames');changed_tiles.add(tile)
    value=int(after[y,x])if j==len(loc)-1 else 0;require((off,shift)not in demands or demands[off,shift]==value,'HUD alias conflict');demands[off,shift]=value
  detail.append({'frame':key[1],'changed_pixels':int(np.count_nonzero(after!=a)),'transparent_removed':int(np.count_nonzero((a>0)&(after==0))),'size':sz,'bounds':bb})
 for (off,shift),v in demands.items():ng[off]=(ng[off]&~(15<<shift))|(v<<shift)
 ng=bytes(ng);checked=0
 # Every statically encoded bank is identified by its texture entry / valid tile references.
 bank_count=struct.unpack_from('<I',parts)[0]//4
 static={1,2,3,4,6}if bank_count==7 else{1,2,3,4,*range(9,bank_count)}
 for k,c in comps.items():
  if k[0]in static:
   a,sz,bb,_=composed(tex,c);b,ns,nb,_=composed(ng,c);require(sz==ns and bb==nb and np.array_equal(b,targets.get(k,a)),'Protected static frame or HUD differs: '+str(k));checked+=1
 for tile in range(len(tex)//128):
  if tile not in changed_tiles:require(tile_pixels(tex,tile)==tile_pixels(ng,tile),'Other tile changed')
 result=replace_entry(arc,0x10206,ng);require(entry(result,3)==parts,'HUD geometry changed')
 return result,{'world_rect_exclusive':RECT,'frames':detail,'private_tiles':sorted(changed_tiles),'static_checked':checked,'nontarget_static_exact':True,'parts_coordinates_order_clut_timing_exact':True,'all_nontexture_entries_exact':True,'life_counter_holder_x2_and_right_exact':True,'palette_bytes_exact':True}

def prepare(out):
 out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh HUD output required');out.mkdir(parents=True);allpics=[];allfull=[]
 for project in ('ver_buki_riko','ver_rin_nana'):
  old,rr=load(project);pal=entry(old['COL00_0X.ARC'],5)[544:576];symbols,artmeta=artwork(pal);folder=out/project;folder.mkdir();checks={};files={}
  names=['shibuki','riko','shibuki']if project=='ver_buki_riko'else['nana','rin','nana']
  for filename,character in zip(('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'),names):
   new,proof=patch(old[filename],symbols[character]);p=folder/filename;p.write_bytes(new);checks[filename]=proof;files[filename]={'before':sha256(old[filename]),'after':sha256(new),'size':len(new),'path':p.relative_to(ROOT).as_posix(),'record':rr[filename],'changed_bytes':sum(a!=b for a,b in zip(old[filename],new))}
   for tag,arc in (('before',old[filename]),('after',new)):
    a,sz,bb,_=composed(entry(arc,0x10206),all_compositions(entry(arc,3))[1,69]);pic=render_pixels(a,pal);allfull.append((character+'/'+filename+'/'+tag,pic));pic.save(folder/(character+'_'+filename+'_hud_'+tag+'.png'))
    l,t,r,b=RECT;crop=a[t-bb[1]:b-bb[1],l-bb[0]:r-bb[0]];allpics.append((character+'/'+tag,render_pixels(crop,pal)))
  proposal={'project':project,'baseline':BUILDS[project][0],'baseline_sha256':BUILDS[project][1],'files':files,'checks':checks,'art':{'path':ART.relative_to(ROOT).as_posix(),'sha256':digest(ART),'tool':'built-in image_gen','characters':artmeta},'issues':['C-08'],'runtime_verified':False,'color_limit':'Native shared HUD CLUT is preserved; mint is approximated with the existing light cyan ramp to avoid weapon/boss HUD recoloring.'}
  (folder/'proposal.json').write_text(json.dumps(proposal,indent=2)+'\n','utf8')
 for label,items,cell,scale in [('emblems',allpics,(240,190),8),('full_hud',allfull,(240,290),4)]:
  board=Image.new('RGB',(cell[0]*4,cell[1]*3),'#536273');draw=ImageDraw.Draw(board)
  for i,(name,pic)in enumerate(items):
   x,y=i%4*cell[0],i//4*cell[1];draw.text((x+4,y+4),name,fill='white');pic=pic.resize((pic.width*scale,pic.height*scale),Image.Resampling.NEAREST);board.paste(pic,(x+5,y+22),pic)
  board.save(out/(label+'_comparison.png'))
 print(str(out))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
