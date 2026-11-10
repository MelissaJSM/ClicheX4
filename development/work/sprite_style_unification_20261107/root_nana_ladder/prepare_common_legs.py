"""Bounded same-row registration of new bare legs over new base boots."""
from pathlib import Path
import sys,json,hashlib,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
m=read(D/'first_inputs01/manifest.json');a=Archive((ROOT/m['source_arc']).read_bytes());assert sha(a.data)==m['source_arc_sha256']
Y,X=np.indices((384,384));Y-=160;X-=160
def spans(r):
 x=np.flatnonzero(r);return []if not len(x)else np.split(x,np.flatnonzero(np.diff(x)>1)+1)
data={143:(5,-8,12),144:(10,-8,8),146:(10,-7,5),149:(8,-7,8),151:(5,-7,7),153:(7,-7,6),154:(13,-3,20),183:(22,-5,7)}
ap=argparse.ArgumentParser();ap.add_argument('--v2',action='store_true');args=ap.parse_args()
out=D/('common_legs02'if args.v2 else'common_legs01');out.mkdir(exist_ok=False);records=[];rows=[]
for n,(lower,left,right)in data.items():
 b=np.array(Image.open(D/'contact_registration02'/f'base_{n:03}_indices.png'));f=np.array(Image.open(D/'contact_registration02'/f'fourth_{n:03}_indices.png'));original=f.copy();special=[]
 if args.v2 and n==143:
  # The bent-foot shoe ends one cell above the new basic foot. Register
  # the same new shoe's last 2 rows to 3 rows; do not synthesize its colors.
  patch=f[173:175,158:162].copy();f[173:176,158:162]=np.array(Image.fromarray(patch).resize((4,3),Image.Resampling.NEAREST));special=[{'source_box':[158,173,162,175],'dest_box':[158,173,162,176],'operation':'new shoe local registration 2 rows to 3'}]
 nf=f.copy();links=[];reject=[];region=(Y>=lower)&(X>=left)&(X<=right)
 for y in range(lower+160,200):
  bs=spans((b[y]>0)&region[y]&((f[y]==0)if args.v2 else True));fs=spans((f[y]>0)&region[y]);assigned={}
  for sb in bs:
   if np.all(f[y,sb]>0):continue
   if not fs:reject.append({'y':y-160,'base':list(map(int,sb-160)),'reason':'no authored Fourth span'});continue
   sf=min(fs,key=lambda s:float(np.min(np.abs(s[:,None]-sb))))
   key=(int(sf[0]),int(sf[-1]));assigned.setdefault(key,[]).append(sb)
  for (l,r),groups in assigned.items():
   sf=np.arange(l,r+1);lo=min(l,*(int(x[0])for x in groups));hi=max(r,*(int(x[-1])for x in groups));dst=np.arange(lo,hi+1)
   if max(l-lo,hi-r)>2 or len(dst)>max(3,len(sf)*2):reject.append({'y':y-160,'source':[l-160,r-160],'dest':[lo-160,hi-160],'reason':'over two-pixel edge / double width guard'});continue
   sample=sf[np.rint(np.linspace(0,len(sf)-1,len(dst))).astype(int)];nf[y,dst]=f[y,sample]
   links += [{'dest':[int(x-160),y-160],'source':[int(sx-160),y-160],'index':int(f[y,sx])}for x,sx in zip(dst,sample)]
 assert np.array_equal(nf[~region],f[~region])
 full=np.where(nf,nf,b).astype(np.uint8)
 for form,z in(('base',b),('fourth',nf)):Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png')
 issues=np.argwhere((b>0)&(nf==0)&region)
 records.append({'ref':n,'region':[lower,left,right],'source_links':links,'special_source_registration':special,'rejected_rows':reject,'remaining_base_lower':[[int(x-160),int(y-160)]for y,x in issues],'components':{'base':int(label(b>0,np.ones((3,3)))[1]),'fourth':int(label(nf>0,np.ones((3,3)))[1])},'base_unchanged':True,'source_sha256':sha(original.tobytes()),'new_sha256':sha(nf.tobytes())})
 rows.append((f'{n} authored-leg registration',[('new basic',a.rgba(b)),('new Fourth source',a.rgba(original,16)),('Fourth registered',a.rgba(nf,16)),('actual combined',a.rgba(full,16))]))
for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
(out/'manifest.json').write_text(json.dumps({'frames':records,'method':'새 기본 부츠 불변. 같은 새포스 원화 행에서 인접2픽셀/최대2배 폭 이내의 다리·구두를 등록. 전신축척/옛 픽셀/임의채움 없음.','native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps([{k:r[k]for k in('ref','rejected_rows','remaining_base_lower','components')}for r in records]))
