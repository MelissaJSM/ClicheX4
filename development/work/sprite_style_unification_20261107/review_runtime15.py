"""Make actual-window contact sheets using decoded timestamps."""
from pathlib import Path
import argparse,json,hashlib,math
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;R=W/'runtime'
p=argparse.ArgumentParser();p.add_argument('name',choices=['rin_arrival15','rin_burst15','rin_dash_follow15']);p.add_argument('--arrival-detail',action='store_true');a=p.parse_args()
play=R/(a.name+'_play');out=R/(a.name+('_detail' if a.arrival_detail else '_review'));assert not out.exists();out.mkdir()
e=json.loads((play/'evidence.json').read_text('utf8'));im=Image.open(play/'play.webp');times=[]
for n in range(im.n_frames):im.seek(n);im.load();times.append(im.info['timestamp']/1000)
if a.arrival_detail:
    assert a.name=='rin_arrival15'
    groups={'arrival':(8.3,9.6)};step=1;box=(150,290,350,560)
elif a.name=='rin_burst15':
    groups={f'burst_{i}':(at-.1,at+1.8) for i,at in enumerate((1,6,11,16))};step=1;box=(0,160,480,560)
elif a.name=='rin_dash_follow15':
    groups={f'dash_{i}':(at-.1,at+1.4) for i,at in enumerate((2,6,10,14))}
    groups.update({'ryuen_left':(17,18.5),'ryuen_right':(20,21.5)});step=2;box=(0,80,800,560)
else:
    groups={'overview':(0,20)};step=8;box=(0,0,800,600)
pages=[];cw,ch=box[2]-box[0],box[3]-box[1]
for name,(lo,hi) in groups.items():
    nums=[n for n,t in enumerate(times) if lo<=t<=hi][::step]
    for start in range(0,len(nums),6):
        selected=nums[start:start+6];board=Image.new('RGB',(cw*2,(ch+24)*math.ceil(len(selected)/2)),'#202630');draw=ImageDraw.Draw(board)
        for j,n in enumerate(selected):
            im.seek(n);x,y=j%2*cw,j//2*(ch+24);board.paste(im.convert('RGB').crop(box),(x,y+24));draw.text((x+4,y+5),f'{name} WebP{n} / {times[n]:.3f}s',fill='white')
        path=out/f'{name}_{start//6:02}.png';board.save(path);pages.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'webp_indices':selected,'actual_times':[times[n] for n in selected]})
(out/'manifest.json').write_text(json.dumps({'source':str(play/'play.webp'),'source_sha256':hashlib.sha256((play/'play.webp').read_bytes()).hexdigest(),'captures':e['frames'],'encoded_webp_frames':im.n_frames,'actual_window_crops':True,'simulated':False,'crop':box,'timestamps_from':'decoded WebP','pages':pages},indent=2)+'\n','utf8')
print(json.dumps({'pages':len(pages),'captures':e['frames'],'encoded':im.n_frames}))
