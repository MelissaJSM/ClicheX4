"""읽기 전용 캡처의 비동기 프레임과 가림을 수치로 비교한다."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.project import digest
from scripts.prepare_nana_idle_shot import write
from src.epsxe_state import match_sprite
ds=[ROOT/'work/ver_rin_nana/nana_batch_runtime'/v for v in ['20261029T072815288351Z','20261029T072938846438Z']]
screens={str(p.relative_to(ROOT)):Image.open(p).convert('RGB') for d in ds for p in d.glob('*.png') if p.name.startswith(('observed_','actual_'))}
exact=[];best=[];out=Path(__file__).parent
for n in range(67,85):
 targets={digest(p):p for d in ds for p in d.glob(f'expected_{n:03d}_*.png')}
 for p in targets.values():
  im=Image.open(p);a=np.array(im.convert('RGBA'))
  for name,screen in screens.items():
   matches=match_sprite(screen,im)
   if matches:exact.append({'frame':n,'target':str(p.relative_to(ROOT)),'screen':name,'matches':matches,'asynchronous_comparison':True})
  for flipped in (False,True):
   v=a[:,::-1] if flipped else a;ys,xs=np.nonzero(v[:,:,3]);colors,idx,cnt=np.unique(v[ys,xs,:3],axis=0,return_index=True,return_counts=True);anchor=idx[np.argsort(cnt)[:1]][0];ay,ax=ys[anchor],xs[anchor];record=None
   for name,screen in screens.items():
    scene=np.array(screen);cy,cx=np.nonzero(np.all(scene==v[ay,ax,:3],axis=2));cy,cx=cy-ay,cx-ax;valid=(cy>=0)&(cx>=0)&(cy+v.shape[0]<=240)&(cx+v.shape[1]<=320)
    for y,x in zip(cy[valid],cx[valid]):
     eq=np.all(scene[y+ys,x+xs]==v[ys,xs,:3],axis=1);hits=int(eq.sum())
     if record is None or hits>record['hits']:
      record={'frame':n,'flip_x':flipped,'screen':name,'target':str(p.relative_to(ROOT)),'x':int(x),'y':int(y),'hits':hits,'opaque':len(xs),'mismatch_xy':np.stack((xs[~eq],ys[~eq]),axis=1).tolist(),'actual_mismatch_colors':np.unique(scene[y+ys[~eq],x+xs[~eq]],axis=0).tolist()}
   if record:best.append(record)
 rows=[r for r in best if r['frame']==n];print(n,[(r['flip_x'],r['hits'],r['opaque'])for r in rows],flush=True)
write(out/'crosscheck_runtime.json',{'exact_matches':exact,'full_matched_frames':sorted({r['frame'] for r in exact}),'best_comparisons':best,'all_sources_read_only':True})
board=Image.new('RGB',(4*320,5*280),'#222630');draw=ImageDraw.Draw(board)
for i,n in enumerate(range(67,85)):
 rows=[r for r in best if r['frame']==n];r=max(rows,key=lambda q:q['hits']/q['opaque']);scene=screens[r['screen']];a=Image.open(ROOT/r['target']);pic=scene.crop((max(0,r['x']-8),max(0,r['y']-8),min(320,r['x']+a.width+8),min(240,r['y']+a.height+8)));pic=pic.resize((pic.width*3,pic.height*3),Image.Resampling.NEAREST);x,y=i%4*320,i//4*280;board.paste(pic,(x,y+24));draw.text((x+6,y+4),f'{n}: {r["hits"]}/{r["opaque"]}',fill='white')
board.save(out/'actual_review.png')
