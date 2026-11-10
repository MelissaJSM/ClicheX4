"""새138 의상 의미층과139 y−1 관계를 실제32부분조건으로 확인한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
def poly(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0
def composite(a,ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--v2',action='store_true');ap.add_argument('--hair',action='store_true');args=ap.parse_args()
 meta=json.loads((D/'body_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['art_parent_arc']).read_bytes());src=D/('hair_registered_v1'if args.hair else'contacts_probe_v1');out=D/('joint_layers_probe_v3'if args.hair else 'joint_layers_probe_v2'if args.v2 else'joint_layers_probe_v1');out.mkdir(exist_ok=False)
 b=np.array(Image.open(src/'base_138_indices.png'));f=np.array(Image.open(src/'fourth_138_indices.png'));full=np.where(f,f,b).astype(np.uint8)
 own=np.full(b.shape,6,np.uint8);own[(Y>=2)|((X>=7)&(Y>=-10))]=8;own[(Y<-11)&(X>=-7)]=5
 if args.v2 or args.hair:own[(X>=6)&(Y>=-12)]=8
 own[(X<=-7)&(Y<-10)]=7;own[poly([(0,-12),(6,-10),(8,-5),(3,-4),(-1,-6)])]=7
 pc=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full];change=((full!=b)|((f>0)&pc))&(full>0)
 layers={0:b,**{pb:np.where(change&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
 expect=a.rgba(b);expect.alpha_composite(a.rgba(f,16));need(composite(a,layers,15,1).tobytes()==expect.tobytes(),'원화전체정합')
 rows=[];partials=[];records=[]
 for n,dy in((138,0),(139,-1)):
  ls={pb:np.roll(z,dy,0)for pb,z in layers.items()};checks=[]
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  Image.fromarray(np.roll(own,dy,0)).save(out/f'owner_{n:03}.png')
  for mask in range(16):
   for arm in(1,2):
    im=composite(a,ls,mask,arm);arr=np.array(im);labels,k=label(arr[:,:,3]>0,np.ones((3,3)));sizes=np.bincount(labels.flat);sizes[0]=0;checks.append({'mask':mask,'arm':arm,'components8':k,'component_sizes':sorted([int(x)for x in sizes if x],reverse=True),'rgba_sha256':sha(im.tobytes())})
  rows.append((str(n),[('base idle',a.composite(0)[0]),('new base',composite(a,ls,0)),('Fourth idle',a.composite(0,15)[0]),('new Fourth arm2',composite(a,ls,15)),('new Fourth arm1',composite(a,ls,15,1))]))
  partials.append((str(n),[(name,composite(a,ls,m))for name,m in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))]))
  records.append({'ref':n,'source_ref':138,'translation':[0,dy],'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'owner_counts':{str(pb):int((ls[pb]>0).sum())for pb in(5,6,7,8)},'partial_checks':checks})
 helper.grid(rows,out/'comparison.png',6);helper.grid(partials,out/'partial.png',6)
 write(out/'manifest.json',{'art_parent_arc':meta['art_parent_arc'],'art_parent_sha256':sha(a.data),'contacts_manifest_sha256':digest(src/'manifest.json'),'frames':records,'ownership':'상단머리5/몸통6/높은팔과반대팔7/하체및큰뒤베일8.공통권총은양폼동일.','scope':'새138 한자세×기본포스2의상,139 전체5층 y−1.기본옛몸체복사없음.부분검토후최종부모에패킹할후보.','native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'owners':q['owner_counts'],'isolated':[c for c in q['partial_checks']if c['components8']>1]}for q in records]))
if __name__=='__main__':main()
