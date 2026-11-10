from pathlib import Path
import json,math,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;name='nana_fourth_arrival30';play=R/(name+'_play');watch=R/(name+'_watch');out=R/(name+'_review');assert not out.exists();out.mkdir()
read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rec=read(play/'evidence.json');obs=read(watch/'evidence.json')
delta=(int(rec['record_start_monotonic_ns'])-int(obs['watch_start_monotonic_ns']))/1e9
lo,hi=8.2-delta,10.1-delta;ids=[i for i,t in enumerate(rec['capture_times'])if lo<=t<=hi]
im=Image.open(play/'play.webp');pages=[];box=(150,200,400,550);cw,ch=250,350
for part,start in enumerate(range(0,len(ids),12)):
 selected=ids[start:start+12];board=Image.new('RGB',(cw*4,(ch+24)*math.ceil(len(selected)/4)),'#202630');draw=ImageDraw.Draw(board)
 for j,index in enumerate(selected):
  t=rec['capture_times'][index];im.seek(index);x,y=j%4*cw,j//4*(ch+24);board.paste(im.convert('RGB').crop(box),(x,y+24))
  event=next((e for e in reversed(obs['events'])if e['first_seen_seconds']<=t+delta),None)
  tag=f"ref{event['frame']} mask{event['armor']}"if event else 'no sample'
  draw.text((x+4,y+5),f'#{index} {t:.3f}s approx {tag}',fill='white')
 p=out/f'arrival_{part:02}.png';board.save(p);pages.append({'path':p.as_posix(),'sha256':sha(p),'window_indices':selected,'crop':list(box)})
(out/'manifest.json').write_text(json.dumps({'source':(play/'play.webp').as_posix(),'source_sha256':sha(play/'play.webp'),'observer_sha256':sha(watch/'evidence.json'),'actual_window_crops':True,'sprite_pixels_edited':False,'resampled':False,'observer_time_minus_capture_time':delta,'labels_are_nearest_previous_readonly_sample_not_atomic_frame_identity':True,'pages':pages},indent=2)+'\n','utf8');print(json.dumps({'pages':len(pages),'window_images':len(ids),'delta':delta}))
