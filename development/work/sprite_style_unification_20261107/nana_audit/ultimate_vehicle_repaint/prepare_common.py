"""탑승 네자세의 새 머리·다리·손과 의상 의미영역 후보를 분리한다."""
from pathlib import Path
import sys,json,importlib.util,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,write,helper
s=importlib.util.spec_from_file_location('ride_semantic',N/'ultimate_standing_repaint/prepare_common.py');sm=importlib.util.module_from_spec(s);s.loader.exec_module(sm)
Y,X=np.indices((384,384));Y-=160;X-=160
POLYS={162:[(-13,-4),(-11,-6),(-9,-7),(-6,-7),(-3,-5),(-2,-4),(-1,-4),(0,-3),(3,-2),(3,2),(1,4),(-3,3),(-6,1),(-9,1),(-11,2),(-15,2),(-15,-1),(-14,-2)],166:[(-15,-2),(-12,-5),(-11,-8),(-8,-9),(-6,-8),(-3,-7),(-2,-4),(0,-3),(2,-1),(2,3),(1,5),(-4,5),(-6,3),(-9,2),(-12,4),(-15,3),(-16,1)],170:[(-14,-7),(-12,-9),(-11,-12),(-8,-12),(-6,-11),(-4,-10),(-1,-8),(1,-5),(2,-2),(1,0),(-2,1),(-6,0),(-9,-1),(-11,-3),(-15,-3),(-16,-5)],174:[(-10,-13),(-8,-15),(-5,-15),(-1,-13),(1,-10),(3,-8),(4,-4),(2,-2),(-2,-2),(-5,-4),(-9,-4),(-11,-6),(-13,-6),(-13,-10)]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--version',choices=['v1','v2'],default='v2');args=ap.parse_args();meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['parent_arc']).read_bytes());out=D/f'common_probe_{args.version}';out.mkdir(exist_ok=False);proof=[];rows=[]
 for n in(162,166,170,174):
  b=np.array(Image.open(D/f'contacts_probe_v1/before_{n:03}_indices.png'));donor=np.array(Image.open(D/f'contacts_probe_v1/after_{n:03}_indices.png'));v=b.copy();page='a'if n<170 else'b';col=0 if n in(162,170)else 1;cell=Image.open(D/f'{page}_v1/generated.png').convert('RGBA').crop((col*627,0,(col+1)*627,627));pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.float32);mapping=[]
  for y,x in np.argwhere(b==15):
   value,votes=sm.source_vote(cell,pal,(int(x-160),int(y-160)),{15});v[y,x]=value;mapping.append({'world':[int(x-160),int(y-160)],'index':value,'votes':votes})
  costume=sm.poly(POLYS[n]);boundary=[]
  if args.version=='v2':
   points={162:[(-14,-5),(-15,-4),(-14,-3)],166:[(-13,-6)],170:[(-5,-11),(2,-5),(-7,1),(-6,1),(-7,2),(-6,2),(-4,2)],174:[(-2,-14),(-1,-14),(0,-13),(1,-12),(3,-9),(4,-6),(-10,-2)]}[n]
   for x,y in points:
    costume[y+160,x+160]=True;boundary.append({'world':[x,y],'before_index':int(b[y+160,x+160]),'after_source_index':int(donor[y+160,x+160]),'meaning':'새목/어깨·소매끝 또는 허벅지 상단의 실제후폼 표본. 머리전체나 다리전체를 덮지 않음.'})
  v[costume]=donor[costume]
  if n==162:hand=(X<=-16)&(X>=-22)&(Y>=-1)&(Y<=2)
  elif n==166:hand=(X<=-16)&(X>=-22)&(Y>=1)&(Y<=5)
  elif n==170:hand=(X<=-15)&(X>=-20)&(Y>=-7)&(Y<=-4)
  else:hand=(X<=-11)&(X>=-17)&(Y>=-13)&(Y<=-6)
  v[hand]=b[hand];outside=(v>0)&(b==0)
  for name,z in(('before',b),('after',v),('donor',donor),('costume_mask',costume.astype(np.uint8)*255),('shared_hand_mask',hand.astype(np.uint8)*255),('outside',outside.astype(np.uint8)*255)):Image.fromarray(z).save(out/f'{name}_{n:03}_indices.png')
  proof.append({'ref':n,'polygon':POLYS[n],'palette15_source':mapping,'source_boundary_links':boundary,'shared_hand_cells':[[int(x-160),int(y-160),int(b[y,x])]for y,x in np.argwhere(hand)],'outside':[[int(x-160),int(y-160),int(v[y,x])]for y,x in np.argwhere(outside)],'components':[int(label(z>0,np.ones((3,3)))[1])for z in(b,v)],'alpha_clipped':False,'old_body_copied':False});rows.append((str(n),[('jacket',a.rgba(b,16)),('bare donor',a.rgba(donor)),('common candidate',a.rgba(v)),('idle',a.composite(0)[0])]))
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'parent_sha256':meta['parent_arc_sha256'],'frames':proof,'native_packed':False,'runtime_verified':False,'scope':'의상경계·팔꿈치/손목과 두다리 시각검토 전의 공통화 진단. 재킷 밖 맨팔을 삭제/클립하지 않는다.'});print(json.dumps([{'ref':q['ref'],'outside':q['outside'],'components':q['components']}for q in proof]))
if __name__=='__main__':main()
