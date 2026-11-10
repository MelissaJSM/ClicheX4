"""승리 두 원화의 머리/팔/몸/다리를 분리하고 소수 의상 경계를 정합한다."""
from pathlib import Path
import sys,argparse
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
from register_ladder_parts import poly,compose

HEAD={
204:[(-15,-26),(8,-26),(14,-13),(15,-6),(8,-2),(5,-1),(-8,-3),(-15,-11)],
205:[(-15,-26),(9,-26),(17,-12),(16,-4),(8,0),(5,-2),(-7,-3),(-14,-11)],
206:[(-17,-27),(8,-27),(14,-16),(8,-10),(6,-4),(-7,-3),(-14,-10)],
207:[(-17,-27),(5,-27),(7,-14),(4,-4),(-7,-3),(-15,-11)]}
ARMS={
204:[[(-25,-8),(-11,-8),(-8,-2),(-11,8),(-19,10),(-25,3)],[(-1,-2),(8,-1),(10,9),(3,12),(-2,7)]],
205:[[(-18,-19),(-8,-19),(-7,-10),(-11,0),(-17,-3),(-21,-10)],[(0,-2),(9,-1),(11,9),(4,12),(-1,7)]],
206:[[(-16,-5),(-9,-5),(-6,2),(-7,9),(-15,9)],[(-3,-20),(6,-20),(10,-9),(9,0),(3,3),(-2,-2)]],
207:[[(-16,-5),(-9,-5),(-6,2),(-7,9),(-15,9)],[(2,-31),(10,-31),(12,-11),(9,-1),(3,3),(1,-4)]]}
LEGS=[ [(-11,9),(-3,9),(-2,15),(-5,24),(-15,24),(-15,19)],[(0,9),(7,9),(10,15),(13,24),(3,24),(0,18)] ]

def make(a,n):
 folder=H/f'victory_native_page{1 if n<206 else 2:02}'
 base=np.array(Image.open(folder/f'base_{n:03}_indices.png'));full=np.array(Image.open(folder/f'fourth_{n:03}_indices.png'));raw=full.copy()
 own=np.full(base.shape,6,np.uint8)
 for p in LEGS:own[poly(p)]=8
 own[poly(HEAD[n])]=5
 for p in ARMS[n]:own[poly(p)]=7
 # The raised wrists/sleeves pass in front of the hair in 205..207. The
 # opposite side's long hair remains body-owned with its coat backing.
 rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:32]],np.int32)
 nearest={i:int(((rgb[17:32]-rgb[i])**2).sum(1).argmin())+1 for i in range(1,16)}
 garment={1:2,4:11,10:10,11:11,12:9,13:9,15:1};rows=[]
 for y,x in zip(*np.nonzero((base>0)&(full==0))):
  src=int(base[y,x]);b=int(own[y,x]);dst=nearest[src]
  if b!=5 and src in garment:dst=garment[src]
  elif b==5 and src in(1,4,10,11):dst={1:2,4:11,10:10,11:11}[src]
  full[y,x]=dst;rows.append([int(x)-160,int(y)-160,src,dst,b])
 layers={0:base,**{b:np.where(own==b,full,0).astype(np.uint8)for b in(5,6,7,8)}}
 need(np.array_equal(raw[raw>0],full[raw>0]),'New Fourth source altered')
 return layers,own,dict(ref=n,source=folder.name,edge_registration=rows,original_fourth_source_pixels_exact=True,base_outside_final_fourth=int(np.count_nonzero((base>0)&(full==0))))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();out=H/args.output;need(out.is_relative_to(H)and not out.exists(),'Output conflict')
 data=(H/'prepared_ladder_wall_front02/PL00_U.ARC').read_bytes();need(sha(data)=='76f19a188ad58dd447eec058b669f8d62a4b8c00f957de3b229aeaa67f37495b','Parent changed');a=Archive(data);out.mkdir();proof=[];review={0:[],15:[]}
 for n in range(204,208):
  layers,own,row=make(a,n);proof.append(row)
  for b,v in layers.items():Image.fromarray(v).save(out/f'{n:03}_bank{b}_indices.png')
  Image.fromarray(own).save(out/f'{n:03}_owner.png')
  page([(f'{n} mask{mask:X}',compose(a,layers,mask))for mask in range(16)],a.composite(0,15)[0],out/f'partial_{n:03}.png',cols=4,scale=4)
  for mask in(0,15):review[mask].extend([(f'{n} before',a.composite(n,mask)[0]),(f'{n} registered',compose(a,layers,mask))])
 for mask,label in((0,'base'),(15,'fourth')):page(review[mask],a.composite(0,mask)[0],out/f'{label}_comparison.png',cols=2,scale=4)
 write(out/'registration.json',dict(parent_sha256=sha(data),rows=proof,source_new_art_pixels_exact=True,old_head_body_overwrite=False,body_scaling=False,not_packed=True,partial_review_pending=True))
 print([(r['ref'],len(r['edge_registration']))for r in proof])
if __name__=='__main__':main()
