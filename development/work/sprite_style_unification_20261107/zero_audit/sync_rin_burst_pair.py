"""Rebuild both cumulative embedded bodies from proven original dome, no effect edits."""
from pathlib import Path
import sys,json,struct,hashlib,os,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent/'rin_extension'
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render,rgba
from scripts.c01_audio_build import read_disc
from scripts.extract_zero import save_image
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static,patch_static
sha=lambda b:hashlib.sha256(b).hexdigest()
P=D/'prepared_burst_pair_main_v1/PL01_U.ARC';B=D/'prepared_air_continuation2_v2/PL01_U.ARC';F=D/'prepared_priority_final_v2/PL01_U.ARC';O=D/'prepared_burst_pair_final_v1'
assert not O.exists()
arc=P.read_bytes();before=B.read_bytes();fifty=F.read_bytes()
assert sha(arc)=='70a7ecd20e9aa34efa6f092c8c71d607883b8a42df4489f932a03518b7b736e5'
assert sha(before)=='ffca3087c17c883e6383b0ff38417b003138d1614c8add8edb1b99199bf322df'
assert sha(fifty)=='3536c3773f3a1a8da48e948b64c556986d2b3a51c7592baf4930b07b837b198d'
path=ROOT/'MegaMan X4.bin';assert sha(path.read_bytes())=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
original=read_disc(path,('PL01_U.ARC',))[0]['PL01_U.ARC'];ot=entry(original,0x10206);tex=entry(before,0x10206);currenttex=entry(arc,0x10206);parts=entry(arc,3);zero=np.roll(render(original,1,5,182)[0],-1,axis=0)
history=ROOT/'work/ver_rin_nana/style_revision/v4_special/static_burst';hist=json.loads((history/'static_effects.json').read_text('utf8'));pal=(history/'palette.bin').read_bytes();assert sha(pal)==hist['palette_sha256'];words=struct.unpack('<16H',pal)
frames={};comps={};proof=[];previews={}
for n,body in((23,185),(24,182)):
 cp=composition_frame(parts,6,n);comps[n]=cp;raw,size,bb,prov=compose_static(ot,cp);a=np.frombuffer(raw,np.uint8).reshape(size[1],size[0]);baseline=np.frombuffer(compose_static(tex,cp)[0],np.uint8).reshape(a.shape);current=np.frombuffer(compose_static(currenttex,cp)[0],np.uint8).reshape(a.shape)
 x0,y0,x1,y1=[160+v for v in bb];oldmask=(zero[y0:y1,x0:x1]>0)&(a>0);oldmask[:max(0,-17-bb[1])]=False
 counts=collections.Counter(loc for cells in prov for loc in cells);unique=np.array([len(cells)==1 and counts[cells[0]]==1 for cells in prov]).reshape(a.shape);assert not np.any(oldmask&~unique)
 bg=a.copy()
 for y,x in zip(*np.nonzero(oldmask)):
  mirror=-12-x-2*bb[0]
  if 0<=mirror<size[0]and not oldmask[y,mirror]and a[y,mirror]:bg[y,x]=a[y,mirror]
  else:
   available=np.flatnonzero((~oldmask[y])&(a[y]>0))
   if not len(available):bg[y,x]=0
   elif n==24 and 13 in a[y,available]:bg[y,x]=13
   else:bg[y,x]=a[y,min(available,key=lambda xx:(abs(xx-x),xx))]
 remap=np.array(hist['frames'][str(n)]['tint_map'],np.uint8)
 def composite(blob):
  bodyarr=render(blob,1,5,body)[0][y0:y1,x0:x1];mask=(bodyarr>0)&(a>0)&unique;out=bg.copy();out[mask]=remap[bodyarr[mask]];return out,mask
 prior,prior_mask=composite(before);assert np.array_equal(prior,baseline)
 actual50,mask50=composite(fifty);assert np.array_equal(actual50,current)
 after,new_mask=composite(arc);assert np.array_equal(after>0,current>0);assert np.array_equal(after[~(mask50|new_mask)],current[~(mask50|new_mask)])
 if n==24:assert np.array_equal(after,current)
 frames[n]=(after.tobytes(),size);previews[n]=(current,after);proof.append({'ref':n,'body_ref':body,'baseline_and_50_reconstruction_exact':True,'changed_pixels_from_baseline':int(np.count_nonzero(baseline!=after)),'changed_pixels_from_50':int(np.count_nonzero(current!=after)),'outside_old_new_body_exact':True,'entire_alpha_exact':True,'body_world_sha256':sha(render(arc,1,5,body)[0].tobytes()),'tint_map':remap.tolist()})
