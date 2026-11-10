"""새 원화 팔과 접힌 손 영역만 같은 좌표로 등록하는 첫 후보."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
SRC=N/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';EXPECTED='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031'
POLYS={
68:[(-45,-10),(-13,-10),(-13,-4),(-10,-4),(-10,-2),(-6,-2),(-6,-1),(-3,-1),(-3,2),(-4,2),(-4,6),(-5,7),(-45,7)],
70:[(-45,-4),(-22,-4),(-22,2),(-18,2),(-18,3),(-12,3),(-8,4),(-8,6),(-11,6),(-11,9),(-45,9)],
72:[(-45,2),(-25,2),(-25,10),(-20,10),(-20,11),(-16,11),(-14,11),(-7,12),(-7,14),(-10,14),(-10,16),(-45,16)],
76:[(-45,2),(-25,2),(-25,10),(-21,10),(-21,12),(-16,12),(-10,13),(-10,14),(-13,14),(-13,16),(-45,16)],
78:[(-45,-10),(-14,-10),(-14,-4),(-10,-4),(-10,-2),(-6,-2),(-1,-1),(-1,3),(-4,3),(-4,6),(-45,6)],
80:[(-45,-11),(-10,-11),(-10,-4),(-6,-4),(-3,-3),(1,-2),(1,3),(-2,3),(-2,4),(-45,4)],
82:[(-45,-10),(2,-10),(2,-7),(8,-7),(11,-6),(11,-2),(8,-1),(5,0),(5,3),(-45,3)],
84:[(-45,-10),(-9,-10),(-9,-6),(-5,-6),(-1,-5),(-1,1),(-5,1),(-5,5),(-45,5)]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--page',choices=['a','b'],required=True);p.add_argument('--form',choices=['before','after'],default='before');p.add_argument('--version',default='v3');v=p.parse_args();need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/f'firing_{v.page}_{v.form}_joint_probe_{v.version}';out.mkdir(exist_ok=False);inp=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'));reg=json.loads((D/f'firing_{v.page}_{v.form}_registered_v1/registration.json').read_text('utf8'));off=16 if v.form=='before'else 0;Y,X=np.indices((384,384));Y-=160;X-=160;rows=[];recs=[]
 for r in reg['frames']:
  n=r['ref'];q=next(x for x in inp['frames']if x['ref']==n);bp=ROOT/q['sources'][v.form]['body_path'];sp=D/f'firing_{v.page}_{v.form}_registered_v1/{v.form}_{n:03}.png';b=np.array(Image.open(bp));s=np.array(Image.open(sp));case=np.array(Image.open(D/f'firing_inputs_v1/{v.form}_case_{n:03}.png'));poly=POLYS[n];m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon([(x+160,y+160)for x,y in poly],fill=1);mask=np.array(m).astype(bool);ex,ey=r['eye_world'];head=(X>=ex-6)&(Y<=ey+4)&(b>0);mask&=~head;t=b.copy();t[mask]=s[mask]
  cleanup=[]
  if v.form in ('before','after'):
   for x,y in {72:[(-13,17)],76:[(-18,17)],80:[(-4,5)]}.get(n,[]):
    need(b[y+160,x+160]==5 and s[y+160,x+160]==0,'Old folded cuff/new source alpha');mask[y+160,x+160]=True;t[y+160,x+160]=s[y+160,x+160];cleanup.append({'world':[x,y],'before_index':5,'source_index':0,'meaning':'접힌 소매 끝 고립점. 새 사격 원화의 실제 투명 위치로 교체.'})
  x0,y0,x1,y1=q['window_world'];window=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1);t[window]=case[window];allowed=mask|window;need(np.array_equal(t[~allowed],b[~allowed]),'Other body');need(np.array_equal(t[head&~window],b[head&~window]),'Head');need(np.array_equal(t[window],case[window]),'Original weapon');lower=(Y>max(y for x,y in poly))&~mask;need(np.array_equal(t[lower],b[lower]),'Lower body');labs,count=label(t>0,np.ones((3,3)));sizes=np.bincount(labs.flat);small=[{'size':int(sizes[k]),'world':[[int(x-160),int(y-160)]for y,x in zip(*np.nonzero(labs==k))]}for k in range(1,count+1)if sizes[k]<20]
  for name,ar in[(v.form,t),('source_arm',np.where(mask,s,0)),('replacement_mask',mask.astype(np.uint8)*255),('protected_head',head.astype(np.uint8)*255)]:Image.fromarray(ar.astype(np.uint8)).save(out/f'{name}_{n:03}.png')
  recs.append({'ref':n,'body_path':bp.relative_to(ROOT).as_posix(),'body_sha256':digest(bp),'arm_path':sp.relative_to(ROOT).as_posix(),'arm_sha256':digest(sp),'polygon':poly,'folded_cuff_alpha_correction':cleanup,'head_protected_eye_relative':[ex-6,ey+4],'same_coordinate_registration':True,'arm_rescale_or_stretch':False,'original_weapon_window_exact':True,'outside_replacement_exact':True,'lower_body_exact_below_except_source_cuff':max(y for x,y in poly),'changed_pixels':int((t!=b).sum()),'index_sha256':sha(t.tobytes()),'components8':int(count),'small_components':small})
  rows.append((f'new firing {n} {v.form}',[('fixed new body',a.rgba(b,off)),('new arm source',a.rgba(s,off)),('local arm / original weapon',a.rgba(t,off))]))
 for i in(0,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'registration.json',{'parent_arc_sha256':EXPECTED,'frames':recs,'scope':'원화의 팔/옛 접힌 손 의미영역만 동일좌표 채택. 총구8열은 현PL02 실제원색. 새머리·하지 보호.','native_packed':False,'runtime_verified':False,'art_review_pending':True});print(out)
if __name__=='__main__':main()
