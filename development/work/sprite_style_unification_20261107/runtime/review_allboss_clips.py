import json,math
from pathlib import Path
from PIL import Image,ImageDraw
R=Path('work/sprite_style_unification_20261107/runtime')
groups={
 '01':{'combo':(1.45,2.70,(150,160,470,560)), 'spin':(13.20,13.70,(150,160,470,560)), 'rakuhouha':(15.48,16.85,(150,160,470,560)), 'raijingeki':(18,19.75,(150,160,470,560))},
 '02':{'ryuenjin':(1.55,3.10,(230,40,550,560)), 'ice':(4.30,5.30,(230,40,550,560)), 'dash_slash':(7.5,9,(280,160,600,560)), 'left_ryuenjin':(11,12.65,(230,40,550,560))}
}
manifest=[]
for clip,sets in groups.items():
 play=R/f'riko_allboss_play{clip}';out=R/f'riko_allboss_play{clip}_review';out.mkdir(exist_ok=False)
 d=json.loads((play/'evidence.json').read_text('utf8'));im=Image.open(play/'play.webp')
 for name,(lo,hi,box) in sets.items():
  ids=[i for i,t in enumerate(d['capture_times'])if lo<=t<=hi]
  for part,start in enumerate(range(0,len(ids),12)):
   selected=ids[start:start+12];cw,ch=box[2]-box[0],box[3]-box[1]
   board=Image.new('RGB',(cw*4,(ch+24)*math.ceil(len(selected)/4)),'#202630');draw=ImageDraw.Draw(board)
   for j,index in enumerate(selected):
    im.seek(index);crop=im.convert('RGB').crop(box);x,y=j%4*cw,j//4*(ch+24)
    board.paste(crop,(x,y+24));draw.text((x+4,y+5),f'{name} frame{index} / {d["capture_times"][index]:.3f}s',fill='white')
   dest=out/f'{name}_{part:02}.png';board.save(dest)
   manifest.append({'path':dest.as_posix(),'source':(play/'play.webp').as_posix(),'indices':selected,'crop':box})
(R/'riko_allboss_review_manifest.json').write_text(json.dumps({'actual_window_crops':True,'sprite_pixels_edited':False,'pages':manifest},indent=2)+'\n','utf8')
print(json.dumps({'pages':len(manifest)}))
