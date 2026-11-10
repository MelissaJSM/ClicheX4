import json,math
from pathlib import Path
from PIL import Image,ImageDraw
root=Path('work/sprite_style_unification_20261107/runtime')
play=root/'riko_ground_play01'
out=root/'riko_ground_play01_review';out.mkdir(exist_ok=False)
d=json.loads((play/'evidence.json').read_text('utf8'))
im=Image.open(play/'play.webp')
groups={'ground_combo':(1.45,2.75),'run':(3.25,3.9),'jump_saber':(5.25,6.25),'left_combo':(6.95,8.15),'dash_jump':(12.95,14.95)}
pages=[]
for name,(lo,hi) in groups.items():
 ids=[i for i,t in enumerate(d['capture_times'])if lo<=t<=hi]
 for part,start in enumerate(range(0,len(ids),16)):
  selected=ids[start:start+16]
  board=Image.new('RGB',(1000,324*math.ceil(len(selected)/4)),'#202630');draw=ImageDraw.Draw(board)
  for j,index in enumerate(selected):
   im.seek(index);frame=im.convert('RGB')
   # Actual 800x600 client capture, no sprite repainting/resampling/filter.
   crop=frame.crop((230,200,480,500))
   x,y=j%4*250,j//4*324;board.paste(crop,(x,y+24))
   draw.text((x+4,y+5),f'{name} {index} / {d["capture_times"][index]:.3f}s',fill='white')
  dest=out/f'{name}_{part:02}.png';board.save(dest)
  pages.append({'path':dest.as_posix(),'window_indices':selected})
(out/'manifest.json').write_text(json.dumps({'source':(play/'play.webp').as_posix(),'actual_window_crops':True,'sprite_pixels_edited':False,'pages':pages},indent=2)+'\n','utf8')
print(json.dumps({'pages':len(pages),'out':str(out)}))
