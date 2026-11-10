"""C-09/R-01/R-02: 기준 BIN 불변, 실제 로더 색상표와 UI 경계만 수정한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_ui_inventory import BUILDS,D,load
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_hud_emblems import all_compositions,composed,render_pixels
from scripts.prepare_ui_revision import pause_background
from scripts.build_rin_pause import composition
from scripts.discover_inputs import sha256,psx_arc
from src.psx_ui_atlas import local_composition,tile_pixels,write_tile
from src.psx_static_effect import patch_static
from src.psx_ui_render import render_static_rgba

def require(x,msg):
 if not x:raise ValueError(msg)

def life(arc,kind):
 tex,parts=entry(arc,0x10206),entry(arc,3);comps=all_compositions(parts);selected={(3,n)for n in range(89,99)}
 used={p['page']*256+p['tile']for c in comps.values()for p in c['parts']};free=iter(sorted(set(range(len(tex)//128))-used));mapping={}
 remap=({2:2,4:8,6:5,7:14,8:9}if kind=='shibuki'else{7:8,9:1,13:2,14:11,15:1})
 tg=bytearray(tex);np_=bytearray(parts);allowed=set();head_offsets=set()
 for tile in (513,514,515):
  dest=next(free,None);require(dest is not None,'No private life-bubble capacity');mapping[tile]=dest
  a=tile_pixels(tex,tile);b=bytes(remap.get(v,v)for v in a);require(bytes(bool(v)for v in a)==bytes(bool(v)for v in b),'Bubble alpha changed');write_tile(tg,dest,b)
 for key in selected:
  for p in comps[key]['parts']:
   off=p['record_offset'];tile=p['page']*256+p['tile']
   if tile in mapping:
    dest=mapping[tile];np_[off:off+2]=bytes(((p['flags']&~15)|dest//256,dest%256));allowed.update((off,off+1))
   elif kind=='riko':
    require(p['clut']==1,'Expected Riko face CLUT+1');np_[off]=p['flags']&~12;allowed.add(off);head_offsets.add(off)
 ng,nc=bytes(tg),bytes(np_);newcomps=all_compositions(nc);checked=0
 static={1,2,3,4,6}if kind=='riko'else{1,2,3,4,*range(9,22)}
 for key,c in comps.items():
  if key not in selected:
   require(c==newcomps[key],'Life parts alias another frame')
   if key[0]in static:
    a,sz,bb,_=composed(tex,c);b,ns,nb,_=composed(ng,newcomps[key]);require(sz==ns and bb==nb and np.array_equal(a,b),'Non-life frame changed');checked+=1
  else:
   for p,q in zip(c['parts'],newcomps[key]['parts']):
    require(all(p[k]==q[k]for k in ('x','y','flip_x','flip_y','unknown_flags')),'Life geometry changed')
    require(q['clut']==0,'Life no longer uses intended shared COL11')
 require(all(a==b or i in allowed for i,(a,b)in enumerate(zip(parts,nc))),'Unowned parts byte changed')
 for t in range(len(tex)//128):
  if t not in mapping.values():require(tile_pixels(tex,t)==tile_pixels(ng,t),'Unowned static tile changed')
 return replace_entry(replace_entry(arc,3,nc),0x10206,ng),{'selected_frames':sorted(n for b,n in selected),'private_bubble_tiles':mapping,'bubble_remap':remap,'riko_face_clut_records':len(head_offsets),'protected_static_frames':checked,'geometry_alpha_timing_unchanged':True,'actual_palette_row':11}

def pause(arc,original):
 c=composition(arc);g=entry(arc,0x10007);a,sz,bb,_=composed(g[12288:],c);native,ns,nb,_=composed(entry(original,0x10007)[12288:],composition(original));require(sz==ns and bb==nb,'Pause geometry unexpectedly changed')
 mask=native>0;yy,xx=np.nonzero(mask);targetbox=(int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1)
 yy,xx=np.nonzero(a);box=(int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1);crop=a[box[1]:box[3],box[0]:box[2]]
 w,h=targetbox[2]-targetbox[0],targetbox[3]-targetbox[1];scale=min(w/crop.shape[1],h/crop.shape[0]);size=(round(crop.shape[1]*scale),round(crop.shape[0]*scale))
 fitted=np.array(Image.fromarray(crop).resize(size,Image.Resampling.NEAREST));after=np.zeros_like(a);x=targetbox[0]+(w-size[0])//2;y=targetbox[3]-size[1];after[y:y+size[1],x:x+size[0]]=fitted;after[~mask]=0
 ng=patch_static(g[12288:],{10:local_composition(c)},{10:(after.tobytes(),sz)});new=replace_entry(arc,0x10007,g[:12288]+ng)
 got,gs,gb,_=composed(entry(new,0x10007)[12288:],c);require(np.array_equal(got,after)and gs==sz and gb==bb,'Pause roundtrip differs');require(not np.any((got>0)&~mask),'Pause escapes original window')
 return new,{'frame':10,'before_opaque_bbox':box,'original_window_bbox':targetbox,'after_origin':[x,y],'size':list(size),'uniform_scale':scale,'before_outside_window_pixels':int(np.count_nonzero((a>0)&~mask)),'after_outside_window_pixels':0,'part_coordinates_and_palette_exact':True,'nearest_index_resampling':True}

def loading(exe):
 out=bytearray(exe);table=0xded04
 require(struct.unpack_from('<h',exe,table+8)[0]==200 and struct.unpack_from('<h',exe,table+16)[0]==248,'Unexpected current logo coordinates')
 struct.pack_into('<h',out,table+8,184);struct.pack_into('<h',out,table+16,232)
 edits=[{'offset':i,'before':a,'after':b}for i,(a,b)in enumerate(zip(exe,out))if a!=b]
 require([x['offset']for x in edits]==[table+8,table+16],'Logo edit escaped X fields')
 return bytes(out),{'loading_before_x':[200,248],'loading_after_x':[184,232],'shift_x':-16,'width':112,'right_margin_before':8,'right_margin_after':24,'y':192,'exe_data_edits':edits,'instruction_uv_palette_text_exact':True,'other_screens':'Main title centered at x40 width240; repeated background motifs intentionally tile across edges, unchanged.'}

def board(items,path,cell=(340,270),cols=3):
 im=Image.new('RGB',(cols*cell[0],((len(items)+cols-1)//cols)*cell[1]),'#536273');d=ImageDraw.Draw(im)
 for i,(label,pic)in enumerate(items):
  x,y=i%cols*cell[0],i//cols*cell[1];d.text((x+4,y+4),label,fill='white');im.paste(pic,(x+4,y+23),pic)
 im.save(path)

def prepare(out):
 out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh UI output required');out.mkdir(parents=True);original,_=load('original');previews=[];lifepics=[]
 for project in ('ver_buki_riko','ver_rin_nana'):
  old,records=load(project);new={};checks={};folder=out/project;folder.mkdir()
  new['SLUS_005.61'],checks['C-09']=loading(old['SLUS_005.61'])
  if project=='ver_buki_riko':
   for name,kind in (('PL00_U.ARC','shibuki'),('PL01_U.ARC','riko'),('PL02_U.ARC','shibuki')):
    a,checks[name+'_life']=life(old[name],kind);a,checks[name+'_pause']=pause(a,original[name]);new[name]=a
    for tag,arc in (('before',old[name]),('after',a)):
     c=composition(arc);v,sz,bb,_=composed(entry(arc,0x10007)[12288:],c);pic=render_pixels(v,entry(arc,0x11)[320:352]);bg=pause_background(arc);bg.alpha_composite(pic,(64+bb[0],192+bb[1]));previews.append((name+'/'+tag,bg));bg.save(folder/(name+'_pause_'+tag+'.png'))
   palette_by_code={'X':entry(old['PL00_U.ARC'],9)[352:384],'Z':entry(old['PL01_U.ARC'],9)[384:416]};stage_checks=[]
   for name,arc in old.items():
    if not(name.startswith('COL')and name.endswith(('X.ARC','Z.ARC'))and name[3:5]not in('0D','0E','0F')):continue
    code=name[-5];pal=entry(arc,5);npal=pal[:352]+palette_by_code[code]+pal[384:];new[name]=replace_entry(arc,5,npal);stage_checks.append(name)
   require(len(stage_checks)==48,'Expected 24 X and 24 Zero gameplay palettes');checks['R-01_stage_copies']=stage_checks
   for name,code in (('PL00_U.ARC','X'),('PL01_U.ARC','Z'),('PL02_U.ARC','X')):
    for tag,d in (('before',old),('after',{**old,**new})):
     pal=entry(d['COL00_0'+code+'.ARC'],5);pals={i:struct.unpack_from('<16H',pal,(11+i)*32)for i in range(4)}
     for n in (89,91,94,95,98):
      cp=all_compositions(entry(d[name],3))[3,n];im,bb=render_static_rgba(entry(d[name],0x10206),cp,pals);im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST);lifepics.append((name+'/'+tag+'/'+str(n),im))
  files={}
  for name,v in new.items():
   require(len(v)==len(old[name]),'Resource resized');p=folder/name;p.write_bytes(v);files[name]={'before':sha256(old[name]),'after':sha256(v),'size':len(v),'path':p.relative_to(ROOT).as_posix(),'record':records[name],'changed_bytes':sum(a!=b for a,b in zip(old[name],v))}
  proposal={'project':project,'baseline':BUILDS[project][0],'baseline_sha256':BUILDS[project][1],'files':files,'checks':checks,'issues':['C-09']+(['R-01','R-02']if project=='ver_buki_riko'else[]),'runtime_verified':False}
  (folder/'proposal.json').write_text(json.dumps(proposal,indent=2)+'\n','utf8')
 board(previews,out/'pause_before_after.png');board(lifepics,out/'life_actual_clut_before_after.png',(180,175),5);print(str(out))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();prepare(a.output)
