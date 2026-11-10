"""Review sheets from recorded windows using decoded WebP timestamps."""
from pathlib import Path
import json,hashlib,math,argparse
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
p=argparse.ArgumentParser();p.add_argument('--name',default='nana_fourth_rising16');a=p.parse_args()
assert a.name in ('nana_fourth_rising16','nana_base_rising16')
play=R/(a.name+'_play');out=R/(a.name+'_review');assert not out.exists();out.mkdir()
im=Image.open(play/'play.webp');e=json.loads((play/'evidence.json').read_text('utf8'));times=[]
for i in range(im.n_frames):im.seek(i);im.load();times.append(im.info['timestamp']/1000)
groups={'normal_right':(1,1.9),'jump_right':(3.15,4.1),'charged_right':(7.75,8.8),
        'normal_left':(11,11.9),'charged_left':(14.75,15.8),'jump_left':(18.15,19.1)}
if a.name=='nana_base_rising16':groups={'normal_right':(1,1.9),'jump_right':(3.15,4.1),'normal_left':(6,6.9),'jump_left':(8.15,9.1)}
pages=[];box=(120,40,470,560);cw,ch=350,520
for name,(lo,hi) in groups.items():
    ids=[i for i,t in enumerate(times) if lo<=t<=hi]
    for start in range(0,len(ids),9):
        nums=ids[start:start+9];board=Image.new('RGB',(cw*3,(ch+24)*math.ceil(len(nums)/3)),'#202630');d=ImageDraw.Draw(board)
        for j,i in enumerate(nums):
            im.seek(i);x,y=j%3*cw,j//3*(ch+24);board.paste(im.convert('RGB').crop(box),(x,y+24))
            d.text((x+4,y+5),f'{name} WebP{i} / {times[i]:.3f}s',fill='white')
        q=out/f'{name}_{start//9:02}.png';board.save(q);pages.append({'path':q.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
(out/'manifest.json').write_text(json.dumps({'pages':pages,'captures':e['frames'],'encoded_frames':im.n_frames,
    'times_from':'decoded WebP','actual_window_crops':True,'sprite_pixels_edited':False,'resampled':False},indent=2)+'\n','utf8')
print(json.dumps({'pages':len(pages),'captures':e['frames'],'encoded_frames':im.n_frames}))
