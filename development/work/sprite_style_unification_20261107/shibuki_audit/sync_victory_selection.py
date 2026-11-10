"""선택18만 게임승리207의 x,y-1 사본으로 교체한다."""
from pathlib import Path
import sys,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from src.psx_player import composition_frame
from src.psx_ui_atlas import aliased_composition,local_composition,repack_frames,tile_pixels
from src.psx_static_effect import compose_static
from scripts.discover_inputs import psx_arc
PARENT_SHA='80da6cbfa706a3fce1f79133390ed12b719940046e7670eebda81977d1e2325b'

def patch(before_game,after_game,ui,palette):
 need(sha(ui)==PARENT_SHA,'Wrong current selection parent');before=Archive(before_game);after=Archive(after_game)
 need(palette[512:544]==before.p[:32]==after.p[:32],'Selection and game palettes differ')
 g=entry(ui,0x10102);p=entry(ui,10);texture=g[90112:]
 def decode(texture,parts,n,bank=2):
  cp=aliased_composition(parts,bank,n);px,size,bb,_=compose_static(texture,local_composition(cp))
  q=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);a=np.zeros((384,384),np.uint8);yy,xx=np.nonzero(q);a[yy+bb[1]+160,xx+bb[0]+160]=q[yy,xx];return a,cp,(size,bb)
 def orient(v):
  a=np.zeros_like(v);yy,xx=np.nonzero(v);a[yy-1,xx]=v[yy,xx];return a
 previous,oldcomp,_=decode(texture,p,18);need(np.array_equal(previous,orient(before.layer(207)[0])),'Original18 is not exact207 y-1')
 offsets=struct.unpack_from('<'+'I'*(struct.unpack_from('<I',p)[0]//4),p);lo=offsets[2];hi=min((x for x in offsets if x>lo),default=len(p));one=struct.pack('<I',4)+p[lo:hi]
 rr=[]
 for q in composition_frame(after.c,0,207)['parts']:rr.append(struct.pack('<BBbb',q['flags'],q['tile'],q['x'],q['y']-1))
 altered,slack=repack_parts(one,0,{18:b''.join(rr)});cp=composition_frame(altered,0,18);_,size,bb,_=compose_static(texture,local_composition(cp));target=orient(after.layer(207)[0]);target_small=target[bb[1]+160:bb[3]+160,bb[0]+160:bb[2]+160]
 ng,np_,info=repack_frames(texture,altered,0,{18:(target_small.tobytes(),size)},guard_uv_zero=True)
 newp=p[:lo]+np_[4:]+p[hi:];result=replace_entry(replace_entry(ui,0x10102,g[:90112]+ng),10,newp)
 need(len(result)==len(ui),'UI size changed');need(entry(result,0x10102)[:90112]==g[:90112],'Portrait/background changed')
 need(p[:lo]==newp[:lo]and p[hi:]==newp[hi:],'Other UI banks changed')
 count=oldcomp['bank_frame_count'];preserved=[]
 for n in range(count):
  a,oc,meta=decode(texture,p,n);b,nc,newmeta=decode(ng,newp,n)
  if n==18:need(np.array_equal(b,target),'New18 is not exact207 y-1')
  else:
   need(meta==newmeta and np.array_equal(a,b),'Other UI display/origin changed')
   need(len(oc['parts'])==len(nc['parts']),'Other UI part count changed')
   for x,y in zip(oc['parts'],nc['parts']):need(p[x['record_offset']:x['record_offset']+4]==newp[y['record_offset']:y['record_offset']+4],'Other UI part bytes changed')
   preserved.append(n)
 for e in psx_arc(ui):
  t=int(e['type'],16)
  if t not in(0x10102,10):need(entry(ui,t)==entry(result,t),'Other UI entry changed')
 proof=dict(passed=True,before=sha(ui),after=sha(result),target_bank=2,target_refs=[18],game_ref=207,transform={'x':'x','y':'y-1'},before_after_exact=True,palette_same=True,unchanged_frames=preserved,unchanged_frame_count=len(preserved),unchanged_frame_records_byte_exact=True,composition_bank_range=[lo,hi],composition_slack=slack,changed_tiles=[n for n in range(len(texture)//128)if tile_pixels(texture,n)!=tile_pixels(ng,n)],protected_portrait_bytes=90112,packing=info,runtime_verified=False)
 return result,proof,previous,target
