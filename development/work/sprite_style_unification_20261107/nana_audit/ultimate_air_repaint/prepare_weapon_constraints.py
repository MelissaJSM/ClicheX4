"""공중 사랑이의 기존 총몸/총구와 원래 공유 스트림·파츠 제약 추출."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from check_first_geometry import full
from make_body_cycle import source
from src.psx_player import composition_frame
SRC=N/'native_restore/nova_sync_v1/PL02_U.ARC';EXPECTED='bced7f9086a9e6a72440bab25cda7e0c87ccc121a2ffbbc970f750dee257da45'
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'weapon_constraints_v1';out.mkdir(exist_ok=False);Y,X=np.indices((384,384));rows=[];records=[]
 for n in range(33,55):
  v=full(a,n);gy,gx=np.nonzero((v==14)&(Y<160));ex,ey=int(np.median(gx)),int(np.median(gy))
  if n%2:
   area=(Y>=ey+3)&(Y<ey+11)&(X<ex+1)&(v>0);yy,xx=np.nonzero(area);mx=int(xx.min());my=ey+6;mask=(X>=mx)&(X<mx+8)&(Y>=ey+3)&(Y<ey+11);kind='held_case_candidate'
  else:
   yy,xx=np.nonzero(v);mx=int(xx.min());my=float(np.median(yy[xx==mx]));mask=(X>=mx)&(X<mx+8)&(Y>=int(np.floor(my))-2)&(Y<=int(np.ceil(my))+3);kind='firing_case_and_muzzle'
  weapon=np.where(mask,v,0).astype(np.uint8);Image.fromarray(weapon).save(out/f'case_{n:03}.png');vis=a.rgba(v,16);draw=ImageDraw.Draw(vis);yy,xx=np.nonzero(mask);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];draw.rectangle(box,outline=(255,80,40,255));items=[('original case window',vis),('case only',a.rgba(weapon,16))]
  if n%2:items.append(('new body candidate',a.rgba(np.array(Image.open(source(n))),16)))
  rows.append((f'{n} {kind}',items));f=a.banks[0]['frames'][n];shared=[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']];parts={str(pb):len(composition_frame(a.c,pb,n)['parts'])for pb in(0,5,6,7,8)}
  records.append({'ref':n,'kind':kind,'eye_world':[ex-160,ey-160],'window_world':[q-160 for q in box],'window_width':8,'muzzle_x':mx-160 if n%2==0 else None,'original_indexed_sha256':sha(weapon.tobytes()),'shared_gfx_refs':shared,'tile_count':f['tile_count'],'composition_parts':parts,'held_window_semantic_review_pending':bool(n%2)})
 for start in range(0,len(rows),4):helper.grid(rows[start:start+4],out/f'review_{start//4+1}.png',6)
 write(out/'manifest.json',{'parent_sha256':EXPECTED,'frames':records,'palette_rows_1_2_equal':bool(np.array_equal(a.words[16:32],a.words[32:48])),'scope':'Read-only extraction. Held-case8 columns are candidates pending semantic review; no sleeve imported into artwork. Firing x/muzzle are original data.','new_firing_art_complete':False,'native_packed':False});print(str(out))
if __name__=='__main__':main()
