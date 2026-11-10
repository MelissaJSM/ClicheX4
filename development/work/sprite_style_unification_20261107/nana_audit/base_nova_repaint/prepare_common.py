"""새 준비두자세의 손/얼굴·같은행 하체 표본과 부분 의상 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
def box(x0,y0,x1,y1):return (X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
def spans(row):
 xs=np.flatnonzero(row);return [] if not len(xs) else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def comp(a,ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/meta['parent_arc'];need(digest(p)==meta['parent_sha256'],'부모')
 a=Archive(p.read_bytes());out=D/'common_layers_probe_v1';out.mkdir(exist_ok=False);frames=[];compare=[];partial=[]
 for n in(213,215):
  bs=D/f'a_registered_v1/base_{n:03}_indices.png';fs=D/f'a_registered_v1/fourth_{n:03}_indices.png'
  b=np.array(Image.open(bs));f=np.array(Image.open(fs));b0=b.copy();f0=f.copy();moves=[]
  if n==213:
   m=box(-3,10,11,20)&(b>0);cut=np.where(m,b,0).astype(np.uint8);b[m]=0;shift=np.roll(cut,-1,axis=0);b[shift>0]=shift[shift>0]
   moves.append({'meaning':'새 기본213 하단 부츠/발목 국소 원높이 정합','source_box':[-3,10,11,20],'translation':[0,-1],'source_pixels':int(m.sum()),'source_sha256':sha(cut.tobytes()),'old_floor_exclusive':19,'new_floor_exclusive':int(np.nonzero(b)[0].max()-159)})
  shared_boxes=([[-6,-14,-2,-9],[-12,-7,-6,-1],[5,-2,11,4]] if n==213 else [[-2,-14,1,-9],[-11,-23,-5,-16],[6,-1,12,5]])
  shared=np.zeros(b.shape,bool)
  for bounds in shared_boxes:shared|=box(*bounds)
  f[shared]=b[shared]
  before_leg=f.copy();links=[];rejected=[];region=(Y>=7)&(Y<=22)&(X<18)
  for y in range(167,183):
   gaps=spans((b[y]>0)&(f[y]==0)&region[y]);runs=spans((before_leg[y]>0)&region[y]);groups={}
   for gap in gaps:
    need(bool(runs),'같은행 하체 원표본 없음');sr=min(runs,key=lambda q:np.min(np.abs(q[:,None]-gap)));groups.setdefault((int(sr[0]),int(sr[-1])),[]).append(gap)
   for(l,r),gs in groups.items():
    lo=min(l,*(int(q[0])for q in gs));hi=max(r,*(int(q[-1])for q in gs));dest=np.arange(lo,hi+1)
    if max(l-lo,hi-r)>2 or len(dest)>max(3,2*(r-l+1)):
     rejected.append({'world_y':y-160,'source':[l-160,r-160],'requested':[lo-160,hi-160]});continue
    sx=np.arange(l,r+1)[np.rint(np.linspace(0,r-l,len(dest))).astype(int)];f[y,dest]=before_leg[y,sx]
    links.extend({'destination':[int(x-160),y-160],'source':[int(xx-160),y-160],'index':int(before_leg[y,xx])}for x,xx in zip(dest,sx)if x!=xx)
  full=np.where(f,f,b).astype(np.uint8);owner=np.full(b.shape,6,np.uint8)
  # 의상 의미 소유: 얼굴/모자5, 몸6, 두팔7, 치마·하체와큰뒤베일8.
  owner[(Y<-7)&(X>=(-7 if n==213 else -3))]=5
  owner[(Y>=3)|((X>=10)&(Y>=-10))]=8
  if n==213:
   owner[box(-13,-8,-4,2)]=7;owner[box(5,-4,12,4)]=7
  else:
   owner[box(-12,-24,-3,-11)]=7;owner[box(6,-3,13,5)]=7
  for bounds in shared_boxes[:1]:owner[box(*bounds)]=5
  pc=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full]
  diff=((full!=b)|((f>0)&pc))&(full>0)
  ls={0:b,**{pb:np.where(diff&(owner==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
  expected=a.rgba(b);expected.alpha_composite(a.rgba(f,16));need(expected.tobytes()==comp(a,ls,15,1).tobytes(),'전체5층 재구성')
  checks=[]
  for mask in range(16):
   for arm in(1,2):
    im=comp(a,ls,mask,arm);labs,c=label(np.array(im)[:,:,3]>0,np.ones((3,3)));sizes=np.bincount(labs.flat)[1:]
    checks.append({'mask':mask,'arm':arm,'components8':c,'sizes':sorted([int(v)for v in sizes],reverse=True),'rgba_sha256':sha(im.tobytes())})
  for name,z in(('base',b),('fourth',f),('full',full),('owner',owner),('shared_mask',shared.astype(np.uint8)*255)):
   Image.fromarray(z).save(out/f'{name}_{n:03}_indices.png')
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  frames.append({'ref':n,'base_source':bs.relative_to(ROOT).as_posix(),'base_source_sha256':digest(bs),'fourth_source':fs.relative_to(ROOT).as_posix(),'fourth_source_sha256':digest(fs),'rigid_moves':moves,'shared_boxes':shared_boxes,'same_scanline_fourth_links':links,'rejected_scanlines':rejected,'remaining_lower_base_outside_fourth':int(((b>0)&(f==0)&region).sum()),'all_base_outside_fourth':[[int(x-160),int(y-160),int(b[y,x])]for y,x in np.argwhere((b>0)&(f==0))],'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'partial_checks':checks})
  compare.append((str(n),[('base raw',a.rgba(b0)),('base contact',a.rgba(b)),('Fourth raw',a.rgba(f0,16)),('common source',a.rgba(f,16)),('native union',comp(a,ls,15))]))
  partial.append((str(n),[(str(mask),comp(a,ls,mask))for mask in(1,2,4,8,10)]))
 helper.grid(compare,out/'comparison.png',7);helper.grid(partial,out/'partial.png',7)
 write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_sha256':digest(p),'frames':frames,'scope':'새2몸체×2의상의 공통손/얼굴 및 원하체 같은행 표본 정합 후보.옛그림복사·신규색도장 없음.214효과·216파생·패킹 전이며 부분소유와남은가시구형의상같은오인가능성은시각검토대상.','native_packed':False,'runtime_verified':False})
 print(json.dumps([{'ref':q['ref'],'lower_gaps':q['remaining_lower_base_outside_fourth'],'all_gaps':len(q['all_base_outside_fourth']),'links':len(q['same_scanline_fourth_links']),'rejected':q['rejected_scanlines'],'isolated':[x for x in q['partial_checks']if x['components8']>1]}for q in frames]))
if __name__=='__main__':main()
