from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
play=R/'red_rin15_play';out=R/'red_rin15_review';assert not out.exists();out.mkdir()
im=Image.open(play/'play.webp');e=json.loads((play/'evidence.json').read_text('utf8'));times=[]
for i in range(im.n_frames):im.seek(i);im.load();times.append(im.info['timestamp']/1000)
groups={'ground_combo':(1.45,2.75),'run':(3.25,4.9),'jump_saber':(5.25,6.25),'left_combo':(6.95,8.15),'right_jump_saber':(10,11.4),'dash_jump':(12.95,14.95)}
pages=[];box=(0,180,560,560);cw,ch=560,380
for name,(lo,hi) in groups.items():
 ids=[i for i,t in enumerate(times) if lo<=t<=hi][::2]
 for start in range(0,len(ids),6):
  nums=ids[start:start+6];board=Image.new('RGB',(cw*2,(ch+24)*math.ceil(len(nums)/2)),'#202630');d=ImageDraw.Draw(board)
  for j,i in enumerate(nums):
   im.seek(i);x,y=j%2*cw,j//2*(ch+24);board.paste(im.convert('RGB').crop(box),(x,y+24));d.text((x+4,y+5),f'{name} WebP{i} / {times[i]:.3f}s',fill='white')
  p=out/f'{name}_{start//6:02}.png';board.save(p);pages.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(out/'manifest.json').write_text(json.dumps({'pages':pages,'captures':e['frames'],'encoded_frames':im.n_frames,'times_from':'decoded WebP','actual_window_crops':True},indent=2)+'\n','utf8')
print(json.dumps({'pages':len(pages),'captures':e['frames'],'encoded_frames':im.n_frames}))
