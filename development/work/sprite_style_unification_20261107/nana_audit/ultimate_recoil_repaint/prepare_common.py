"""새90/91의 실제 맨팔 의상과 고정 권총을 공통 몸체에 정합한다."""
from pathlib import Path
import sys,json,importlib.util,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
sp=importlib.util.spec_from_file_location('standing_semantics',N/'ultimate_standing_repaint/prepare_common.py');sm=importlib.util.module_from_spec(sp);sp.loader.exec_module(sm)
Y,X=np.indices((384,384));Y-=160;X-=160
POLYS={90:[(-16,-11),(-11,-11),(-11,-9),(-7,-8),(-6,-7),(-3,-7),(-1,-8),(3,-7),(5,-5),(7,-1),(8,2),(6,4),(2,5),(2,7),(-2,9),(-6,7),(-9,6),(-8,3),(-6,1),(-6,-2),(-10,-2),(-13,-4),(-15,-7)],91:[(-20,-8),(-15,-8),(-13,-8),(-10,-9),(-5,-8),(-1,-8),(3,-7),(5,-4),(7,-1),(8,2),(6,4),(2,5),(1,8),(-3,9),(-7,7),(-9,5),(-8,2),(-6,-1),(-6,-3),(-11,-2),(-14,-3),(-16,-5),(-20,-5)]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--version',choices=['v1','v2'],default='v2');args=ap.parse_args()
 m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/m['parent_arc'];need(digest(p)==m['parent_arc_sha256'],'고정부모');a=Archive(p.read_bytes());art=D/'a_v1/generated.png';need(digest(art)=='c78d7de88c8b807535d2612e4d9ca8c5ab7e3d89ff20153c7ea4f7ba1733f242','새4원화');im=Image.open(art).convert('RGBA');out=D/f'common_probe_{args.version}';out.mkdir(exist_ok=False);rows=[];proof=[]
 canonical=a.layer(85)[0];gunmask=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(canonical,range(1,10));gun=np.where(gunmask,canonical,0).astype(np.uint8);need(int((gun>0).sum())==20,'정본85권총20');case=np.roll(gun,-2,1)
 for col,n in enumerate((90,91)):
  corrected={};eyes=[]
  for row,(form,start)in enumerate((('before',16),('after',0))):
   z=np.array(Image.open(D/f'first_registered_v1/{form}_{n:03}_indices.png'));pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32);cell=im.crop((col*627,row*627,(col+1)*627,(row+1)*627))
   if n==90:
    x,y=-4,-12;need(z[y+160,x+160]==14 and z[y+161,x+160]==14,'추가위홍채');v,votes=sm.source_vote(cell,pal,(x,y),{14,15});need(v in(1,2),'새눈윗경계');z[y+160,x+160]=v;eyes.append({'form':form,'world':[x,y],'value':v,'votes':votes})
   corrected[form]=z
  b=corrected['before'];donor=corrected['after'];v=b.copy();pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);cell=im.crop((col*627,0,(col+1)*627,627));face=[]
  for y,x in np.argwhere(b==15):
   val,votes=sm.source_vote(cell,pal,(int(x-160),int(y-160)),{15});v[y,x]=val;face.append({'world':[int(x-160),int(y-160)],'value':val,'votes':votes})
  mask=sm.poly(POLYS[n]);boundary=[]
  if args.version=='v2':
   pts=[(-7,-1),(-8,0),(-7,0),(-9,1),(-8,1),(-7,1),(-8,2),(-9,3)]if n==90 else[(-18,-4),(-17,-4),(-16,-4),(-13,-2),(-12,-2),(-10,-2),(-9,-2),(-8,-2),(-7,-2),(-7,-1),(-8,1)]
   for x,y in pts:boundary.append({'world':[x,y],'before_index':int(b[y+160,x+160]),'source_after_index':int(donor[y+160,x+160]),'meaning':'새 후폼 원화의 맨팔/허리 경계와 실제 투명 틈. 공통몸에 남은 재킷 커프·밑단만 의미분리.'});mask[y+160,x+160]=True
  v[mask]=donor[mask];weapon={}
  if n==90:
   share=sm.poly([(-20,-20),(-11,-20),(-11,-10),(-20,-10)]);v[share]=b[share];weapon={'mode':'새before 사선권총/손 원화 공통','polygon':[(-20,-20),(-11,-20),(-11,-10),(-20,-10)]}
  else:
   records=[]
   for form,z in(('before',b),('after',v)):
    original=z.copy();skin=(X>=-22)&(X<=-17)&(Y>=-9)&(Y<=-6)&np.isin(z,(10,11,12,13));rm=(X>=-25)&(X<=-17)&(Y>=-13)&(Y<=-7)&((Y<=-10)|(X<=-20))&np.isin(z,range(1,10));z[rm]=0;vis=(case>0)&~skin;z[vis]=case[vis];z[skin]=original[skin];records.append({'form':form,'removed_source_cells':[[int(x-160),int(y-160),int(original[y,x])]for y,x in np.argwhere(rm)],'preserved_skin_cells':[[int(x-160),int(y-160),int(original[y,x])]for y,x in np.argwhere(skin)],'gun_skin_contact8':int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum())})
   share=(X>=-25)&(X<=-16)&(Y>=-13)&(Y<=-5)if args.version=='v1'else(case>0)|((X>=-22)&(X<=-17)&(Y>=-9)&(Y<=-6)&np.isin(b,(10,11,12,13)));v[share]=b[share];weapon={'mode':'정본85의20texel 사랑이 X−2,Y불변. 수용된 기본/포스91과 같은 모듈위치이며 실제발사좌표 검증은별도.','module_sha256':sha(gun.tobytes()),'translation':[-2,0],'registrations':records,'common_policy':'v2는정본총과실제피부손만공통. 검정커프를손으로복사하지않음.'if args.version=='v2'else'진단사각창','common_cells':[[int(x-160),int(y-160),int(b[y,x])]for y,x in np.argwhere(share)]}
  outside=(v>0)&(b==0);links=[[int(x-160),int(y-160),int(v[y,x])]for y,x in np.argwhere(outside)]
  for tag,z in(('before',b),('after',v),('donor',donor),('costume_mask',mask.astype(np.uint8)*255),('outside',outside.astype(np.uint8)*255)):Image.fromarray(z).save(out/f'{tag}_{n:03}_indices.png')
  proof.append({'ref':n,'costume_polygon':POLYS[n],'source_boundary_links':boundary,'eye_source':eyes,'face15_source':face,'weapon':weapon,'outside_before':links,'components':[int(label(z>0,np.ones((3,3)))[1])for z in(b,v)],'body_translation':[0,0],'old_body_copied':False,'alpha_clipped':False,'candidate_only':True})
  rows.append((str(n),[('new jacket',a.rgba(b,16)),('bare donor',a.rgba(donor)),('common candidate',a.rgba(v)),('idle',a.composite(0)[0])]))
 helper.grid(rows,out/'comparison.png',7);write(out/'manifest.json',{'parent_arc_sha256':digest(p),'source_art_sha256':digest(art),'frames':proof,'scope':'초기 공통몸체/권총 후보. 원화의 새로운 맨팔과 의상 의미영역만 선택하며 실루엣·접점 미검증, 패킹 전.','native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'outside':q['outside_before'],'components':q['components']}for q in proof]))
if __name__=='__main__':main()
