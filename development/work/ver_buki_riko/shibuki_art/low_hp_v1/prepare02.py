import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_idle import breathe
from scripts.extract_zero import save_image
from scripts.solve_sprite_cover import cover
d=Path(__file__).parent;a=d/'production02';a.mkdir(exist_ok=True);source=d/'production01';art=json.loads((source/'art.json').read_text());pal=art['palette_words'];raw=np.array(Image.open(source/'frame_120.png'));base=np.zeros_like(raw);base[:,:-1]=raw[:,1:];opened=base.copy();sample=np.array(Image.open(source/'frame_122.png'));assert int(base[32,42])==13;opened[32,42]=sample[32,44];assert opened[32,42]==11
records=[];layouts=[];sheet=Image.new('RGB',(4*288,2*264),'#28394b');dr=ImageDraw.Draw(sheet)
for i,(n,delta) in enumerate([(120,1),(122,0),(124,-1)]):
 for row,src in enumerate((base,opened)):
  arr=np.zeros_like(base);arr[15:63,24:72]=breathe(src[15:63,24:72],delta);save_image(arr.tobytes(),(96,80),pal,a/f'frame_{n+row:03d}.png');records.append({'frame':n+row,'image':f'frame_{n+row:03d}.png','source':'generated.png, first pose; second pose mouth sample','breathing_delta':delta,'mouth_open':bool(row)});im=Image.open(a/f'frame_{n+row:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);x=(i+1)*288;y=row*264;sheet.paste(im,(x,y+24),im);dr.text((x+8,y+5),str(n+row),fill='white')
  assert np.array_equal(arr[58:],base[58:])
  if row==0:q=cover(arr!=0,7,10);q.update(frame=n);layouts.append(q);print(q,flush=True)
for row in range(2):
 im=Image.open(d.parent/'standing_buster_v1/parent_000.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,(0,row*264+24),im);dr.text((8,row*264+5),'ACCEPTED IDLE',fill='white')
sheet.save(a/'body_review.png');(a/'art.json').write_text(json.dumps({'palette_words':pal,'source_inventory':art['source_inventory'],'frames':records},indent=2));(a/'layout.json').write_text(json.dumps(layouts,indent=2))
frames=[]
for n in (120,122,124):
 arr=np.array(Image.open(a/f'frame_{n:03d}.png'));im=save_image(arr.tobytes(),(96,80),pal,a/f'gif_{n:03d}.png').convert('RGBA');bg=Image.new('RGBA',im.size,'#28394b');bg.alpha_composite(im);frames.append(bg.resize((384,320),Image.Resampling.NEAREST))
frames=[frames[1],frames[0],frames[1],frames[2]];frames[0].save(a/'breathing_preview.gif',save_all=True,append_images=frames[1:],duration=[200,234,200,234],loop=0)