nt=patch_static(tex,comps,frames)
def users_of(t):
 changes={(i,s)for i,(a,b)in enumerate(zip(t,nt))for s in(0,4)if(a>>s&15)!=(b>>s&15)};users=[];checked=0
 for b in(1,2,3,4,6):
  for n in range(composition_frame(parts,b,0)['bank_frame_count']):
   used=set()
   for p in composition_frame(parts,b,n)['parts']:
    tile=p['page']*256+p['tile']
    for y in range(16):
     for x in range(16):used.add(((tile//16*16+y)*128+tile%16*8+x//2,(x%2)*4))
   if used&changes:users.append([b,n])
   checked+=1
 return users,checked,len(changes)
users,checked,nibbles=users_of(tex);incremental,_,_=users_of(currenttex);assert users==[[6,23],[6,24]];assert incremental==[[6,23]]
O.mkdir();(O/'palette.bin').write_bytes(pal);bound={}
for n,(pixels,size)in frames.items():save_image(pixels,size,words,O/f'effect_{n}.png');bound[str(n)]={'file':f'effect_{n}.png','sha256':sha((O/f'effect_{n}.png').read_bytes())}
evidence=(history/hist['palette_evidence_file']).resolve();assert sha(evidence.read_bytes())==hist['palette_evidence_sha256']
recipe={'kind':'us_rakuhouha_embedded_body_v1','project':'ver_rin_nana','source_texture_sha256':sha(tex),'parts_sha256':sha(parts),'palette_file':'palette.bin','palette_sha256':sha(pal),'palette_evidence_file':os.path.relpath(evidence,O),'palette_evidence_sha256':sha(evidence.read_bytes()),'frames':bound,'modified_texture_sha256':sha(nt),'expected_changed_references':users}
(O/'static_effects.json').write_text(json.dumps(recipe,indent=2)+'\n','utf8')
assert pal==evidence.read_bytes()[480*2048+96:480*2048+128]
final=replace_entry(arc,0x10206,nt);assert replace_entry(final,0x10206,currenttex)==arc;(O/'PL01_U.ARC').write_bytes(final)
sheet=Image.new('RGB',(960,720),'#28323b');draw=ImageDraw.Draw(sheet)
for col,(n,pair)in enumerate(previews.items()):
 for row,a in enumerate(pair):
  pic=rgba(a,words).resize((a.shape[1]*5,a.shape[0]*5),Image.Resampling.NEAREST);xy=(col*480+(480-pic.width)//2,row*360+25);sheet.paste(pic,xy,pic);draw.text((col*480+8,row*360+5),f'{n} '+('checkpoint50'if row==0 else'new pair52'),fill='white')
sheet.save(O/'effect_comparison.png')
base=json.loads((P.parent/'proposal.json').read_text('utf8'));base.update({'resource':str((O/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':sha(final),'main_prepared':str(P.relative_to(ROOT)),'main_prepared_sha256':sha(arc),'source_arc':str(F.relative_to(ROOT)),'source_arc_sha256':sha(fifty),'component_proposals':[str((F.parent/'proposal.json').relative_to(ROOT)),str((P.parent/'proposal.json').relative_to(ROOT))],'static_burst23_sync_required':False,'static_refs_changed_from_baseline':[23,24],'static_refs_changed_from_50':[23],'static_reconstruction':proof,'static_references_inspected':checked,'static_nibbles_changed_from_baseline':nibbles,'static_body_patch':{'recipe':str((O/'static_effects.json').relative_to(ROOT)),'sha256':sha((O/'static_effects.json').read_bytes())},'independent_review_pending':True,'user_accepted':False,'runtime_verified':False})
(O/'proposal.json').write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha':sha(final),'proof':proof,'static_users':users,'incremental_users':incremental}))
