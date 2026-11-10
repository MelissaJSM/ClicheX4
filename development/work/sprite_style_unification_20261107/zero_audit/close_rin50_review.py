from pathlib import Path
import sys,json,hashlib,struct,copy
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent/'rin_extension'
from scripts.build_sprite_style_unification import check_static_body
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
P=D/'prepared_priority_final_v2';B=D/'prepared_air_continuation2_v2';old=(B/'PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();O=D/'rin50_guard_review';O.mkdir(exist_ok=True)
j=json.loads((P/'proposal.json').read_text('utf8'));bound=j['static_body_patch'];positive=check_static_body(old,new,bound)
negative=[]
for case in('wrong_declared_ref','empty_scope','outside_scope','wrong_recipe_hash'):
 folder=O/case;folder.mkdir(exist_ok=True);r=json.loads((P/'static_effects.json').read_text('utf8'))
 for name in('palette.bin','effect_23.png','effect_24.png'):(folder/name).write_bytes((P/name).read_bytes())
 if case=='wrong_declared_ref':r['expected_changed_references']=[[6,23]]
 elif case=='empty_scope':r['expected_changed_references']=[]
 elif case=='outside_scope':r['expected_changed_references']=[[6,25]]
 file=folder/'static_effects.json';file.write_text(json.dumps(r,indent=2)+'\n','utf8');b={'recipe':str(file.relative_to(ROOT)),'sha256':sha(file.read_bytes())if case!='wrong_recipe_hash'else'0'*64}
 try:check_static_body(old,new,b)
 except ValueError as exc:negative.append({'case':case,'reason':str(exc)})
 else:raise AssertionError('Unsafe static binding accepted: '+case)
pal=struct.unpack_from('<16H',entry(new,9));sheet=Image.new('RGB',(1200,856),'#626c78');draw=ImageDraw.Draw(sheet);comparisons=[]
for row,blob in enumerate((old,new)):
 for col,n in enumerate((182,184,185)):
  a=render(blob,1,5,n)[0];pic=rgba(a,pal).crop((120,120,200,192)).resize((400,360),Image.Resampling.NEAREST);sheet.paste(pic,(col*400,row*428+30),pic);draw.text((col*400+8,row*428+8),f'{n} '+('previous'if row==0 else'candidate'),fill='white')
for n in(183,184,185):
 a=render(old,1,5,182)[0];b=render(old,1,5,n)[0];diff=a!=b;y,x=np.nonzero(diff);comparisons.append({'ref':n,'original_difference_to182':int(diff.sum()),'difference_bounds':[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]if len(x)else None})
sheet.save(O/'burst_sequence_transition.png')
result={'passed':True,'positive':positive,'negative':negative,'candidate_sha256':sha(new),'recipe_hash_before_after':bound['sha256'],'recipe_unchanged':sha((P/'static_effects.json').read_bytes())==bound['sha256'],'burst_original_differences':comparisons,'user_accepted':False,'runtime_verified':False}
(O/'guard_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(result))
