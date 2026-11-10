"""생성원화8셀부터 의미영역/정본권총/20층을 재구성한다(제작자 검사)."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,digest,sha,write,need
from pack_native import PARENT,BEFORE,REFS,PBS
from prepare_canonical_weapon import REMOVE,HAND
spec=importlib.util.spec_from_file_location('quantize_native',N/'base_run_repaint/register_page.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
Y,X=np.indices((384,384));Y-=160;X-=160
read=lambda p:json.loads(p.read_text('utf8'))
def check(z,p):need(np.array_equal(z,np.array(Image.open(p))),str(p));return z
def rect(q):x0,y0,x1,y1=q;return (X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
def main():
 out=D/'packed_victory_candidate_v1';lock=read(out/'INPUT_FROZEN.json')
 for q in lock['files']:need(digest(ROOT/q['path'])==q['sha256'],'잠금 '+q['path'])
 a=Archive(PARENT.read_bytes());native={};cells=[]
 for group in('a','b'):
  m=read(D/f'{group}_registered_v1/registration.json');art=ROOT/m['source_art_path'];need(digest(art)==m['source_art_sha256'],'원화해시');im=Image.open(art).convert('RGBA')
  for q in m['frames']:
   n,f=q['ref'],q['form'];palstart=16 if f=='before'else 0;pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[palstart:palstart+16]],np.float32);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(im.crop(q['source_crop']),(96,96),pal,'area_vote');check(z,D/f'{group}_registered_v1/{f}_{n:03}_indices.png');native[f,n]=z;cells.append({'ref':n,'form':f,'source_art_sha256':digest(art),'source_crop':q['source_crop'],'native_sha256':sha(z.tobytes())})
 bodies={}
 for q in read(D/'costume_pair_probe_v2/manifest.json')['frames']:
  n=q['ref'];b=native['before',n];donor=native['after',n];im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in q['costume_polygon']],fill=1);m=np.array(im)>0
  for x,y,v in q['after_hair_excluded_from_costume']:need(donor[y+160,x+160]==v,'옆머리 원화 표본');m[y+160,x+160]=False
  c=b.copy();c[b==15]=13;af=np.where(m,donor,c).astype(np.uint8);check(b,D/f'costume_pair_probe_v2/before_{n:03}.png');check(af,D/f'costume_pair_probe_v2/after_{n:03}.png');bodies['before',n]=b;bodies['after',n]=af
 wm=read(D/'canonical_weapon_probe_v1/manifest.json');donor=a.layer(85)[0];mask=rect((-22,-11,-14,-5))&np.isin(donor,range(1,10));coords=[(int(x-160),int(y-160),int(donor[y,x]))for y,x in np.argwhere(mask)];need(coords==[tuple(v)for v in wm['canonical_texels']],'실제 정본85의20texel');weapons=[]
 for q in wm['frames']:
  n,f=q['ref'],q['form'];old=bodies[f,n];z=old.copy()
  if q['new_weapon']:
   rm=rect(REMOVE[n])&np.isin(old,range(1,10));skin=rect(HAND[n])&np.isin(old,(10,11,12,13));case=np.zeros_like(old)
   for x,y,v in coords:tx,ty=np.array(q['matrix'])@np.array([x,y])+q['translation'];case[ty+160,tx+160]=v
   z[rm]=0;z[(case>0)&~skin]=case[(case>0)&~skin];z[skin]=old[skin];check(case,D/f'canonical_weapon_probe_v1/{f}_{n:03}_case.png');weapons.append({'ref':n,'form':f,'texels':20,'matrix':q['matrix'],'translation':q['translation']})
  bodies[f,n]=check(z,D/f'canonical_weapon_probe_v1/{f}_{n:03}_indices.png')
 count=0
 for n in REFS:
  b=bodies['before',n];af=bodies['after',n];ls={0:af,5:np.where((b!=af)|(b==15),b,0).astype(np.uint8),6:np.zeros_like(b),7:np.zeros_like(b),8:np.zeros_like(b)}
  for pb,z in ls.items():check(z,D/f'final_targets_v1/layer{pb}_{n:03}.png');count+=1
 write(out/'source_reconstruction.json',{'passed':True,'candidate_sha256':digest(out/'PL02_U.ARC'),'parent_sha256':BEFORE,'input_files_verified':len(lock['files']),'generated_pages':2,'fixed_cell_registrations':cells,'canonical_weapon':weapons,'semantic_hair_cells_not_cloth':2,'target_layers_reconstructed':count,'manual_painted_pixels':0,'scope':'제작자 실제 원화2장8고정셀→의상/공통부/정본85→20층 재구성.별도 reader/원MIPS/게임실기와 구분.','runtime_verified':False});print(json.dumps({'sources':len(cells),'layers':count,'passed':True}))
if __name__=='__main__':main()
