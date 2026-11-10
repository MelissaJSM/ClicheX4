"""새89/97의 원화 홍채/의상 의미영역만 등록하고 공통 몸을 비교한다."""
from pathlib import Path
import sys,json,importlib.util,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
POLYS={89:[(-17,-23),(-12,-23),(-11,-18),(-8,-12),(-6,-10),(2,-10),(4,-8),(6,-6),(7,0),(9,5),(6,7),(3,5),(1,7),(-4,7),(-8,8),(-10,6),(-8,1),(-7,-5),(-10,-8),(-12,-11),(-14,-15),(-16,-19)],97:[(-13,-11),(-9,-12),(-8,-9),(-6,-8),(-2,-8),(3,-8),(5,-6),(7,-3),(8,1),(7,5),(4,6),(1,7),(-4,7),(-8,7),(-9,3),(-8,0),(-12,-1),(-14,-4),(-14,-7)]}
def poly(points):
 z=Image.new('L',(384,384));ImageDraw.Draw(z).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(z)>0
def source_vote(cell,pal,world,excluded):
 ar=np.array(cell);rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(np.float32)/255;avail=np.array([v for v in range(1,16)if v not in excluded]);labs=np.zeros(ar.shape[:2],np.uint8)
 for y in range(len(labs)):labs[y]=avail[((rgb[y,:,None]-pal[None,avail])**2).sum(2).argmin(1)]
 votes=np.stack([np.array(Image.fromarray(np.where(labs==v,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for v in avail]);x,y=world;x+=48;y+=48
 return int(avail[votes[:,y,x].argmax()]),{str(int(v)):float(votes[j,y,x])for j,v in enumerate(avail)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--version',default='v1',choices=['v1','v2','v3']);args=ap.parse_args()
 meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/meta['parent_arc'];need(digest(p)==meta['parent_arc_sha256'],'부모');a=Archive(p.read_bytes());im=Image.open(D/'a_v1/generated.png').convert('RGBA');need(im.size==(1254,1254),'전체고정캔버스')
 out=D/f'common_probe_{args.version}';out.mkdir(exist_ok=False);rows=[];records=[]
 polygons=dict(POLYS)
 if args.version in('v2','v3'):polygons[97]=[(-13,-11),(-9,-12),(-8,-9),(-6,-8),(-2,-8),(3,-8),(5,-6),(7,-3),(8,1),(7,5),(4,6),(1,7),(-4,7),(-8,7),(-10,4),(-13,3),(-15,1),(-15,-4),(-14,-7)]
 for n,points in polygons.items():
  corrected={};eyeproof=[];col=0 if n==89 else 1;world=(-4,-13 if n==89 else -12)
  for row,(form,start)in enumerate((('before',16),('after',0))):
   z=np.array(Image.open(D/'first_registered_v1'/f'{form}_{n:03}_indices.png'));need(z[world[1]+160,world[0]+160]==14,'추가홍채셀');need(z[world[1]+161,world[0]+160]==14,'원위치홍채셀')
   cell=im.crop((col*627,row*627,(col+1)*627,(row+1)*627));pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
   v,votes=source_vote(cell,pal,world,{14,15});need(v in(1,2),'실제짙은눈윗경계');z[world[1]+160,world[0]+160]=v;corrected[form]=z;eyeproof.append({'form':form,'world':world,'old_index':14,'source_vote':v,'votes':votes,'rule':'원래 한셀홍채 위치는 아래셀에 유지. 추가위셀은 같은새원화의 비홍채 표본으로 재양자화.'})
  b=corrected['before'];donor=corrected['after'];common=b.copy();mapping=[]
  # Palette15 means neutral gray before, cyan after. Re-read the same authored
  # face sample under after's actual palette instead of copying a cyan mark.
  cell=im.crop((col*627,0,(col+1)*627,627));pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
  for y,x in np.argwhere(b==15):
   v,votes=source_vote(cell,pal,(int(x-160),int(y-160)),{15});common[y,x]=v;mapping.append({'world':[int(x-160),int(y-160)],'old_index':15,'after_index':v,'votes':votes,'source':'새before의 동일 얼굴 표본, after 실제 팔레트'})
  m=poly(points);boundary=[]
  if args.version=='v3' and n==89:
   for x,y in [(-10,-20),(-10,-19),(-10,-18),(-9,-18),(-10,-17),(-9,-17),(-9,-16),(-9,-15)]:
    boundary.append({'world':[x,y],'before_index':int(b[y+160,x+160]),'source_after_index':int(donor[y+160,x+160]),'meaning':'새 맨팔 손목 오른쪽의 투명 틈/귀·머리 경계. 옛 재킷 커프가 공통머리 보호에 포함된 부분만 실제 후폼 원화로 등록.'});m[y+160,x+160]=True
  after=common.copy();after[m]=donor[m];shared=np.zeros_like(m)
  if args.version in('v2','v3') and n==97:
   shared=poly([(-14,-14),(-9,-14),(-8,-10),(-7,-8),(-8,-5),(-10,-5),(-12,-8)])
   after[shared]=common[shared]
  if args.version=='v3' and n==89:
   shared=poly([(-19,-30),(-11,-30),(-11,-21),(-19,-21)]);after[shared]=common[shared]
  outside=(after>0)&(b==0);need(np.array_equal(after[~m],common[~m]),'공통영역')
  for tag,z in(('before',b),('after',after),('donor',donor),('costume_mask',m.astype(np.uint8)*255),('outside',outside.astype(np.uint8)*255)):Image.fromarray(z).save(out/f'{tag}_{n:03}_indices.png')
  Image.fromarray(shared.astype(np.uint8)*255).save(out/f'shared_hand_mask_{n:03}.png')
  records.append({'ref':n,'costume_polygon':points,'source_boundary_links':boundary,'eye_registration':eyeproof,'palette15_face_semantic':mapping,'shared_hand_policy':'새before 권총/손 의미창만 공통화. 회전한 정본85로 대체한 것이 아니라 생성된 비사격 사선 권총이다.','shared_hand_polygon':[(-19,-30),(-11,-30),(-11,-21),(-19,-21)]if n==89 and args.version=='v3'else[(-14,-14),(-9,-14),(-8,-10),(-7,-8),(-8,-5),(-10,-5),(-12,-8)]if n==97 and args.version in('v2','v3')else[],'before_sha256':sha(b.tobytes()),'after_sha256':sha(after.tobytes()),'outside_before':[[int(x-160),int(y-160),int(after[y,x])]for y,x in np.argwhere(outside)],'components_before':int(label(b>0,np.ones((3,3)))[1]),'components_after':int(label(after>0,np.ones((3,3)))[1]),'alpha_clipped':False,'old_body_copied':False,'new_source_shared_cells':int((after!=donor).sum())})
  rows.append((f'common {n}',[('jacket',a.rgba(b,16)),('after donor',a.rgba(donor)),('common candidate',a.rgba(after)),('after idle',a.composite(0)[0])]))
 helper.grid(rows,out/'comparison.png',7)
 write(out/'manifest.json',{'parent_arc_sha256':digest(p),'source_art_sha256':digest(D/'a_v1/generated.png'),'frames':records,'scope':'새홍채한셀/팔레트15 의미 표본과새의상polygon의 공통층전 후보. 머리/손발/총/양폼실루엣 세부열람전,후폼허리회색범위는별도검토.','native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'outside':q['outside_before'],'components':[q['components_before'],q['components_after']]}for q in records]))
if __name__=='__main__':main()
