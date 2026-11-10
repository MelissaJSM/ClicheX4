"""새95/98의 머리·사지 공통과 의상/맨팔 의미영역을 분리한다."""
from pathlib import Path
import sys,json,importlib.util,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,helper,sha,digest
s=importlib.util.spec_from_file_location('special_source_semantics',N/'ultimate_standing_repaint/prepare_common.py');sm=importlib.util.module_from_spec(s);s.loader.exec_module(sm)
Y,X=np.indices((384,384));Y-=160;X-=160
POLYS={95:[(-11,-14),(-7,-14),(-5,-14),(0,-14),(2,-12),(5,-10),(9,-6),(13,-5),(17,-4),(17,1),(11,1),(7,-2),(5,0),(4,2),(2,3),(-3,4),(-8,3),(-8,0),(-6,-4),(-9,-6),(-12,-5),(-15,-6),(-15,-10)],98:[(-24,-7),(-18,-7),(-14,-6),(-11,-4),(-7,-4),(-6,-5),(-3,-4),(0,-4),(2,-3),(5,-2),(8,-2),(12,-2),(16,-3),(16,-7),(22,-7),(22,-2),(18,1),(15,1),(10,1),(6,1),(4,2),(4,6),(2,8),(-3,8),(-8,7),(-9,3),(-7,0),(-10,0),(-13,0),(-17,-1),(-22,-2)]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--version',choices=['v1','v2'],default='v2');args=ap.parse_args();m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());out=D/f'common_probe_{args.version}';out.mkdir(exist_ok=False);rows=[];proof=[]
 for n in(95,98):
  folder='contacts_probe_v1'if n==95 else'hand98_local_probe_v1';bp=D/f'{folder}/before_{n:03}_indices.png';ap=D/f'{folder}/after_{n:03}_indices.png';b=np.array(Image.open(bp));donor=np.array(Image.open(ap));v=b.copy();mapping=[]
  if n==95:
   cell=Image.open(D/'a_v1/generated.png').convert('RGBA').crop((0,0,627,627));pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.float32)
   for y,x in np.argwhere(b==15):
    sx,sy=int(x-160),int(y-160)+1;value,votes=sm.source_vote(cell,pal,(sx,sy),{15});v[y,x]=value;mapping.append({'world':[int(x-160),int(y-160)],'source_world':[sx,sy],'source':'a_v1 before95 head Y−1','index':value,'votes':votes})
  else:assert not np.any(b==15)
  costume=sm.poly(POLYS[n]);boundary=[];common_hand=[]
  if args.version=='v2':
   pts=[(2,-14),(3,-14),(4,-14),(5,-14),(6,-14),(3,-13),(4,-13),(5,-13),(6,-13),(3,-12),(4,-12),(5,-12),(6,-12),(7,-12),(5,-11),(6,-11),(7,-11),(6,-10),(7,-10),(8,-10),(7,-9),(8,-9),(9,-9),(8,-8),(9,-8),(10,-8),(9,-7),(10,-7),(11,-7),(10,-6),(11,-6),(15,-5),(-8,-4),(-9,-3),(-8,-3)]if n==95 else[(3,-3),(4,-3),(15,-3),(-15,0),(-14,0),(-15,1),(-14,1),(-13,1),(-12,1),(-10,1),(-13,2),(-12,2),(-11,2),(-10,2),(16,2),(-13,3),(-12,3),(-11,3)]
   for x,y in pts:boundary.append({'world':[x,y],'before_index':int(b[y+160,x+160]),'source_after_index':int(donor[y+160,x+160]),'meaning':'새 맨팔의 바깥 피부선·소매 아래 실제투명 틈. 머리 전체 색치환 없음.'});costume[y+160,x+160]=True
   if n==95:
    x,y=15,-3;assert b[y+160,x+160]==0 and donor[y+160,x+160]==3;b[y+160,x+160]=donor[y+160,x+160];v[y+160,x+160]=donor[y+160,x+160];common_hand.append({'world':[x,y],'source_after_index':3,'meaning':'새 후폼 자유손의 실제 어두운 끝 외곽1셀을 전폼공통화. 임의확장/보간없음.'})
  v[costume]=donor[costume]
  if n==95:
   shared=(X<=-13)&(X>=-21)&(Y>=-8)&(Y<=1);policy='95 새사선권총의 실제바깥 총열/그립만공유, 커프와맨팔은각원화. 정본회전주장없음.'
  else:
   c=a.layer(85)[0];gm=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(c,range(1,10));case=np.roll(np.roll(np.where(gm,c,0),-3,1),1,0);skin=(X>=-23)&(X<=-17)&(Y>=-7)&(Y<=-2)&np.isin(b,(10,11,12,13));shared=(case>0)|skin;policy='98 정본85 X−3,Y+1과 새손 피부만공유. 새98 손원화4576b0c9, 가림2/18texel가시.'
  v[shared]=b[shared];outside=(v>0)&(b==0);comps=[]
  for tag,z in(('before',b),('after',v),('donor',donor),('costume_mask',costume.astype(np.uint8)*255),('shared_mask',shared.astype(np.uint8)*255),('outside',outside.astype(np.uint8)*255)):Image.fromarray(z).save(out/f'{tag}_{n:03}_indices.png')
  for z in(b,v):
   lab,ct=label(z>0,np.ones((3,3)));comps.append(np.bincount(lab.flat)[1:].tolist())
  proof.append({'ref':n,'before_source':bp.relative_to(ROOT).as_posix(),'before_source_sha256':digest(bp),'after_donor':ap.relative_to(ROOT).as_posix(),'after_donor_sha256':digest(ap),'costume_polygon':POLYS[n],'source_boundary_links':boundary,'shared_hand_outline_links':common_hand,'palette15_source':mapping,'shared_policy':policy,'shared_source_cells':[[int(x-160),int(y-160),int(b[y,x])]for y,x in np.argwhere(shared)],'outside_before':[[int(x-160),int(y-160),int(v[y,x])]for y,x in np.argwhere(outside)],'component_sizes':comps,'alpha_clipped':False,'old_body_copied':False});rows.append((str(n),[('jacket',a.rgba(b,16)),('bare donor',a.rgba(donor)),('common candidate',a.rgba(v)),('idle',a.composite(0)[0])]))
 helper.grid(rows,out/'comparison.png',7);write(out/'manifest.json',{'parent_sha256':m['parent_arc_sha256'],'frames':proof,'native_packed':False,'runtime_verified':False,'scope':'새95/98의 초기공통층. 미술/의상경계 검토 전이며 최종 아님.'});print(json.dumps([{'ref':q['ref'],'outside':q['outside_before'],'components':q['component_sizes']}for q in proof]))
if __name__=='__main__':main()
