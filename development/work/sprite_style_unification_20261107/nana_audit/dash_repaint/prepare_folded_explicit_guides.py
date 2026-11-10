"""Prepare fixed calf axes for a local art correction, never a game output."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,write,digest
from prepare_next_guides import body_path
o=D/'fourth_folded_explicit_inputs_v3';o.mkdir(exist_ok=True);p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());sheet=Image.new('RGBA',(1536,1536));draw=ImageDraw.Draw(sheet)
for k,n in enumerate((71,75)):
 src=np.array(Image.open(D/'fourth_folded_registered_v2'/f'source_rgba8_{n:03}.png').convert('RGBA'));z=src.copy()
 # This near-left shoe belongs to the folded rear shin. The other shoe is
 # already close to the exact base contact and is left untouched.
 box=(-7,19,-3,22);dx=11;dy=-1 if n==71 else 0
 x0,y0,x1,y1=box;patch=src[(y0+40)*8:(y1+40)*8,(x0+40)*8:(x1+40)*8].copy();z[(y0+40)*8:(y1+40)*8,(x0+40)*8:(x1+40)*8]=0
 dst=z[(y0+dy+40)*8:(y1+dy+40)*8,(x0+dx+40)*8:(x1+dx+40)*8];m=patch[:,:,3]>0;dst[m]=patch[m]
 im=Image.fromarray(z);g=ImageDraw.Draw(im);pts=[((-9+40)*8,(18+40)*8),((2+40)*8,(19+dy+40)*8),((5+40)*8,(20+dy+40)*8)];g.line(pts,fill=(20,210,250,255),width=4)
 crop=im.crop((80,224,560,544)).resize((720,480),Image.Resampling.NEAREST);sheet.alpha_composite(crop,(k*768+24,150));draw.text((k*768+25,40),f'EDIT {n}: follow CYAN calf guide; shoes fixed; erase guide.',fill=(110,120,130,255))
 native=a.rgba(np.array(Image.open(body_path(n)))).crop((130,148,190,188)).resize((720,480),Image.Resampling.NEAREST);sheet.alpha_composite(native,(k*768+24,918));draw.text((k*768+25,808),f'POSE CONTACT REFERENCE {n}; bare shins above, NOT these boots',fill=(110,120,130,255))
sheet.save(o/'edit_target.png');write(o/'manifest.json',{'guide_only':True,'image_sha256':digest(o/'edit_target.png'),'not_native_art':True})
