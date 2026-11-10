"""Crop actual recorded hurt windows, aligning observer and recorder clocks."""
from pathlib import Path
import argparse,json,hashlib,math
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('name');a=p.parse_args()
R=Path(__file__).resolve().parent/'runtime';play=R/(a.name+'_play');watch=R/(a.name+'_watch');out=R/(a.name+'_hurt_review')
assert not out.exists();out.mkdir()
read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rec=read(play/'evidence.json');obs=read(watch/'evidence.json')
delta=(int(rec['record_start_monotonic_ns'])-int(obs['watch_start_monotonic_ns']))/1e9
hits=[e for e in obs['events'] if 106<=e['frame']<=114 or 233<=e['frame']<=236]
ts=sorted(e['first_seen_seconds']-delta for e in hits);clusters=[]
for t in ts:
 if not clusters or t-clusters[-1][-1]>.5:clusters.append([t])
 else:clusters[-1].append(t)
im=Image.open(play/'play.webp');times=[]
for n in range(im.n_frames):im.seek(n);im.load();times.append(im.info['timestamp']/1000)
groups={'context':[0,im.n_frames-1]}
for j,c in enumerate(clusters):groups[f'hurt{j:02}']=[n for n,t in enumerate(times) if max(0,c[0]-.3)<=t<=c[-1]+.4]
pages=[];cw,ch=800,400
for name,nums in groups.items():
 for start in range(0,len(nums),6):
  group=nums[start:start+6];board=Image.new('RGB',(cw*2,(ch+24)*math.ceil(len(group)/2)),'#202630');draw=ImageDraw.Draw(board)
  for j,n in enumerate(group):
   im.seek(n);frame=im.convert('RGB');x,y=j%2*cw,j//2*(ch+24)
   board.paste(frame.crop((0,200,800,600)),(x,y+24));draw.text((x+4,y+5),f'{name} WebP{n} / {times[n]:.3f}s',fill='white')
  path=out/f'{name}_{start//6:02}.png';board.save(path)
  pages.append({'path':path.as_posix(),'sha256':sha(path),'webp_indices':group,'actual_times':[times[n] for n in group]})
data={'source':(play/'play.webp').as_posix(),'source_sha256':sha(play/'play.webp'),'captures':rec['frames'],'encoded_webp_frames':im.n_frames,
 'observer_recorder_delta_seconds':delta,'hurt_refs_seen':sorted(set(e['frame'] for e in hits)),
 'actual_window_crops':True,'simulated':False,'crop':[0,200,800,600],'timestamps_from':'decoded WebP with observer/recorder monotonic alignment','pages':pages}
(out/'manifest.json').write_text(json.dumps(data,indent=2)+'\n','utf8');print(json.dumps({'pages':len(pages),'refs':data['hurt_refs_seen'],'directory':str(out)}))
