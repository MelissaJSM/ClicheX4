"""새 팔 원화만 의미영역에 등록한다. 원총구와 새 머리/하지 보호."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
SRC=D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC';EXPECTED='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'
def main():
 p=argparse.ArgumentParser();p.add_argument('--page',choices=list('abcd'),required=True);p.add_argument('--form',choices=['before','after'],default='before');p.add_argument('--regions',default='firing_regions_v1.json');p.add_argument('--version',default='v1');args=p.parse_args()
 need(digest(SRC)==EXPECTED,'Frozen source');a=Archive(SRC.read_bytes());out=D/f'firing_{args.page}_{args.form}_joint_probe_{args.version}';out.mkdir(exist_ok=False);inputs=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'));reg=json.loads((D/f'firing_{args.page}_{args.form}_registered_v1/registration.json').read_text('utf8'));polys=json.loads((D/args.regions).read_text('utf8'));off=16 if args.form=='before'else 0;Y,X=np.indices((384,384));Y-=160;X-=160;records=[];rows=[]
 for r in reg['frames']:
  n=r['ref'];q=next(z for z in inputs['frames']if z['ref']==n);bp=ROOT/q['sources'][args.form]['body_path'];sp=D/f'firing_{args.page}_{args.form}_registered_v1/{args.form}_{n:03}.png';b=np.array(Image.open(bp));s=np.array(Image.open(sp));need(digest(bp)==q['sources'][args.form]['body_sha256']and sha(s.tobytes())==r['index_sha256'],'Input provenance');case=np.array(Image.open(D/f'firing_inputs_v1/{args.form}_case_{n:03}.png'));held=np.array(Image.open(ROOT/q['held_gun_path']));poly=polys[str(n)]
  extra=[]
  if isinstance(poly,dict):extra=poly.get('source_cells',[]);poly=poly['polygon']
  mi=Image.new('1',(384,384));ImageDraw.Draw(mi).polygon([(x+160,y+160)for x,y in poly],fill=1);mask=np.array(mi).astype(bool);ex,ey=r['eye_world'];head=(X>=ex-6)&(Y<=ey+4)&(b>0);mask&=~head;mask|=held>0
  for x,y,before,after in extra:
   need(int(b[y+160,x+160])==before and int(s[y+160,x+160])==after,'Exact source cell');need(not head[y+160,x+160],'Cell outside head');mask[y+160,x+160]=True
  t=b.copy();t[mask]=s[mask]
  x0,y0,x1,y1=q['window_world'];window=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1);t[window]=case[window];allowed=mask|window;need(np.array_equal(t[~allowed],b[~allowed]),'Outside arm exact');need(np.array_equal(t[head&~window&~(held>0)],b[head&~window&~(held>0)]),'New head');need(np.array_equal(t[window],case[window]),'Original case window exact');lower=(Y>max(y for x,y in poly))&~allowed;need(np.array_equal(t[lower],b[lower]),'New lower body exact')
  labs,count=label(t>0,np.ones((3,3)));sizes=np.bincount(labs.ravel());small=[{'size':int(sizes[k]),'world':[[int(x-160),int(y-160)]for y,x in zip(*np.nonzero(labs==k))]}for k in range(1,count+1)if sizes[k]<20]
  for name,v in((args.form,t),('source_arm',np.where(mask,s,0)),('replacement_mask',mask.astype(np.uint8)*255),('protected_head',head.astype(np.uint8)*255)):Image.fromarray(v.astype(np.uint8)).save(out/f'{name}_{n:03}.png')
  records.append({'ref':n,'body_path':bp.relative_to(ROOT).as_posix(),'body_sha256':digest(bp),'arm_path':sp.relative_to(ROOT).as_posix(),'arm_sha256':digest(sp),'polygon':poly,'exact_source_cells':extra,'head_protected_eye_relative':[ex-6,ey+4],'same_coordinate_registration':True,'arm_rescale_or_stretch':False,'original_weapon_window_exact':True,'outside_replacement_exact':True,'lower_body_exact_below':max(y for x,y in poly),'changed_pixels':int((t!=b).sum()),'index_sha256':sha(t.tobytes()),'components8':int(count),'small_components':small})
  rows.append((f'run firing {n} {args.form}',[('fixed new body',a.rgba(b,off)),('new arm source',a.rgba(s,off)),('local arm / original pistol',a.rgba(t,off))]))
 for i in(0,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'registration.json',{'parent_arc_sha256':EXPECTED,'regions_sha256':digest(D/args.regions),'frames':records,'scope':'새 팔/원 접힌 손 위치만 동일좌표 원화 등록. 총구8열은 현PL02 실제 원색이고 새 머리·하지는 보호한다.','native_packed':False,'runtime_verified':False,'art_review_pending':True});print(json.dumps({q['ref']:{'components':q['components8'],'small':q['small_components']}for q in records}))
if __name__=='__main__':main()
