"""선택창의 기본형 귀환158 사본만 새 게임몸과 정확히 동기화한다."""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry,replace_entry
from src.psx_ui_atlas import aliased_composition,local_composition,repack_frames
from src.psx_static_effect import compose_static
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash
from scripts.discover_inputs import psx_arc

def patch(old,new,ui,pal):
 need(sha(ui)=='131645e5e28f51411bfa192a45b967f69097f805d060aaa8351273c89e9dec46','Wrong current selection source')
 before=Archive(old);after=Archive(new);g=entry(ui,0x10102);p=entry(ui,10);texture=g[90112:]
 comp=aliased_composition(p,2,21);px,size,bb,_=compose_static(texture,local_composition(comp));v=np.frombuffer(px,np.uint8).reshape(size[1],size[0])
 base=before.layer(158)[0];gy,gx=np.nonzero(base);uy,ux=np.nonzero(v);dx,dy=int(ux.min()-gx.min()),int(uy.min()-gy.min())
 need(pal[512:544]==before.p[:32]and{q['clut']for q in comp['parts']}=={0},'Selection CLUT differs from gameplay')
 def mapped(arr):
  y,x=np.nonzero(arr);need((x+dx).min()>=0 and(x+dx).max()<size[0]and(y+dy).min()>=0 and(y+dy).max()<size[1],'Sprite clips UI canvas')
  out=np.zeros_like(v);out[y+dy,x+dx]=arr[y,x];return out
 need(np.array_equal(mapped(base),v),'Current UI is not the gameplay158 copy')
 want=mapped(after.layer(158)[0]);offsets=struct.unpack_from('<'+'I'*(struct.unpack_from('<I',p)[0]//4),p);lo=offsets[2];hi=min((x for x in offsets if x>lo),default=len(p));one=struct.pack('<I',4)+p[lo:hi]
 ng,np_,info=repack_frames(texture,one,0,{21:(want.tobytes(),size)},guard_uv_zero=True)
 newp=p[:lo]+np_[4:]+p[hi:];result=replace_entry(replace_entry(ui,0x10102,g[:90112]+ng),10,newp)
 need(g[:90112]==entry(result,0x10102)[:90112],'Portrait/background changed')
 need(p[:lo]==newp[:lo]and p[hi:]==newp[hi:],'Other banks changed')
 count=comp['bank_frame_count'];preserved=0
 for n in range(count):
  oc=aliased_composition(p,2,n);nc=aliased_composition(newp,2,n)
  opx,osz,obb,_=compose_static(texture,local_composition(oc));npx,nsz,nbb,_=compose_static(ng,local_composition(nc))
  need((osz,obb)==(nsz,nbb),'UI origin changed')
  for o,q in zip(oc['parts'],nc['parts']):need(all(o[k]==q[k]for k in('x','y','flip_x','flip_y','clut')),'UI native geometry changed')
  need((npx==want.tobytes())if n==21 else(opx==npx),'Unrelated UI frame changed')
  preserved+=n!=21
 for e in psx_arc(ui):
  t=int(e['type'],16)
  if t not in(0x10102,10):need(entry(ui,t)==entry(result,t),'Other UI entry changed')
 return result,{'passed':True,'source_ui_sha256':sha(ui),'new_ui_sha256':sha(result),'target_bank':2,'target_ref':21,'gameplay_ref':158,'game_to_ui_translation':[dx,dy],'native_bounds':bb,'source_pixels_equal_before':True,'target_pixels_equal_after':True,'unchanged_ui_frames':preserved,'palette_clut_geometry_unchanged':True,'save_ui_reason_unchanged':'MOJIPAT/LOAD saves use idle0 and its four armor layers;158 is not a save-frame source.','packing':info},v,want

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source BIN changed');data=read_disc(SOURCE,('PL00_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0];out=H/'prepared_return158_01';new=(out/'PL00_U.ARC').read_bytes()
 result,proof,old,newv=patch(data['PL00_U.ARC'],new,data['ST0E_U1.ARC'],entry(data['COL0E_U1.ARC'],5))
 (out/'ST0E_U1.ARC').write_bytes(result);write(out/'ui_verification.json',proof)
 prop=json.loads((out/'proposal.json').read_text('utf8'));prop['files']['ST0E_U1.ARC']={'path':(out/'ST0E_U1.ARC').relative_to(ROOT).as_posix(),'before':sha(data['ST0E_U1.ARC']),'after':sha(result)};write(out/'proposal.json',prop)
 a=Archive(data['PL00_U.ARC']);board=Image.new('RGB',(64*5*2,80*5+28),'#1a202b');dr=ImageDraw.Draw(board)
 for i,(label,v)in enumerate((('selection21 before',old),('selection21 after',newv))):
  im=a.rgba(v).resize((64*5,80*5),Image.Resampling.NEAREST);board.paste(im,(i*320,28),im);dr.text((i*320+4,5),label,fill='white')
 board.save(out/'selection21_comparison.png');print(json.dumps(proof))
if __name__=='__main__':main()
