"""생성7장 고정22셀→의상/손/정본권총/하체→최종50층의 제작자 재구성."""
from pathlib import Path
import sys,json,collections
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,digest,sha,write,need
from register_page import register
from pack_native import PARENT,BEFORE,PBS,REFS
from register_canonical_cases import REMOVE,HAND
from prepare_effect_probe import render,overlay,full
from prepare_arrival_targets import split,shift
from src.psx_player import composition_frame
from scripts.c01_audio_build import read_disc
Y,X=np.indices((384,384));Y-=160;X-=160
def meta(folder,name='manifest.json'):return json.loads((D/folder/name).read_text('utf8'))
def load(folder,name):return np.array(Image.open(D/folder/name))
def poly(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0
def rect(box):
 x0,y0,x1,y1=box;return(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
def main():
 out=D/'packed_arrival_candidate_v1';lock=json.loads((out/'INPUT_FROZEN.json').read_text('utf8'))
 for q in lock['files']:need(digest(ROOT/q['path'])==q['sha256'],q['path'])
 a=Archive(PARENT.read_bytes());cache={};source_cells=[];stages=[]
 def check(z,path):
  p=Path(path);p=p if p.is_absolute()else D/p;need(np.array_equal(z,np.array(Image.open(p))),p.relative_to(ROOT).as_posix());cache[p.resolve()]=z.copy();return z
 def prior(path):
  p=Path(path);p=p if p.is_absolute()else ROOT/p;need(p.resolve()in cache,'선행 재구성 누락 '+str(p));return cache[p.resolve()].copy()
 def native(art,crop,form,dim=(96,96)):
  im=Image.open(art).convert('RGBA').crop(crop);start=16 if form=='before'else 0;pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32);z=np.zeros((384,384),np.uint8);w,h=dim;ox=160-w//2;oy=160-h//2;z[oy:oy+h,ox:ox+w]=register(im,dim,pal,'area_vote');source_cells.append({'source':Path(art).relative_to(ROOT).as_posix(),'source_sha256':digest(art),'crop':list(crop),'native_size':list(dim),'form':form,'indices_sha256':sha(z.tobytes())});return z
 for folder in('first_registered_v2','second_registered_v1','settle_registered_v1','raised138_registered_v1'):
  m=meta(folder,'registration.json');art=ROOT/m['source_art_path'];need(digest(art)==m['source_art_sha256'],'원화')
  for q in m['frames']:
   tall=q['ref']==138;z=native(art,q['source_crop'],q['form'],(96,128)if tall else(96,96));name=f'{q["form"]}_{q["ref"]:03}'+('_fixed_indices.png'if folder=='first_registered_v2'else'_indices.png');check(z,Path(folder)/name)
 for q in meta('costume_pair_probe_v3')['frames']:
  n=q['ref'];b=prior(q['before_source']);donor=prior(q['after_source'])
  for c in q['source_boundary_cells']:
   im=Image.open(ROOT/c['source_art']).convert('RGBA').crop(c['source_crop']);ar=np.array(im);alpha=ar[:,:,3].astype(np.float32)/255;rgb=ar[:,:,:3].astype(np.float32);pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);labs=np.empty(alpha.shape,np.uint8)
   for y in range(len(labs)):labs[y]=1+((rgb[y,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
   votes=np.stack([np.array(Image.fromarray(np.where(labs==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)]);coverage=np.array(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX));sx,sy=c['source_native_cell'];v=int(votes[:,sy,sx].argmax()+1);need(v==c['winner']and np.array_equal(votes[:,sy,sx],np.array(c['palette_votes'],np.float32)),'경계 실제표본');need(float(coverage[sy,sx])==c['alpha_coverage'],'경계 실제알파');x,y=c['world'];b[y+160,x+160]=v
  m=poly(q['costume_polygon'])
  if q['costume_extra_box_world']:m|=rect(q['costume_extra_box_world'])
  for x,y in q['costume_extra_points_world']:m[y+160,x+160]=True
  common=b.copy();common[b==15]=13;after=np.where(m,donor,common).astype(np.uint8);check(b,f'costume_pair_probe_v3/before_{n:03}.png');check(after,f'costume_pair_probe_v3/after_{n:03}.png')
 stages.append({'stage':'costume4','source_boundary_cells':6,'bodies':8})
 for q in meta('raised138_local_probe_v1')['frames']:
  b=prior(q['base_source']);donor=prior(q['donor_source']);m=poly(q['semantic_polygon_world']);z=np.where(m,donor,b).astype(np.uint8);check(z,f'raised138_local_probe_v1/{q["form"]}_138_indices.png')
 q=meta('settle_pair_probe_v1')['frames'][0];b=prior(q['before_source']);donor=prior(q['after_source']);c=b.copy();c[b==15]=13;after=np.where(poly(q['costume_polygon']),donor,c).astype(np.uint8);check(b,'settle_pair_probe_v1/before_138.png');check(after,'settle_pair_probe_v1/after_138.png')
 for q in meta('pistol_hands_registered_v1')['frames']:
  donor=native(ROOT/q['source_art'],q['source_crop'],q['form']);check(donor,f'pistol_hands_registered_v1/{q["form"]}_{q["ref"]:03}_fixed.png');b=prior(q['base_path']);z=np.where(poly(q['polygon']),donor,b).astype(np.uint8);check(z,f'pistol_hands_registered_v1/{q["form"]}_{q["ref"]:03}_local.png')
 cm=meta('canonical_cases_probe_v2');w=a.layer(85)[0];wm=rect((-22,-11,-14,-5))&np.isin(w,range(1,10));coords=[(int(x-160),int(y-160),int(w[y,x]))for y,x in np.argwhere(wm)];need(coords==[tuple(v)for v in cm['canonical_source_texels']],'정본85 실제20texel');weapon=[]
 for q in cm['frames']:
  n,f=q['ref'],q['form'];b=prior(q['body_source']);rm=rect(REMOVE[n])&np.isin(b,range(1,10));skin=rect(HAND[n])&np.isin(b,(10,11,12,13));case=np.zeros_like(b)
  for sx,sy,v in coords:
   tx,ty=np.array(q['matrix'])@np.array([sx,sy])+q['translation'];case[ty+160,tx+160]=v
  z=b.copy();z[rm]=0;visible=(case>0)&~skin;z[visible]=case[visible];z[skin]=b[skin];check(z,f'canonical_cases_probe_v2/{f}_{n:03}_indices.png');check(case,f'canonical_cases_probe_v2/{f}_{n:03}_case.png');weapon.append({'ref':n,'form':f,'texels':20,'visible':int(visible.sum()),'matrix':q['matrix'],'translation':q['translation']})
 body={}
 for q in meta('common_hands_probe_v1')['frames']:
  n=q['ref'];b=prior(q['before_path']);donor=prior(q['after_path']);case=prior((D/f'canonical_cases_probe_v2/before_{n:03}_case.png'));m=poly(q['common_hand_polygon'])|(case>0);common=b.copy();common[b==15]=13;after=np.where(m,common,donor).astype(np.uint8);body['before',n]=check(b,f'common_hands_probe_v1/before_{n:03}.png');body['after',n]=check(after,f'common_hands_probe_v1/after_{n:03}.png')
 lm=meta('settle_legs_registered_v1');fixed={}
 for q in lm['frames']:
  f=q['form'];fixed[f]=native(ROOT/lm['source_art'],q['source_crop'],f,(96,128));check(fixed[f],f'settle_legs_registered_v1/{f}_fixed.png')
 legs=rect(lm['legs_mask_world']);side=rect(lm['side_mask_world']);m=legs|side
 for f in('before','after'):
  b=body[f,138];z=np.where(m,fixed[f],b).astype(np.uint8)
  if f=='after':common=fixed['before'].copy();common[common==15]=13;z[legs]=common[legs]
  need(np.array_equal(z[Y>=20],b[Y>=20]),'신발/바닥보호');need(np.array_equal(z[~m],b[~m]),'권총/얼굴/상체보호');body[f,138]=check(z,f'settle_legs_registered_v1/{f}_138.png')
 stages.append({'stage':'local_hands_weapon_raisedarm_calf','fixed_cells_total':len(source_cells),'body10_reconstructed':True})
 h=Archive((ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC').read_bytes());td='arrival_targets_probe_v2';fxproof=[]
 for n in(136,137):
  ps=[q for q in composition_frame(h.c,0,n)['parts']if q['tile']==7];fx=render(h,n,ps);check(fx,f'{td}/effect_{n:03}.png');need(np.count_nonzero(fx)==46,'역사 흰선46')
  for f in('before','after'):body[f,n]=overlay(body[f,n],fx)
  fxproof.append({'ref':n,'pixels':46,'world_exact':True})
 fx134=h.layer(129)[0];check(fx134,f'{td}/effect_134.png')
 for f in('before','after'):body[f,134]=overlay(fx134,body[f,133]);body[f,139]=shift(body[f,138],-1)
 fx131=render(h,131,composition_frame(h.c,0,131)['parts'][:16]);need(np.array_equal(fx131,a.layer(132)[0]),'132 effect exact');check(fx131,f'{td}/effect_131.png');z=np.where(body['after',133]>0,13,fx131).astype(np.uint8)
 for f in('before','after'):body[f,131]=z.copy()
 original,_=read_disc(ROOT/'MegaMan X4.bin',('PL02_U.ARC',));u=Archive(original['PL02_U.ARC']);mapper=np.array([0,5,1,10,12,9,7,5,13,9,6,1,8,7,6,5],np.uint8);bg=mapper[u.layer(129)[0]%16];shell=mapper[u.layer(130)[0]%16];z=overlay(bg,np.where(body['after',133]>0,13,0).astype(np.uint8));ps=composition_frame(u.c,0,130)['parts'];counts=collections.Counter(q['tile']for q in ps);sm=np.zeros_like(z,bool)
 for q in ps:
  if counts[q['tile']]>1:
   x,y=q['x']+160,q['y']+160;z[y:y+16,x:x+16]=shell[y:y+16,x:x+16];sm[y:y+16,x:x+16]=True
 check(bg,f'{td}/effect_130_background.png');check(shell,f'{td}/effect_130_shell.png');check(sm.astype(np.uint8)*255,f'{td}/effect_130_shell_mask.png')
 for f in('before','after'):body[f,130]=z.copy()
 dp=N.parent/'zero_audit/nana_arrival141_dust01';dust=np.load(dp/'dust141_indices.npy');need(np.count_nonzero(dust)==12,'역사먼지12');check(dust,f'{td}/effect_141_visible_dust.png');body['before',141]=overlay(dust,full(a,0));body['after',141]=overlay(dust,a.layer(0)[0]);need(np.array_equal(body['before',141],full(a,141)),'앞폼141 exact')
 layers=0
 for n in REFS:
  for f in('before','after'):check(body[f,n],f'{td}/{f}_{n:03}_indices.png')
  ls=split(body['before',n],body['after',n])
  for pb in PBS:check(ls[pb],f'{td}/layer{pb}_{n:03}.png');layers+=1
 write(out/'source_reconstruction.json',{'passed':True,'candidate_sha256':digest(out/'PL02_U.ARC'),'parent_sha256':BEFORE,'input_files_verified':len(lock['files']),'generated_pages':len({q['source']for q in source_cells}),'fixed_cell_registrations':source_cells,'stages':stages,'canonical_weapon':weapon,'effect_records':fxproof,'target_layers_reconstructed':layers,'source_art_pixels_manually_painted':0,'scope':'제작자 원화7장22셀의 고정16색 등록부터6실제경계셀·의상·손/권총·138하체국소·5연동효과 및50층을 별도 재구성. 원US/역사효과 사용. 독립reader·원MIPS·실기와 구분.','runtime_verified':False});print(json.dumps({'fixed_cells':len(source_cells),'pages':len({q['source']for q in source_cells}),'layers':layers}))
if __name__=='__main__':main()
