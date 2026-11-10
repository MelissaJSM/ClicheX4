"""Check both modular body forms against original signed muzzle coordinates."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper
from scripts.c01_audio_build import read_disc
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((D/'input_audit.json').read_text('utf8'));a=Archive((ROOT/m['input']['path']).read_bytes());data,_=read_disc(ROOT/'MegaMan X4.bin',['SLUS_005.61']);exe=data['SLUS_005.61'];off=lambda x:x-0x80010000+2048
coords=json.loads((N/'base_hover_shot_support01/inputs_a01/manifest.json').read_text('utf8'))['canonical_source_texels'];fxpath=W/'zero_audit/nana_ultimate_hover_muzzle01/lemon_first_frame.npy';fx=np.load(fxpath);assert int((fx>0).sum())==188
out=D/'final_muzzle_probe01';out.mkdir(exist_ok=False);frames=[]
for n,expected in [(222,(-27,-9)),(224,(-29,-8)),(226,(-20,-10)),(228,(-17,-10)),(230,(-24,-11))]:
 ox,oy=struct.unpack_from('<bb',exe,off(0x8011b230+n*2));assert(ox,oy)==expected;gun=np.zeros((384,384),np.uint8)
 for x,y,v in coords:gun[y+oy+9+160,x+ox+23+160]=v
 ls={pb:np.array(Image.open(D/f'shoot_layers_probe02/layer{pb}_{n}.png'))for pb in(0,5,6,7,8)};rows=[]
 for form,mask in [('base_legs',8),('fourth',15)]:
  pic=a.rgba(ls[0]);z=ls[0].copy()
  for bit,pb in((8,8),(1,5),(4,7),(2,6)):
   if mask&bit:pic.alpha_composite(a.rgba(ls[pb],32 if pb==7 else 16));z[ls[pb]>0]=ls[pb][ls[pb]>0]
  assert z[oy-1+160,ox+1+160]==gun[oy-1+160,ox+1+160]>0 and z[oy+160,ox+1+160]==gun[oy+160,ox+1+160]>0
  effect=np.roll(np.roll(fx,oy,axis=0),ox,axis=1);neutral=np.zeros((384,384,4),np.uint8);neutral[effect>0]=(255,210,30,125);merge=Image.fromarray(neutral);merge.alpha_composite(pic);draw=ImageDraw.Draw(merge);draw.line((160+ox-1,160+oy,160+ox+1,160+oy),fill='#00eeff')
  rows.append((f'{form} {n} / original muzzle {ox},{oy}',[('idle',a.composite(0,0 if mask==8 else 15)[0]),('new final layers',pic),('original188 neutral effect',merge)]));frames.append({'ref':n,'form':form,'original_origin':[ox,oy],'actual_two_barrel_rows_exact':True,'components8':int(label(z>0,np.ones((3,3)))[1]),'original_first_flash_overlap':int(((effect>0)&(z>0)).sum()),'effect_origin_changed':False})
 helper.grid(rows,out/f'muzzle_{n}.png',6)
(out/'manifest.json').write_text(json.dumps({'exe_sha256':hashlib.sha256(exe).hexdigest(),'original_muzzle_function_sha256':hashlib.sha256(exe[off(0x80092e2c):off(0x80092f08)]).hexdigest(),'original_first_flash_sha256':sha(fxpath),'frames':frames,'neutral_effect_not_actual_CLUT':True,'native_or_gameplay_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print('10 final layer figures original signed muzzle + two barrel rows checked')
