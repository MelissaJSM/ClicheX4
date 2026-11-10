"""Crop recorded selection sprites; use WebP timing after duplicate-frame merging."""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image, ImageDraw
p=argparse.ArgumentParser();p.add_argument('play',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
assert not a.output.exists()
a.output.mkdir()
v=Image.open(a.play/'play.webp')
e=json.loads((a.play/'evidence.json').read_text('utf8'))
chosen=list(range(0,v.n_frames,2));pages=[]
for start in range(0,len(chosen),16):
    nums=chosen[start:start+16];b=Image.new('RGB',(1280,824),'#1b212a');d=ImageDraw.Draw(b);rows=[]
    for k,n in enumerate(nums):
        v.seek(n);f=v.convert('RGB');assert f.size==(800,600)
        ms=v.info['timestamp'];duration=v.info['duration']
        x=(k%4)*320;y=(k//4)*206
        b.paste(f.crop((20,300,180,480)),(x,y+24))
        b.paste(f.crop((640,300,800,480)),(x+160,y+24))
        d.text((x+3,y+4),f'WebP {n}: {ms/1000:.3f}s',fill='white')
        rows.append({'webp_index':n,'webp_timestamp_ms':ms,'duration_ms':duration})
    q=a.output/f'selection_{start//16:02}.png';b.save(q)
    pages.append({'path':q.as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'samples':rows})
proof={'source':str(a.play/'play.webp'),'source_sha256':hashlib.sha256((a.play/'play.webp').read_bytes()).hexdigest(),
       'recorded_window_frames':e['frames'],'encoded_webp_frames':v.n_frames,
       'timestamps_from':'Decoded WebP timing; adjacent identical captures can merge into one encoded frame.',
       'actual_window_crops':True,'simulated':False,'pages':pages}
(a.output/'manifest.json').write_text(json.dumps(proof,indent=2)+'\n','utf8')
print(json.dumps({'pages':len(pages),'captures':e['frames'],'webp_frames':v.n_frames}))
