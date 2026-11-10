"""새 사격팔을 새149몸체와 정본8x7권총에 원좌표로 연결한다."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from register_page import reg
from preview_restore import Archive,digest,sha,write,need,helper
OUT=D/'shots_registered51';BODY=D/'remaining_common51c'
POLYS={150:[(-24,-13),(-18,-13),(-14,-11),(-9,-11),(-5,-13),(-2,-11),(-2,-4),(-8,-3),(-17,-3),(-24,-4)],155:[(-21,-17),(-15,-17),(-11,-14),(-7,-12),(-5,-13),(-2,-11),(-2,-4),(-8,-4),(-15,-7),(-21,-8)]}
GUNS={150:(-24,-11,-16,-4),155:(-21,-15,-13,-8)}
def main():
 need(not OUT.exists(),'Fresh output');OUT.mkdir();gen=Path('<LOCAL_PATH>');shutil.copyfile(gen,OUT/'generated.png');im=Image.open(gen).convert('RGBA');need(im.size==(1536,1024),'Grid')
 src=json.loads((W/'staging_rn_v43.json').read_text('utf8'))['resources']['PL02_U.ARC'];p=ROOT/src['path'];need(digest(p)==src['after'],'Current parent');a=Archive(p.read_bytes());frames=[];rows=[]
 for i,n in enumerate((150,155)):
  mi=Image.new('L',(384,384));ImageDraw.Draw(mi).polygon([(160+x,160+y)for x,y in POLYS[n]],fill=1);m=np.array(mi)>0;forms={};gs=GUNS[n];gw=(slice(160+gs[1],160+gs[3]),slice(160+gs[0],160+gs[2]));gun=a.layer(n,0)[0][gw].copy();need(np.count_nonzero(gun)==32,'Canonical gun changed')
  for j,(f,paloff)in enumerate([('before',16),('after',0)]):
   pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[paloff:paloff+16]],np.float32);z=np.zeros((384,384),np.uint8);z[124:188,112:208]=reg.register(im.crop((i*768,j*512,(i+1)*768,(j+1)*512)),(96,64),pal,'area_vote');Image.fromarray(z).save(OUT/f'{f}_{n}_source.png')
   body=np.array(Image.open(BODY/f'{f}_149_indices.png'));v=np.where(m,z,body).astype(np.uint8)
   # Gun columns belong to the unchanged native pistol, including alpha.
   v[:, :160+gs[2]]=0;v[gw]=gun
   forms[f]=v
  b,v=forms['before'],forms['after'];fringe=(v>0)&(b==0);b[fringe]=v[fringe]
  for f,z in forms.items():
   Image.fromarray(z).save(OUT/f'{f}_{n:03}_indices.png');labs,k=label(z>0,np.ones((3,3)));print(json.dumps({'ref':n,'form':f,'components':np.bincount(labs.flat)[1:].tolist()}));need(np.array_equal(z[gw],gun),'Gun exact')
  rows.append((str(n),[('idle',a.composite(0)[0]),('new jacket',a.rgba(b,16)),('new bare',a.rgba(v))]));frames.append({'ref':n,'arm_polygon':POLYS[n],'gun_world_box':list(gs),'gun_indexed_sha256':sha(gun.tobytes()),'original_muzzle_preserved':True,'new_before_boundary_cells':int(fringe.sum()),'body_source':str(BODY.relative_to(ROOT)),'source_hashes':{f:digest(BODY/f'{f}_149_indices.png')for f in['before','after']},'outside_arm_body_exact_except_gun':True})
 helper.grid(rows,OUT/'comparison.png',7);write(OUT/'manifest.json',{'parent':src,'generated_sha256':digest(OUT/'generated.png'),'frames':frames,'native_packed':False,'runtime_verified':False});print(OUT)
if __name__=='__main__':main()
