"""새9참조의 별도 reader·거부검사 및 원MIPS 계획 준비."""
from pathlib import Path
import json,hashlib
D=Path(__file__).parent;E=D/'rin_extension';P=E/'prepared_ladder_dash01';C=hashlib.sha256((P/'PL01_U.ARC').read_bytes()).hexdigest()
plan=json.loads((E/'rin205_components.json').read_text('utf8'));plan['resources']['PL01_U.ARC'].update(path='work/sprite_style_unification_20261107/zero_audit/rin_extension/prepared_ladder_dash01/PL01_U.ARC',after=C);(E/'rin214_components.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
s=(D/'verify_rin205_readback.py').read_text('utf8');tail=s[s.index('g,c=entry(old,2)'):];tail=tail.replace('support={(0,198),(1,144),(1,145),(1,147),(1,157),(1,159)}','support={(0,n)for n in(200,203,205,207,209,211,157)}').replace("counts['authored_exact']==5 and counts['other_display_exact']==431","counts['authored_exact']==9 and counts['other_display_exact']==427").replace('prepared_spin01','prepared_followthrough01').replace('rin205_components','rin214_components').replace("'cumulative_authored_refs':205,'incremental_refs':5,'previous200_preserved':True","'cumulative_authored_refs':214,'incremental_refs':9,'previous205_preserved':True").replace('final205_readback_audit','final214_readback_audit')
head='''"""Actual generated fixed-grid source to decoded ARC; no producer imports."""
from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
D=Path(__file__).parent/'rin_extension';P=D/'prepared_ladder_dash01';A=D/'ladder_dash_registered_v1';G=D/'ladder_dash01';sha=lambda b:hashlib.sha256(b).hexdigest()
old=(D/'prepared_followthrough01/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(old)=='d3bee17d11b9181d96395fcd0274353f78ef5f7f1bc7c8c5428e573fae3d88b8';assert sha(new)=='CANDIDATE'
reg=json.loads((A/'registration.json').read_text('utf8'));info=json.loads((G/'inputs.json').read_text('utf8'));assert reg['source_arc_sha256']==sha(old);im=Image.open(G/'generated.png').convert('RGBA');assert sha((G/'generated.png').read_bytes())==reg['source_generated_sha256']=='8b0421d987948cee062ceac6f545db0161647561f62d9978317859fb44b0b8cf'
pal=struct.unpack_from('<16H',entry(old,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);masters={};provenance=[];cw=im.width/2
for row in reg['records']:
 key=row['key'];n=row['ref'];f=next(v for v in info['frames']if v['key']==key);cx,cy=f['cell'];crop=im.crop((round(cx*cw),round(cy*cw),round((cx+1)*cw),round((cy+1)*cw)));v=np.array(crop);nearest=np.zeros(v.shape[:2],np.uint8)
 for yy in range(v.shape[0]):nearest[yy]=1+np.sum((v[yy,:,:3,None].transpose(0,2,1).astype(np.int32)-colors[None,:,:])**2,2).argmin(1)
 votes=np.stack([np.array(Image.fromarray(np.where(nearest==i,v[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)]);alpha=np.array(crop.getchannel('A').resize((96,96),Image.Resampling.BOX));cell=np.where(alpha>=128,votes.argmax(0)+1,0).astype(np.uint8);z=np.zeros((384,384),np.uint8);z[104:200,112:208]=cell;assert np.array_equal(z,np.array(Image.open(G/'native_fixed'/(key+'_indices.png'))))
 rr,gg,bb,aa=np.moveaxis(v.astype(float),-1,0);yy,xx=np.where((rr<gg*.6)&(gg>90)&(gg/(bb+1)>.6)&(gg/(bb+1)<1.15)&(aa>=128));counts=collections.Counter((112+int(x*96/cw),104+int(y*96/cw))for x,y in zip(xx,yy))
 for eye in row['cyan_eye_registration']:
  ex,ey=eye['point'];assert counts[ex,ey]==eye['cyan_source_sample_count']>=15;assert z[ey,ex]==eye['old_index'];assert eye['new_index']==15;z[ey,ex]=15
 dx,dy=row['translation'];z=np.roll(z,(dy,dx),(0,1));assert np.array_equal(z,np.array(Image.open(G/'anchor_probe'/(key+'_indices.png'))))
 if n in(199,202):
  x0,y0,x1,y1=row['head_box'];head=np.zeros_like(z);head[y0:y1,x0:x1]=z[y0:y1,x0:x1];mask=binary_fill_holes(head>0);assert mask.sum()==row['head_mask_pixels'];assert sha((A/(key+'_head_mask.png')).read_bytes())==row['head_mask_sha256'];assert np.array_equal(mask,np.array(Image.open(A/(key+'_head_mask.png')))>0)
  body=z.copy();body[mask]=0;out=np.roll(body,-2,axis=0);out[mask]=head[mask];assert np.array_equal(out[mask],z[mask]);z=out
 assert np.array_equal(z,np.array(Image.open(A/(key+'_indices.png'))));assert sha((A/(key+'_indices.png')).read_bytes())==row['output_sha256'];assert np.nonzero(z)[0].max()==np.nonzero(render(old,0,0,n)[0])[0].max();masters[0,n]=z
 provenance.append({'key':key,'fixed_grid_quantization_exact':True,'source_cyan_eye_samples_verified':True,'new_body_translation_head_and_negative_spaces_exact':n in(199,202),'registered_sha256':row['output_sha256']})
targets={}
for m,refs in[(199,[199,201]),(202,[202,204,206,208,210]),(155,[155]),(156,[156])]:
 for n in refs:assert np.array_equal(render(old,0,0,n)[0],render(old,0,0,m)[0]);targets[0,n]=masters[0,m]
'''.replace('CANDIDATE',C)
(D/'verify_rin214_readback.py').write_text(head+tail,'utf8')
s=(D/'check_rin205_guards.py').read_text('utf8').replace('pack_rin_followthrough01','pack_rin_ladder_dash01').replace('rin205','rin214').replace('missing146','missing199').replace('altered156','altered155').replace('changed_alias212','changed_alias204').replace('del t[1,146]','del t[0,199]').replace('t[1,146]','t[0,199]').replace('t[1,156]','t[0,155]').replace('t[1,157]','t[0,157]').replace('t[0,212]','t[0,204]');(D/'check_rin214_guards.py').write_text(s,'utf8')
print(C)
