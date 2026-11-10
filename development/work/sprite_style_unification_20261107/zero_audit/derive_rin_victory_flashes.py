"""Reproduce the existing departure rule, then synchronize it with new pose3."""
from pathlib import Path
import sys,json,hashlib,struct,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';ART=D/'victory_registered_v1';P=D/'prepared_rising_rear_v1/PL01_U.ARC';O=D/'victory_targets_v1';assert not O.exists();O.mkdir();arc=P.read_bytes();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(P)=='223e553f97ecc85d52b085f3e0e6cd46ecc914063f1adcef43fd1d34c25d298e'
def derive(a,n):
 radius=1 if n==7 else 2;out=np.zeros_like(a);mask=a>0
 for dy in range(-radius,radius+1):
  for dx in range(-radius,radius+1):
   if abs(dx)+abs(dy)<=radius:out[np.roll(np.roll(mask,dy,0),dx,1)]=11 if n==7 else 10
 pale=np.array([0,10,10,10,11,11,10,11,11,11,10,10,11,10,11,11],np.uint8);out[mask]=a[mask]if n==7 else pale[a[mask]];return out
registration=json.loads((ART/'registration.json').read_text('utf8'));records=[]
for r in registration['records']:
 p=ART/(r['key']+'_indices.png');assert sha(p)==r['after_sha256'];shutil.copyfile(p,O/p.name);records.append({'key':r['key'],'kind':'new_authored','source':str(p.relative_to(ROOT)),'sha256':sha(p)})
old=render(arc,1,5,3)[0];new=np.array(Image.open(O/'b1_003_indices.png'));pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
for n in(7,8):
 assert np.array_equal(derive(old,n),render(arc,1,5,n)[0]);v=derive(new,n);p=O/f'b1_{n:03}_indices.png';Image.fromarray(v).save(p);records.append({'key':f'b1_{n:03}','kind':'derived_departure_flash','source':'b1_003','source_sha256':sha(O/'b1_003_indices.png'),'sha256':sha(p),'radius_manhattan':1 if n==7 else 2,'original_rule_reproduction_error_pixels':0})
for form,words in[('normal',pal),('black',black)]:page([(f'{n} before',rgba(render(arc,1,5,n)[0],words))for n in(3,7,8)]+[(f'{n} new body/flash',rgba(np.array(Image.open(O/f'b1_{n:03}_indices.png')),words))for n in(3,7,8)],rgba(render(arc,0,0,147)[0],words),O/f'{form}_departure.png',cols=3,scale=5)
(O/'targets.json').write_text(json.dumps({'source_arc':str(P.relative_to(ROOT)),'source_sha256':sha(P),'records':records,'registration':str((ART/'registration.json').relative_to(ROOT)),'registration_sha256':sha(ART/'registration.json'),'body_refs':[1,2,3,4,6],'derived_flash_refs':[7,8],'new_pixels_flat_filled_for_body':False,'effect_rule':'현재 섬광을 기존 수식으로 완전히 재현한 뒤 새3에 같은 수식 적용','runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({r['key']:r['sha256']for r in records}))
