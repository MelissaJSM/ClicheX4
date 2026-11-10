"""Split authored ladder art into existing five equipment layers."""
from pathlib import Path
import sys,json,hashlib,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper
sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((D/'first_inputs01/manifest.json').read_text('utf8'));a=Archive((ROOT/m['source_arc']).read_bytes());assert sha(a.data)==m['source_arc_sha256']
Y,X=np.indices((384,384));Y-=160;X-=160
DATA={
143:{'eye':[-5,-17],'lower':4,'arms':[[[-17,-28],[-10,-28],[-3,-12],[-9,-7]], [[-12,-7],[-3,-12],[0,-6],[-4,0],[-12,-1]]]},
144:{'eye':[-1,-18],'lower':7,'arms':[[[-12,-31],[-5,-31],[-5,-8],[-10,-9]],[[2,-16],[7,-16],[11,-11],[11,-5],[5,-4],[3,-9]]]},
146:{'eye':[-1,-17],'lower':7,'arms':[[[-12,-33],[-4,-33],[-5,-9],[-10,-9]],[[1,-14],[6,-14],[10,-9],[10,-3],[4,-3],[2,-7]]]},
149:{'eye':[-7,-16],'lower':4,'arms':[[[1,-31],[9,-31],[8,-14],[2,-10],[-1,-12]],[[-13,-11],[-5,-11],[1,-6],[-2,-1],[-13,-1]]]},
151:{'eye':[-1,-18],'lower':3,'arms':[[[-13,-23],[-4,-23],[-4,-8],[-9,-8],[-14,-15]],[[2,-17],[10,-17],[14,-12],[13,-5],[5,-7]]]},
153:{'eye':[0,-9],'lower':4,'arms':[[[-14,-1],[-6,-1],[-6,6],[-10,7],[-15,7] ],[[6,-1],[13,-1],[15,7],[10,7],[6,5]]]},
154:{'eye':[-13,-4],'lower':11,'arms':[[[-15,0],[-7,1],[-5,6],[-8,10],[-16,10],[-16,7]]]},
183:{'eye':[-1,-4],'lower':19,'arms':[[[-14,1],[-8,1],[-5,7],[-7,10],[-12,9] ],[[4,2],[14,2],[15,6],[10,10],[5,9]]]}}
def polygon(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0
def composite(ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
ap=argparse.ArgumentParser();ap.add_argument('--v2',action='store_true');ap.add_argument('--v3',action='store_true');ap.add_argument('--v4',action='store_true');ap.add_argument('--v5',action='store_true');args=ap.parse_args();args.v3|=args.v4;args.v2|=args.v3 or args.v5;out=D/('joint_layers05'if args.v5 else('joint_layers04'if args.v4 else('joint_layers03'if args.v3 else('joint_layers02'if args.v2 else'joint_layers01'))));out.mkdir(exist_ok=False);frames={};records=[];rows=[];partials=[]
for n,q in DATA.items():
 ex,ey=q['eye'];b=np.array(Image.open(D/'common_legs02'/f'base_{n:03}_indices.png'));f=np.array(Image.open(D/'common_legs02'/f'fourth_{n:03}_indices.png'))
 owner=np.full(b.shape,6,np.uint8);owner[(Y>=q['lower'])|((X>=ex+10)&(Y>=ey+4))]=8
 if not args.v3:owner[(Y<ey+6)&((X>=ex-3)|(Y<ey-2))]=5
 for p in q['arms']:owner[polygon(p)]=7
 if args.v2:
  # Keep the established 16x16 crown module's ownership, so equipping
  # an arm does not accidentally swap the rear hat/upper veil.
  cx,cy={143:(1,-16),144:(0,-18),146:(0,-16),149:(-2,-17),151:(0,-19),153:(0,-13),154:(-6,-3),183:(0,3)}[n]
  head=(X>=cx-7)&(X<cx+9)&(Y>=cy-8)&(Y<cy+8);owner[head]=5
 if args.v4:
  if n==143:owner[(X>=10)&(Y>=-20)&~head]=8
  if n==149:owner[(X>=7)&(Y>=-13)&~head]=8
 for ref in((149,150,155)if n==149 else(n,)):
  body=b.copy();costume=f.copy();own=owner.copy()
  if ref!=n:
   sd=D/('shot_modules03'if args.v5 else'shot_modules02');body=np.array(Image.open(sd/f'base_{ref:03}_body.png'));costume=np.array(Image.open(sd/f'fourth_{ref:03}_body.png'));arm=np.array(Image.open(sd/f'base_{ref:03}_arm.png'));own[(arm>0)if args.v5 else((arm>0)|((X<=-4)&(Y>=-16)&(Y<=-1)))]=7
  full=np.where(costume,costume,body).astype(np.uint8);pc=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full];change=((full!=body)|((costume>0)&pc))&(full>0)
  ls={0:body,**{pb:np.where(change&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
  expect=a.rgba(body);expect.alpha_composite(a.rgba(costume,16));assert np.array_equal(np.array(composite(ls,15,1)),np.array(expect))
  frames[ref]=ls;records.append({'ref':ref,'source_new_body':n,'components':[{'mask':mask,'arm':arm,'count':int(label(np.array(composite(ls,mask,arm))[:,:,3]>0,np.ones((3,3)))[1])}for mask in range(16)for arm in(1,2)],'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()}})
  Image.fromarray(own).save(out/f'owner_{ref:03}.png')
  rows.append((f'ladder {ref}',[('base idle',a.composite(0)[0]),('new base',composite(ls,0)),('Fourth idle',a.composite(0,15)[0]),('full Fourth',composite(ls,15))]))
  partials.append((f'partial {ref}',[(name,composite(ls,mask))for name,mask in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))]))
for src,dest,total in((144,145,319),(146,147,320),(149,148,320),(151,152,320)):
 frames[dest]={}
 for pb,z in frames[src].items():
  v=np.zeros_like(z);yy,xx=np.nonzero(z);v[yy,total-xx]=z[yy,xx];frames[dest][pb]=v
 records.append({'ref':dest,'mirror_of':src,'x_sum_canvas':total,'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in frames[dest].items()}})
for ref,ls in frames.items():
 for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{ref:03}.png')
for i in range(0,len(rows),2):
 helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',5);helper.grid(partials[i:i+2],out/f'partial_{i//2+1}.png',5)
(out/'manifest.json').write_text(json.dumps({'parent_arc':m['source_arc'],'parent_sha256':m['source_arc_sha256'],'frames':records,'refs':sorted(frames),'semantic_geometry':DATA,'native_packed':False,'runtime_verified':False,'status':'부분아머 의미소유 초기안, 그림 검토 전'},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'refs':sorted(frames),'layers':sum(len(ls)for ls in frames.values()),'component_issues':[{ 'ref':q['ref'],'issues':[t for t in q.get('components',[])if t['count']>1]}for q in records if any(t['count']>1 for t in q.get('components',[]))]}))
