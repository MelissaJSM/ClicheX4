"""선택창의19/20/21을 새 귀환156/157/158과 같은 도트로 동기화한다."""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from src.psx_player import composition_frame
from src.psx_ui_atlas import aliased_composition,local_composition,repack_frames,tile_pixels
from src.psx_static_effect import compose_static
from src.psx_disc import file_hash
from scripts.discover_inputs import psx_arc
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write

PARENT_UI_SHA='b15319740e54a2a5fabd6039502cc82d220e50eb40db61584a61d499a814a4df'
MAPPING={19:156,20:157,21:158}

def patch(old,new,ui,pal):
 need(sha(ui)==PARENT_UI_SHA,'Wrong stable selection checkpoint')
 before=Archive(old);after=Archive(new);g=entry(ui,0x10102);p=entry(ui,10);texture=g[90112:]
 need(pal[512:544]==before.p[:32]==after.p[:32],'Selection and gameplay palettes differ')
 wants={};oldrasters={};mapping=[]
 for n,k in MAPPING.items():
  comp=aliased_composition(p,2,n);px,size,bb,_=compose_static(texture,local_composition(comp));v=np.frombuffer(px,np.uint8).reshape(size[1],size[0])
  need({q['clut']for q in comp['parts']}=={0},'Unexpected original selection CLUT')
  flipped=n in(19,20)
  def orient(arr):return arr[:,::-1]if flipped else arr
  base=orient(before.layer(k)[0]);gy,gx=np.nonzero(base);uy,ux=np.nonzero(v);dx,dy=int(ux.min()-gx.min()),int(uy.min()-gy.min())
  def mapped(arr):
   arr=orient(arr);y,x=np.nonzero(arr);need((x+dx).min()>=0 and(x+dx).max()<size[0]and(y+dy).min()>=0 and(y+dy).max()<size[1],'New sprite clips original selection canvas')
   out=np.zeros_like(v);out[y+dy,x+dx]=arr[y,x];return out
  need(np.array_equal(mapped(before.layer(k)[0]),v),'Current UI is not the exact current gameplay copy')
  want=mapped(after.layer(k)[0]);wants[n]=(want.tobytes(),size);oldrasters[n]=v.copy()
  mapping.append({'ui_ref':n,'game_ref':k,'horizontal_flip':flipped,'oriented384_to_ui_translation':[dx,dy],'native_bounds':bb,'size':size,'gameplay_source_before_exact':True,'gameplay_source_after_exact':True})
 offsets=struct.unpack_from('<'+'I'*(struct.unpack_from('<I',p)[0]//4),p);lo=offsets[2];hi=min((x for x in offsets if x>lo),default=len(p));one=struct.pack('<I',4)+p[lo:hi]
 # The old irregular seven/nine tiles covered only the old silhouette.
 # Preserve the exact object transform, while using the new game's rectangles.
 updates={}
 for n,k in MAPPING.items():
  flipped=n in(19,20);rr=[]
  sourceparts=composition_frame(after.c,0,k)['parts']
  if n==20:
   # Exact coverage solved at the nine-part budget; eight rectangles suffice.
   # Coordinates are in the 160px staging canvas, not a rescaled image.
   rects=[(66,53),(80,53),(67,68),(83,68),(62,76),(84,81),(68,84),(75,88)]
   covered=np.zeros((384,384),bool)
   for x,y in rects:covered[y+80:y+96,x+80:x+96]=True
   need(not np.any((after.layer(k)[0]>0)&~covered),'Fixed exact aura coverage changed')
   sourceparts=[{'flags':0,'tile':i+1,'x':x-80,'y':y-80}for i,(x,y)in enumerate(rects)]
  for q in sourceparts:
   flags=(q['flags']&0xC0)^(0x40 if flipped else 0)
   x=-q['x']-16 if flipped else q['x'];y=q['y']+(1 if flipped else 0)
   rr.append(struct.pack('<BBbb',flags,q['tile'],x,y))
  updates[n]=b''.join(rr)
 regridded,slack=repack_parts(one,0,updates)
 finaltargets={}
 for row in mapping:
  n,k=row['ui_ref'],row['game_ref'];comp=composition_frame(regridded,0,n)
  _,size,bb,_=compose_static(texture,local_composition(comp));arr=after.layer(k)[0];sy,sx=np.nonzero(arr)
  worldx=-(sx-160)-1 if n in(19,20)else sx-160;worldy=sy-160+(1 if n in(19,20)else 0)
  v=np.zeros((size[1],size[0]),np.uint8);v[worldy-bb[1],worldx-bb[0]]=arr[sy,sx]
  finaltargets[n]=(v.tobytes(),size)
  row.update(new_native_bounds=bb,new_size=size,new_part_count=len(comp['parts']),wholebody_native_transform={'x':'-x-1'if n in(19,20)else'x','y':'y+1'if n in(19,20)else'y'})
 ng,np_,info=repack_frames(texture,regridded,0,finaltargets,guard_uv_zero=True)
 newp=p[:lo]+np_[4:]+p[hi:];result=replace_entry(replace_entry(ui,0x10102,g[:90112]+ng),10,newp)
 need(g[:90112]==entry(result,0x10102)[:90112],'Large portrait/background changed')
 need(p[:lo]==newp[:lo]and p[hi:]==newp[hi:],'Other composition banks changed')
 count=aliased_composition(p,2,0)['bank_frame_count'];preserved=[]
 for n in range(count):
  oc=aliased_composition(p,2,n);nc=aliased_composition(newp,2,n);opx,osz,obb,_=compose_static(texture,local_composition(oc));npx,nsz,nbb,_=compose_static(ng,local_composition(nc))
  if n in MAPPING:need(npx==finaltargets[n][0],'New selection target differs')
  else:
   need((osz,obb)==(nsz,nbb),'Other selection canvas/origin changed')
   need(len(oc['parts'])==len(nc['parts']),'Other selection part count changed')
   for o,q in zip(oc['parts'],nc['parts']):need(p[o['record_offset']:o['record_offset']+4]==newp[q['record_offset']:q['record_offset']+4],'Other selection part record bytes changed')
   need(npx==opx,'Other selection pixels differ');preserved.append(n)
 for e in psx_arc(ui):
  t=int(e['type'],16)
  if t not in(0x10102,10):need(entry(ui,t)==entry(result,t),'Other selection entry changed')
 changedtiles=[n for n in range(len(texture)//128)if tile_pixels(texture,n)!=tile_pixels(ng,n)]
 proof={'passed':True,'source_ui_sha256':sha(ui),'new_ui_sha256':sha(result),'target_bank':2,'target_refs':sorted(MAPPING),'mapping':mapping,'total_small_frames':count,'unchanged_small_frames':preserved,'unchanged_small_frames_count':len(preserved),'unchanged_small_frame_records_byte_exact':True,'texture_entry':'0x10102','protected_portrait_byte_range':[0,90112],'texture_tile_indices_changed':changedtiles,'composition_entry':'0x0A','composition_bank_fixed_range':[lo,hi],'composition_slack':slack,'palette_clut_wholebody_transform_and_other_entries_unchanged':True,'selected_rectangle_reassignment':True,'save_ui_unchanged_reason':'MOJIPAT/LOAD use unchanged idle0; these return refs are not save-frame sources.','packing':info,'runtime_emulator_test':False}
 return result,proof,oldrasters,finaltargets

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source BIN changed');data=read_disc(SOURCE,('PL00_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0]
 parent=H/'prepared_lowhp_return01';out=H/'prepared_front_return01';game=(out/'PL00_U.ARC').read_bytes()
 result,proof,olds,wants=patch((parent/'PL00_U.ARC').read_bytes(),game,(parent/'ST0E_U1.ARC').read_bytes(),entry(data['COL0E_U1.ARC'],5))
 need(not(out/'ST0E_U1.ARC').exists(),'Selection output exists');(out/'ST0E_U1.ARC').write_bytes(result);write(out/'ui_verification.json',proof)
 proposal=json.loads((out/'proposal.json').read_text('utf8'));proposal['files']['ST0E_U1.ARC']={'path':(out/'ST0E_U1.ARC').relative_to(ROOT).as_posix(),'before':sha(data['ST0E_U1.ARC']),'after':sha(result)};write(out/'proposal.json',proposal)
 arc=Archive(game);board=Image.new('RGB',(3*384,500),'#1a202b');dr=ImageDraw.Draw(board)
 for col,n in enumerate(MAPPING):
  for row,(label,v)in enumerate((('current',olds[n]),('prepared',np.frombuffer(wants[n][0],np.uint8).reshape(wants[n][1][1],wants[n][1][0])))):
   im=arc.rgba(v);im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);board.paste(im,(col*384+(384-im.width)//2,row*250+20),im);dr.text((col*384+4,row*250+4),f'Select {n} / {label} / game {MAPPING[n]}',fill='white')
 board.save(out/'selection19_21_comparison.png');print(json.dumps(proof))

if __name__=='__main__':main()
