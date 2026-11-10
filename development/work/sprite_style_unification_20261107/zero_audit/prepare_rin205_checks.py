"""독립 소스 재등록 검사를 후속5에 묶고 원MIPS 검사 계획을 만든다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).parent;E=D/'rin_extension';P=E/'prepared_followthrough01';C=hashlib.sha256((P/'PL01_U.ARC').read_bytes()).hexdigest()
s=(D/'verify_rin200_readback.py').read_text('utf8');tail=s[s.index('g,c=entry(old,2)'):]
tail=tail.replace('support={(1,n)for n in (145,146,147,162,164,166,168,170,172,174,176)}','support={(0,198),(1,144),(1,145),(1,147),(1,157),(1,159)}')
tail=tail.replace("counts['authored_exact']==9 and counts['other_display_exact']==427","counts['authored_exact']==5 and counts['other_display_exact']==431")
tail=tail.replace('prepared_ice01','prepared_spin01').replace('rin200_components','rin205_components').replace("'cumulative_authored_refs':200,'incremental_refs':9,'previous191_preserved':True","'cumulative_authored_refs':205,'incremental_refs':5,'previous200_preserved':True").replace('final200_readback_audit','final205_readback_audit')
head='''"""Independent fixed-grid generated/native/ARC check; no producer imports."""
from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
D=Path(__file__).parent/'rin_extension';P=D/'prepared_followthrough01';A=D/'followthrough_registered_v1';sha=lambda b:hashlib.sha256(b).hexdigest()
old=(D/'prepared_spin01/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(old)=='cf0b079549ea6f1968f3eeb8be37541583f070c134a628c7ea5131fc745dee2a';assert sha(new)=='CANDIDATE_SHA'
pal=struct.unpack_from('<16H',entry(old,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
reg=json.loads((A/'registration.json').read_text('utf8'));assert reg['source_arc_sha256']==sha(old)
def fixed_source(folder,key):
 info=json.loads((folder/'inputs.json').read_text('utf8'));f=next(f for f in info['frames']if f['key']==key);im=Image.open(folder/'generated.png').convert('RGBA');cw,ch=im.width/info['columns'],im.height/info['rows'];cx,cy=f['cell'];crop=im.crop((round(cx*cw),round(cy*ch),round((cx+1)*cw),round((cy+1)*ch)));v=np.array(crop);near=np.zeros(v.shape[:2],np.uint8)
 for y in range(v.shape[0]):near[y]=1+np.sum((v[y,:,:3,None].transpose(0,2,1).astype(np.int32)-colors[None,:,:])**2,axis=2).argmin(1)
 votes=np.stack([np.array(Image.fromarray(np.where(near==i,v[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)]);alpha=np.array(crop.getchannel('A').resize((96,96),Image.Resampling.BOX));cell=np.where(alpha>=128,votes.argmax(0)+1,0).astype(np.uint8);a=np.zeros((384,384),np.uint8);x0,y0,x1,y1=info['crop'];a[y0:y1,x0:x1]=cell;return a
g1=D/'followthrough01';g2=D/'followthrough_contacts_fix01'
assert sha((g1/'generated.png').read_bytes())==reg['original_new_art_sha256']=='039e810e08a9a50b51746f96da7ca3b4149ae9cd10c7ae70b538fc536148f6cf'
assert sha((g2/'generated.png').read_bytes())==reg['source_generated_sha256']=='7e66e058b6c6ad73c2495e49c899501182f5dea2c7344ab5013ef6d5a8faeadc'
generic=json.loads((g1/'native/registration.json').read_text('utf8'));anchored=json.loads((g1/'anchor_probe/report.json').read_text('utf8'));masters={};provenance=[]
for r in reg['records']:
 key=r['key'];b,n=r['bank'],r['ref'];a=fixed_source(g1,key);gr=next(q for q in generic['records']if q['key']==key);ar=next(q for q in anchored['rows']if q['key']==key);dx=gr['translate'][0]+ar['translation_from_generic'][0];dy=gr['translate'][1]+ar['translation_from_generic'][1];a=np.roll(a,(dy,dx),(0,1));source=ROOT/r['source_native'];assert sha(source.read_bytes())==r['source_native_sha256'];assert np.array_equal(a,np.array(Image.open(source)))
 lower=fixed_source(g2,key);lp=ROOT/r['lower_source_native'];assert sha(lp.read_bytes())==r['lower_source_native_sha256'];assert np.array_equal(lower,np.array(Image.open(lp)))
 z=a.copy();x0,y0,x1,y1=r['lower_region'];m=np.zeros(z.shape,bool);m[y0:y1,x0:x1]=True;z[m]=lower[m]
 for op in r['contact_translations']:
  x0,y0,x1,y1=op['box'];dx,dy=op['translation'];cut=z[y0:y1,x0:x1].copy();z[y0:y1,x0:x1]=0;z[y0+dy:y1+dy,x0+dx:x1+dx]=cut
  if op['retain_source_top_seam_row']:z[y0,x0:x1]=cut[0]
 assert np.array_equal(z[~m],a[~m]);p=A/(key+'_indices.png');assert sha(p.read_bytes())==r['output_sha256'];assert np.array_equal(z,np.array(Image.open(p)));assert not r['old_head_or_body_override']and not r['invented_color'];assert np.nonzero(z)[0].max()==np.nonzero(render(old,b,b*5,n)[0])[0].max();masters[b,n]=z
 provenance.append({'key':key,'new_upper_quantization_translation_exact':True,'new_lower_quantization_registration_exact':True,'outside_lower_region_exact':True,'floor_y':int(np.nonzero(z)[0].max()),'registered_sha256':sha(p.read_bytes())})
targets=dict(masters);assert np.array_equal(render(old,0,0,197)[0],render(old,0,0,212)[0]);targets[0,212]=masters[0,197].copy()
'''.replace('CANDIDATE_SHA',C)
(D/'verify_rin205_readback.py').write_text(head+tail,'utf8')
plan=json.loads((E/'rin200_components.json').read_text('utf8'));r=plan['resources']['PL01_U.ARC'];r['path']='work/sprite_style_unification_20261107/zero_audit/rin_extension/prepared_followthrough01/PL01_U.ARC';r['after']=C
(E/'rin205_components.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
s=(D/'check_rin200_guards.py').read_text('utf8').replace('pack_rin_spin02','pack_rin_followthrough01').replace('rin200','rin205')
s=s.replace('missing144','missing146').replace('extra147','extra147').replace('altered161','altered156').replace('changed_support162','changed_support157').replace('changed_alias165','changed_alias212')
s=s.replace('del t[1,144]','del t[1,146]').replace('t[1,144].copy()','t[1,146].copy()').replace('t[1,161]','t[1,156]').replace('t[1,162]','t[1,157]').replace('t[1,165]=t[1,156].copy()','t[0,212]=t[1,156].copy()')
(D/'check_rin205_guards.py').write_text(s,'utf8');print(C)
