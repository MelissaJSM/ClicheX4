"""새 발사팔의 강체 정합 후보. 원8열 총구 창과 새 몸체를 각각 보호한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
TRANS={222:(1,-2),224:(0,-2),226:(1,-1),228:(1,-1),230:(1,0)}
POLY_A=[(-26,-12),(-15,-12),(-15,-9),(-4,-9),(-2,-8),(1,-6),(1,-5),(-4,-5),(-4,-6),(-15,-6),(-15,-4),(-20,-4),(-24,-6)]
POLY_C=[(-26,-11),(-15,-11),(-15,-8),(-4,-8),(-2,-7),(1,-6),(1,-4),(-4,-4),(-4,-5),(-15,-5),(-15,-3),(-20,-3),(-24,-6)]
POLY_B=[(-25,-13),(-14,-13),(-14,-10),(-3,-10),(-1,-9),(1,-7),(1,-5),(-4,-5),(-4,-7),(-15,-7),(-15,-5),(-20,-5),(-24,-8)]
def poly(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,dtype=bool)
def box(b):return(X>=b[0])&(Y>=b[1])&(X<b[2])&(Y<b[3])
def main():
 out=D/'shot_joint_probe_v2';out.mkdir(exist_ok=False);p=N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.float32);rows=[];proof=[]
 for n,(dx,dy)in TRANS.items():
  page='a'if n<230 else'b';meta=json.loads((D/f'shot_{page}_registered_v1/manifest.json').read_text('utf8'));q=next(v for v in meta['frames']if v['ref']==n);imeta=json.loads((D/f'shot_{page}_inputs_v1/manifest.json').read_text('utf8'));iq=next(v for v in imeta['frames']if v['ref']==n);bpath=D/f'canonical_cases_probe_v4/body_{n-1:03}_indices.png';base=np.array(Image.open(bpath));raw=np.array(Image.open(D/f'shot_{page}_registered_v1/body_{n:03}_indices.png'));donor=raw.copy();points=POLY_A if n in(222,224)else POLY_C if n in(226,228)else POLY_B;mask=poly(points);cell=Image.open(ROOT/meta['source_art']).convert('RGBA').crop(q['crop']);ar=np.array(cell);alpha=ar[:,:,3].astype(np.float32)/255;rgb=ar[:,:,:3].astype(np.float32);resize=lambda v:np.array(Image.fromarray(v.astype(np.float32),'F').resize((96,96),Image.Resampling.BOX));mass=resize(alpha);means=np.stack([resize(rgb[:,:,k]*alpha)/np.maximum(mass,.001)for k in range(3)],2);skin=[]
  for y,x in np.argwhere(mask&box([-14,-12,-4,-4])&np.isin(donor,[5,6,7,8,9])):
   xx,yy=int(x-160),int(y-160);mean=means[yy+48,xx+48];allowed=np.array([1,2,3,4,10,11,12,13]);value=int(allowed[((pal[allowed]-mean)**2).sum(1).argmin()]);skin.append({'source_world':[xx,yy],'old':int(donor[y,x]),'new':value,'source_alpha_weighted_rgb':mean.tolist()});donor[y,x]=value
  piece=np.where(mask,donor,0);moved=np.roll(np.roll(piece,dy,0),dx,1);z=base.copy();remove=box([-16,-7,-4,2]);z[remove]=0;head=(X>=-8)&(Y<=-10);opposite=(X>=1)&(Y<=-7);protected=head|opposite;use=(moved>0)&~protected;z[use]=moved[use];w=iq['old_gun_window'];guard=box(w);old=a.layer(n)[0];z[guard]=old[guard];need(np.array_equal(z[head],base[head]),'새 머리 보존');need(np.array_equal(z[Y>=3],base[Y>=3]),'새 하체 보존');need(np.array_equal(z[guard],old[guard]),'원8열 총구 창 보존');labs,ct=label(z>0,np.ones((3,3)));components=[{'size':int((labs==i).sum()),'cells':[[int(x-160),int(y-160),int(z[y,x])]for y,x in np.argwhere(labs==i)]if(labs==i).sum()<25 else None}for i in range(1,ct+1)]
  for tag,v in [('body',z),('raw_donor',raw),('source_arm',piece),('placed_arm',moved),('removed_held',np.where(remove,base,0))]:Image.fromarray(v).save(out/f'{tag}_{n:03}_indices.png')
  proof.append({'ref':n,'body_source':bpath.relative_to(ROOT).as_posix(),'body_source_sha256':digest(bpath),'donor_source':(D/f'shot_{page}_registered_v1/body_{n:03}_indices.png').relative_to(ROOT).as_posix(),'source_polygon':points,'source_translation':[dx,dy],'skin_source_requantization':skin,'removed_held_window':[-16,-7,-4,2],'original_barrel_window':w,'original_barrel_exact':True,'original_window_scope':'현재 고정8열 총구/그립 창에는 기존 손끝도 일부 포함된다. 전부 무기만이라고 부르지 않는다.','preserved_new_head':True,'preserved_new_lower_body':True,'components8':components,'target_sha256':sha(z.tobytes()),'adopted':False});rows.append((str(n),[('new body',a.rgba(base)),('raw arm donor',a.rgba(raw)),('fixed muzzle / joint candidate',a.rgba(z)),('old shot',a.composite(n,15)[0])]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'manifest.json',{'parent_arc_sha256':digest(p),'frames':proof,'native_packed':False,'runtime_verified':False,'scope':'총구/새 어깨 접점 진단, 미술 검토 전. 새 팔 원화+원8열 모듈만이며 구형 전신 복원 없음.'});print(json.dumps([{'ref':q['ref'],'components':q['components8'],'source_skin_cells':len(q['skin_source_requantization'])}for q in proof]))
if __name__=='__main__':main()
