"""새 맨팔/의상 donor만 선택하고 이미 수용된 새 머리·손발·총을 보호."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
POLYS={
1:[(-2,-7),(2,-8),(5,-7),(7,-6),(10,-3),(11,0),(11,4),(8,5),(8,7),(0,7),(-4,4),(-4,2),(-7,2),(-7,-1),(-3,-2),(-3,-5)],
7:[(-6,-6),(-2,-7),(4,-6),(7,-4),(10,-1),(10,3),(5,5),(4,6),(-2,6),(-6,5),(-8,3),(-11,1),(-11,-2),(-7,-2)],
15:[(-4,-8),(0,-9),(3,-9),(6,-7),(8,-5),(10,-2),(10,2),(8,3),(8,5),(1,5),(-4,3),(-6,1),(-10,0),(-10,-3),(-6,-4)],
25:[(-4,-6),(-1,-7),(5,-6),(8,-3),(10,0),(10,3),(7,5),(7,8),(0,8),(-4,5),(-6,3),(-8,2),(-8,-1),(-5,-2)]}
FAR={1:(4,2,10,5),7:(5,-1,10,3),15:(6,-1,10,3),25:(5,2,9,5)}
LEG={1:6,7:6,15:5,25:8}
SHOULDER_BOUNDARY={15:[(8,-6,8,12),(9,-5,5,10)],25:[(0,-7,9,12),(1,-7,8,12),(2,-7,8,12)]}

def box_skin(b,q):
 x0,y0,x1,y1=q;return np.isin(b,(10,11,12))&(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
def main():
 p=argparse.ArgumentParser();p.add_argument('--version',default='v2');p.add_argument('--page',choices=list('abcd'),default='a');p.add_argument('--regions');args=p.parse_args();need(args.version.isalnum(),'Version');page=args.page
 src=D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC';need(digest(src)=='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0','Parent');a=Archive(src.read_bytes());out=D/f'after_{page}_costume_probe_{args.version}';out.mkdir(exist_ok=False);records=[];rows=[]
 groups={'a':'first_contacts_probe_v1','b':'second_contacts_probe_v2','c':'third_contacts_probe_v2','d':'fourth_contacts_probe_v1'};group=groups[page];contact=json.loads((D/group/'registration.json').read_text('utf8'));meta={q['ref']:q for q in contact['frames']};canonical=contact['canonical_ref85_texels'];poses={q['ref']:q for q in json.loads((D/f'after_inputs_v1/{page}_poses.json').read_text('utf8'))}
 polys,fars,legs,boundary=POLYS,FAR,LEG,SHOULDER_BOUNDARY
 if args.regions:
  cfg=json.loads((D/args.regions).read_text('utf8'));need(cfg['page']==page,'Config page');polys={int(k):v['polygon']for k,v in cfg['frames'].items()};fars={int(k):v['far_hand_box']for k,v in cfg['frames'].items()};legs={int(k):v['leg_from_y']for k,v in cfg['frames'].items()};boundary={int(k):v.get('boundary',[])for k,v in cfg['frames'].items()}
 pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words]);mapped=int(np.argmin(((pal[:16].astype(float)-pal[31])**2).sum(axis=1)));need(mapped==13,'Palette31 gray maps13')
 for n,poly in polys.items():
  bp=ROOT/poses[n]['source'];need(digest(bp)==poses[n]['source_sha256'],'Current before body');ap=D/f'after_{page}_registered_v1/after_{n:03}.png';b=np.array(Image.open(bp));donor=np.array(Image.open(ap));case=np.zeros_like(b);hx,hy=meta[n]['actual_grip_skin']
  for x,y,v in canonical:case[160+y+hy+9,160+x+hx+16]=v
  need(np.array_equal(b[case>0],case[case>0]),'Canonical20 gun')
  mi=Image.new('L',(384,384));ImageDraw.Draw(mi).polygon([(x+160,y+160)for x,y in poly],fill=255);mask=np.array(mi)>0
  for x,y,bv,av in boundary.get(n,[]):
   need(int(b[y+160,x+160])==bv and int(donor[y+160,x+160])==av,'Authored shoulder edge provenance');mask[y+160,x+160]=True
  protected=(case>0)|box_skin(b,meta[n]['hand_box'])|box_skin(b,fars[n])|((Y>=legs[n])&np.isin(b,(10,11,12,14)))
  expected=b.copy();expected[b==15]=mapped;t=expected.copy();t[mask]=donor[mask];t[protected]=expected[protected];added=(t>0)&(b==0);t[added]=0
  need(np.array_equal(t[~mask],expected[~mask]),'Outside clothing');need(np.array_equal(t[case>0],case[case>0]),'Gun');need(np.array_equal(t[protected],expected[protected]),'Hands/leg skin');need(int(label(t>0,np.ones((3,3)))[1])==int(label(b>0,np.ones((3,3)))[1]),'New detached part')
  for name,ar in [('before',b),('after',t),('mask',mask.astype(np.uint8)*255),('protected',protected.astype(np.uint8)*255),('case',case)]:Image.fromarray(ar).save(out/f'{name}_{n:03}.png')
  records.append({'ref':n,'before_path':bp.relative_to(ROOT).as_posix(),'before_sha256':digest(bp),'donor_path':ap.relative_to(ROOT).as_posix(),'donor_sha256':digest(ap),'polygon':poly,'shoulder_boundary_from_donor':boundary.get(n,[]),'near_hand_box':meta[n]['hand_box'],'far_hand_box':fars[n],'leg_skin_from_y':legs[n],'palette15_mapping':mapped,'canonical_gun_texels':int((case>0).sum()),'outside_mask_exact_except_palette15':True,'protected_hands_legs_gun_exact':True,'donor_alpha_outside_before_envelope_excluded':int(added.sum()),'changed':int((t!=b).sum()),'native_sha256':sha(t.tobytes())});rows.append((f'costume run {n}',[('after idle',a.composite(0,0)[0]),('fixed new before',a.rgba(b,16)),('after donor',a.rgba(donor)),('local costume/common body',a.rgba(t))]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'registration.json',{'parent_sha256':digest(src),'frames':records,'source_policy':'옛 몸체를 복사하지 않고 새 전폼·새 의상 원화만 사용. 의상 다각형 밖 머리/귀/얼굴/사지/총과 새 손을 보호. 경계는 후속 실제확대검토 대상.','native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
