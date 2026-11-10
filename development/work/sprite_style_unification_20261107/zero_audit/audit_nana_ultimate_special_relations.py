"""Ultimate 나나 특수 원작/현재/역사 저장본 읽기. 제작 모듈 호출 없음."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent;N=B/'nana_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,render,tile
O=D/'nana_ultimate_special_relations01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
tracked={}
def load(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return b
def box(z):
 y,x=np.nonzero(z);return [int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)] if len(x) else None
def shift(z,dx):
 v=np.zeros_like(z);v[:,max(dx,0):min(384,384+dx)]=z[:,max(-dx,0):min(384,384-dx)];return v
def merged(a,n,mask):
 v=a.layer(n,0)[0].copy()
 for pb,bit in ((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:
   q=a.layer(n,pb)[0];v[q>0]=q[q>0]
 return v
old=ROOT/'work/ver_rin_nana/nana_ultimate_armor';over=ROOT/'work/overhaul_20261105/sprites'
paths={
 'current':N/'ultimate_ladder_repaint/packed_first7_diagnostic_v1/PL02_U.ARC',
 'previous':N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC',
 'historical_special':old/'special_packed_v3/PL02_U.ARC',
 'historical_elemental':old/'elemental_packed_v1/PL02_U.ARC',
 'overhaul_baseline':over/'ver_rin_nana/baseline/PL02_U.ARC'}
arcs={k:Archive(load(p)) for k,p in paths.items()}
assert sha(arcs['current'].data)=='dcaf1343747fabeab3054c59fc384c3bbd598209eccb6c5a37ac84c1d340d339'
assets,_=read_disc(ROOT/'MegaMan X4.bin',('PL02_U.ARC',))
arcs['original_US']=Archive(assets['PL02_U.ARC'])
PBS=(0,5,6,7,8);REFS=(88,89,95,96,97,98,99)
cur=arcs['current'];prev=arcs['previous'];original=arcs['original_US']
for n in REFS:
 assert raw(cur,0,n)==raw(prev,0,n)
 for pb in PBS:assert [sig(p)for p in parts(cur,pb,n)]==[sig(p)for p in parts(prev,pb,n)]
relations=[];frames=[]
for tag,a in arcs.items():
 for s,t,dx in ((89,88,-1),(95,96,1),(98,99,1)):
  q={'archive':tag,'source':s,'target':t,'dx':dx,'layers':{},'forms':{}}
  for pb in PBS:
   x=shift(a.layer(s,pb)[0],dx);y=a.layer(t,pb)[0];diff=x!=y
   q['layers'][str(pb)]={'changed':int(diff.sum()),'alpha_changed':int(((x>0)!=(y>0)).sum()),'bbox':box(diff),'parts_source':[sig(p)for p in parts(a,pb,s)],'parts_target':[sig(p)for p in parts(a,pb,t)]}
  for form,mask in (('before',15),('after',0)):
   x=shift(merged(a,s,mask),dx);y=merged(a,t,mask);diff=x!=y
   q['forms'][form]={'changed':int(diff.sum()),'alpha_changed':int(((x>0)!=(y>0)).sum()),'bbox':box(diff),'delta_cells':[[int(xx-160),int(yy-160),int(x[yy,xx]),int(y[yy,xx])]for yy,xx in np.argwhere(diff)]}
  relations.append(q)
for n in REFS:
 f=cur.banks[0]['frames'][n];row={'ref':n,'tile_count':f['tile_count'],'stream_offset':f['offset'],'raw_owners':[g['index']for g in cur.banks[0]['frames']if g['offset']==f['offset']],'layers':{}}
 for pb in PBS:
  pp=parts(cur,pb,n);slots={p['record_offset']for p in pp};row['layers'][str(pb)]={'parts':pp,'record_owners':[m for m in range(237)if m!=n and slots&{p['record_offset']for p in parts(cur,pb,m)}]}
 frames.append(row)
# Strictly separate original effect pixels from current differences in the body.
op=parts(original,0,88);assert [p['tile']for p in op[6:8]]==[7,8]
fx=render(original,88,0,op[6:8]);assert int((fx>0).sum())==83
np.save(O/'effect_088_original.npy',fx)
effect={'original_parts':op[6:8],'opaque':83,'bbox':box(fx>0),'whole_tiles':[{'tile':k,'sha256':sha(tile(original,88,k).tobytes())}for k in (7,8)],'forms':{}}
for form,mask in (('before',15),('after',0)):
 c=merged(cur,88,mask);body=shift(merged(cur,89,mask),-1);outsidefx=(c!=body)&(fx==0)
 effect['forms'][form]={'values_on_original_effect':{str(k):int(np.sum(c[fx>0]==k))for k in np.unique(c[fx>0])},'non_effect_body_delta':int(outsidefx.sum()),'body_delta_bbox':box(outsidefx),'body_delta_cells':[[int(x-160),int(y-160),int(body[y,x]),int(c[y,x])]for y,x in np.argwhere(outsidefx)]}
# Compare historical indexed PNG/actual composite, without executing historical code.
history=[]
for tag,folder,ids in [('special',old/'special_packed_v3',(88,89,97,98,99)),('elemental',old/'elemental_packed_v1',(95,96))]:
 a=arcs['historical_'+tag]
 recipe=json.loads(load(folder/'recipe.json'))
 for n in ids:
  p=folder/f'ultimate_{n:03}.png';img=np.array(Image.open(p));load(p);v=np.zeros((384,384),np.uint8);v[80:240,80:240]=img
  assert np.array_equal(v,merged(a,n,15))
  history.append({'ref':n,'historical_png':rel(p),'historical_composite_exact':True,'current_before_delta':int((v!=merged(cur,n,15)).sum()),'current_after_delta':int((v!=merged(cur,n,0)).sum()),'registration':next(t for t in recipe['registration']if t['frames'][0]==n)})
norm=json.loads(load(over/'nana_preultimate/normalized/normalization.json'));normchecks=[]
for n in REFS:
 p=over/f'nana_preultimate/normalized/{n:03}.png';v=np.array(Image.open(p));load(p)
 normchecks.append({'ref':n,'current_after_exact':bool(np.array_equal(v,merged(cur,n,0))),'changed':int((v!=merged(cur,n,0)).sum()),'normalization_record':next((r for r in norm['reports']if r['frame']==n),None)})
for p in ['scripts/prepare_nana_ultimate_special.py','scripts/prepare_nana_ultimate_elemental.py','scripts/overhaul_sprites_costume.py','scripts/overhaul_sprites_costume_pack.py']:load(ROOT/p)
evidencep=D/'shibuki_standing_special_relations01';pr=json.loads(load(evidencep/'report.json'));pc=json.loads(load(evidencep/'conclusions.json'))
tables=[q for q in pr['tables']if q['id']in(91,95,96,97,104,105)]
# Fresh actual render and aligned pair boards, labelled by current form.
boards=[]
for form,mask in (('before',15),('after',0)):
 im=Image.new('RGB',(4*256,3*340),'#273442');dr=ImageDraw.Draw(im)
 for row,(s,t,dx)in enumerate(((89,88,-1),(95,96,1),(98,99,1))):
  ss=cur.composite(s,mask)[0];tt=cur.composite(t,mask)[0];ss2=Image.new('RGBA',ss.size);ss2.paste(ss,(dx,0))
  x=shift(merged(cur,s,mask),dx);y=merged(cur,t,mask);diff=x!=y
  dd=tt.copy();da=np.array(dd);da[diff]=[255,70,180,255];dd=Image.fromarray(da)
  for col,(label,pic)in enumerate([(str(s),ss),(f'{s} x{dx:+}',ss2),(str(t),tt),('difference marked',dd)]):
   pic=pic.crop((128,118,192,194)).resize((256,304),Image.Resampling.NEAREST);im.paste(pic,(col*256,row*340+26),pic);dr.text((col*256+3,row*340+5),f'{form} {label}',fill='white')
 p=O/f'{form}_pairs.png';im.save(p);boards.append({'path':rel(p),'sha256':sha(p.read_bytes())})
out={'scope':'Nana Ultimate 원US/현재/역사 저장본 특수 공유 및 이전에 읽은 원EXE 표 증거 재사용','current_sha256':sha(cur.data),'source_files':tracked,'current_previous_specials_raw_and_records_exact':True,'original_PL02_sha256':sha(original.data),'relations':relations,'frames':frames,'effect83':effect,'historical_targets':history,'normalized_after_provenance':normchecks,'existing_PS1_evidence':{'report_sha256':sha((evidencep/'report.json').read_bytes()),'conclusions_sha256':sha((evidencep/'conclusions.json').read_bytes()),'dispatch':pc['actual_PS1_dispatch'],'tables':tables},'boards':boards,'producer_functions_called':False,'MIPS_execution':False,'gameplay_verified':False,'art_or_resource_modified':False}
(O/'report.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha256':sha((O/'report.json').read_bytes()),'current_pairs':[{'source':q['source'],'target':q['target'],'before':q['forms']['before']['changed'],'after':q['forms']['after']['changed']}for q in relations if q['archive']=='current'],'effect':effect['forms'],'normalized':normchecks},ensure_ascii=False))
