"""표시 픽셀을 바꾸지 않고 기존 공유 스트림 안에 넣을 저장 배치를 찾는다."""
import argparse,json,itertools,random,math,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,indexed_atlas,composition_frame
from src.psx_compress import encode_stream
from src.psx_paired_layout import pack_pair,pack_joint_pair,pack_variant_pair
from src.psx_tile_layout import remap_tiles

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',choices=('ver_buki_riko','ver_rin_nana'),default='ver_buki_riko');p.add_argument('--pairs',type=Path,required=True);p.add_argument('--layout',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--plan',type=Path,default=ROOT/'work/ver_buki_riko/shibuki_run_plan/20261026T044831801392Z/plan.json');p.add_argument('--seed',type=int,default=0);p.add_argument('--steps',type=int,default=1600);p.add_argument('--fast-cost',action='store_true',help='Optional local Numba cost estimator; final producer encodes again');args=p.parse_args()
 if args.fast_cost:
  sys.path.insert(0,str(ROOT/'work/tools'));from psx_compress_cost import encoded_cost
 else:
  def encoded_cost(raw):return len(encode_stream(raw))
 if not 1<=args.steps<=20000:raise ValueError('Invalid search steps')
 d=args.pairs.resolve();parent=args.parent.resolve()
 name='nana' if args.project=='ver_rin_nana' else 'shibuki'
 if not d.is_relative_to(ROOT/'work'/args.project/(name+'_art')) or not parent.is_relative_to(ROOT/'out'/args.project):raise ValueError('Isolated project paths required')
 arc=(parent/'modified.arc').read_bytes();manifest=json.loads((parent/'manifest.json').read_text())
 if sha256(arc)!=manifest['modified_archive_sha256'] or manifest['task']!='x_'+name:raise ValueError('Parent hash or task mismatch')
 entries=psx_arc(arc)
 def entry(t):
  e=next(e for e in entries if int(e['type'],16)==t);return arc[e['offset']:e['offset']+e['size']]
 gfx,parts=entry(2),entry(3);bank=graphics_bank(gfx,0,allow_bank_aliases=True);pairs=json.loads((d/'pairs.json').read_text());layouts=json.loads(args.layout.read_text())
 plan=json.loads(args.plan.read_text());results=[]
 previous=json.loads((d/'packing.json').read_text()) if (d/'packing.json').exists() else []
 for r in pairs['frames']:
  n=r['run'];layout=next((l for l in layouts if l['frame']==n and l['fits']),None)
  if layout is None:continue
  desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128);pair=next(q for q in plan['paired_frames'] if q['frames'][0]==n)
  writable=sorted(set(pair['common_base_tiles']+pair['nonshoot_only_tiles']+pair['shoot_only_tiles']));layers=[np.array(Image.open(d/f'{s}_{n:03d}.png')) for s in ('run','common','shoot_body','gun')]
  if layout['mode']=='variant':raw,rp,sp,*_=pack_variant_pair(dec.data,desc['tile_count'],layers[0],np.array(Image.open(d/f'shoot_{n:03d}.png')),layout['rects'],layout['run_rects'],layout['shot_rects'],writable)
  elif layout['mode']=='joint':raw,rp,sp,*_=pack_joint_pair(dec.data,desc['tile_count'],layers[0],np.array(Image.open(d/f'shoot_{n:03d}.png')),layout['rects'],layout['unique_rects'],writable)
  else:raw,rp,sp,*_=pack_pair(dec.data,desc['tile_count'],*layers,layout['rects'],r['run_arm_rect'],r['gun_rect'],writable)
  counts=[len(composition_frame(parts,0,q)['parts']) for q in (n,n+1)]
  if len(rp)>counts[0] or len(sp)>counts[1]:raise ValueError('Too many parts')
  used={t for t,x,y in rp+sp}
  if (len(rp)<counts[0] or len(sp)<counts[1]) and not set(writable)-used:raise ValueError(f'Frame {n}: spare record needs a blank tile')
  budget=dec.end-dec.start;raw_hash=sha256(raw);prior=next((q for q in previous if q['frame']==n and q.get('raw_sha256')==raw_hash),None);prior_cost=None
  if prior:
   try:
    oldmap={int(k):v for k,v in prior['mapping'].items()};oldflip={int(k):v for k,v in prior['flips'].items()};oldshift={int(k):v for k,v in prior.get('shifts',{}).items()}
    prior_cost=encoded_cost(remap_tiles(raw,desc['tile_count'],oldmap,oldflip,oldshift));valid_cached=prior_cost<=budget
   except ValueError:valid_cached=False
   if valid_cached:
    results.append(prior);print(json.dumps({'frame':n,'cached_verified_solution':True}),flush=True);continue
  mapping={t:t for t in writable};flips={};shifts={};best=encoded_cost(raw);initial=best;rng=random.Random(n+207+args.seed)
  if prior_cost is not None and prior_cost<best:best,mapping,flips,shifts=prior_cost,oldmap,oldflip,oldshift
  atlas,_,_=indexed_atlas(raw,desc['tile_count']);movements={}
  for t in writable:
   coords=[(x,y) for y in range(16) for x in range(16) if atlas[(t//16*16+y)*256+t%16*16+x]]
   if not coords:continue
   xs,ys=zip(*coords);movements[t]=[(x,y) for x in range(-min(xs),16-max(xs)) for y in range(-min(ys),16-max(ys))]
  def cost(m,f,s):
   try:return encoded_cost(remap_tiles(raw,desc['tile_count'],m,f,s))
   except ValueError:return 100000
  for sweep in range(7):
   if best<=budget:break
   candidates=[]
   for a,b in itertools.combinations(writable,2):
    m=dict(mapping);m[a],m[b]=m[b],m[a];candidates.append((m,dict(flips),dict(shifts)))
   for a in writable:
    for flag in (64,128,192):
     f=dict(flips);f[a]=f.get(a,0)^flag;candidates.append((dict(mapping),f,dict(shifts)))
   for a,options in movements.items():
    for xy in options:candidates.append((dict(mapping),dict(flips),{**shifts,a:list(xy)}))
   rng.shuffle(candidates);improved=False
   for m,f,s in candidates:
    size=cost(m,f,s)
    if size<best:best,mapping,flips,shifts=size,m,f,s;improved=True
    if best<=budget:break
   print(json.dumps({'frame':n,'sweep':sweep,'best':best,'budget':budget}),flush=True)
   if not improved:break
  current=best;cm,cf,cs=dict(mapping),dict(flips),dict(shifts)
  for step in range(args.steps):
   if best<=budget:break
   m,f,s=dict(cm),dict(cf),dict(cs);kind=rng.randrange(3)
   if kind==0:
    a,b=rng.sample(writable,2);m[a],m[b]=m[b],m[a]
   elif kind==1:
    a=rng.choice(writable);f[a]=f.get(a,0)^rng.choice((64,128,192))
   else:
    a=rng.choice(list(movements));s[a]=list(rng.choice(movements[a]))
   size=cost(m,f,s);temp=1+4*(1-step/args.steps)
   if size<=current or rng.random()<math.exp((current-size)/temp):current,cm,cf,cs=size,m,f,s
   if size<best:best,mapping,flips,shifts=size,dict(m),dict(f),dict(s)
  record={'frame':n,'initial':initial,'encoded_bytes':best,'budget':budget,'fits':best<=budget,'mapping':mapping,'flips':flips,'shifts':shifts,'common_rects':layout['rects'],'raw_sha256':raw_hash}
  if layout['mode']=='joint':record['joint_unique_rects']=layout['unique_rects']
  if layout['mode']=='variant':record.update(variant_run_rects=layout['run_rects'],variant_shot_rects=layout['shot_rects'])
  results.append(record);(d/'packing.json').write_text(json.dumps(results+[q for q in previous if q['frame']>n],indent=2));print(json.dumps({'frame':n,'bytes':best,'budget':budget,'fits':best<=budget}),flush=True)
 (d/'packing.json').write_text(json.dumps(results,indent=2))
 print(json.dumps({'completed_frames':len(results),'failed':[r['frame'] for r in results if not r['fits']]}))

if __name__=='__main__':main()
