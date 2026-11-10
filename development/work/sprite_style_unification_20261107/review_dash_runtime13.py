"""Review actual bounded dash clips with the encoded WebP timing."""
from pathlib import Path
import argparse,json,hashlib,math
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--crop',type=int,nargs=4,default=[0,150,440,560]);p.add_argument('--output-suffix',default='_review');a=p.parse_args()
R=Path(__file__).resolve().parent/'runtime';play=R/(a.name+'_play');out=R/(a.name+a.output_suffix);assert not out.exists();out.mkdir()
e=json.loads((play/'evidence.json').read_text('utf8'));im=Image.open(play/'play.webp')
times=[]
for n in range(im.n_frames):im.seek(n);im.load();times.append(im.info['timestamp']/1000)
groups={'ground_right':(.9,2.2),'ground_left':(4.9,6.2),'air_right':(8.9,10.3),'air_left':(12.9,14.3),'fire_right':(16.9,18.4),'fire_left':(21.9,23.4)}
pages=[];box=tuple(a.crop);cw,ch=box[2]-box[0],box[3]-box[1]
assert 0<=box[0]<box[2]<=800 and 0<=box[1]<box[3]<=600
for name,(lo,hi) in groups.items():
    nums=[n for n,t in enumerate(times) if lo<=t<=hi][::2]
    for start in range(0,len(nums),6):
        group=nums[start:start+6];board=Image.new('RGB',(cw*2,(ch+24)*math.ceil(len(group)/2)),'#202630');draw=ImageDraw.Draw(board)
        for j,n in enumerate(group):
            im.seek(n);f=im.convert('RGB');x,y=j%2*cw,j//2*(ch+24);board.paste(f.crop(box),(x,y+24));draw.text((x+4,y+5),f'{name} WebP{n} / {times[n]:.3f}s',fill='white')
        path=out/f'{name}_{start//6:02}.png';board.save(path)
        pages.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'webp_indices':group,'actual_times':[times[n] for n in group]})
(out/'manifest.json').write_text(json.dumps({'source':str(play/'play.webp'),'source_sha256':hashlib.sha256((play/'play.webp').read_bytes()).hexdigest(),'captures':e['frames'],'encoded_webp_frames':im.n_frames,'actual_window_crops':True,'simulated':False,'timestamps_from':'decoded WebP, not unmerged capture indices','pages':pages},indent=2)+'\n','utf8')
print(json.dumps({'pages':len(pages),'captures':e['frames'],'encoded':im.n_frames}))
