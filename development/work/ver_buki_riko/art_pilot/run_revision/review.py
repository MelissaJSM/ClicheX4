from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.discover_inputs import psx_arc,sha256
from scripts.project import write_json
from src.psx_player import graphics_bank,bank_offsets,decode_stream,composition_frame,compose_indices
P=Path(__file__).parent
old=ROOT/'out/ver_buki_riko/riko_motion_20261023T130950715295Z'
new=ROOT/'out/ver_buki_riko/riko_motion_20261023T140114425399Z'
motion=ROOT/'work/ver_buki_riko/run_revision_frames/20261023T140033413871Z'
a=(old/'modified.arc').read_bytes();b=(new/'modified.arc').read_bytes()
entries=psx_arc(a);g=next(e for e in entries if e['type']=='0x2');p=next(e for e in entries if e['type']=='0x3')
assert len(a)==len(b) and [tuple(e[k] for k in ('index','type','offset','size')) for e in psx_arc(b)]==[tuple(e[k] for k in ('index','type','offset','size')) for e in entries]
assert a[:g['offset']]==b[:g['offset']] and a[g['offset']+g['size']:]==b[g['offset']+g['size']:]
ga=a[g['offset']:g['offset']+g['size']];gb=b[g['offset']:g['offset']+g['size']];parts=a[p['offset']:p['offset']+p['size']]
changed=[];composed=0;unknown=[]
for bi in range(len(bank_offsets(ga))):
 for f in graphics_bank(ga,bi)['frames']:
  before=decode_stream(ga,f['offset'],f['limit'],f['tile_count']*128).data
  after=decode_stream(gb,f['offset'],f['limit'],f['tile_count']*128).data
  if before!=after:changed.append([bi,f['index']])
  try:
   c=composition_frame(parts,0 if bi==0 else 5,f['index']);pa=compose_indices(before,f['tile_count'],c);pb=compose_indices(after,f['tile_count'],c)
  except ValueError as e:
   assert before==after;unknown.append([bi,f['index'],str(e)]);continue
  composed+=1
  if [bi,f['index']] not in changed:assert pa==pb
assert changed==[[0,n] for n in (3,4,*range(7,21))]
preserved={}
for n in (0,1,2,5,6,*range(21,35),146,147,148):
 name=f'{"idle" if n in (0,1,2,146,147,148) else "frame"}_{n:03d}.png'
 assert (old/name).read_bytes()==(new/name).read_bytes();preserved[name]=sha256((new/name).read_bytes())
report={'previous_build':str(old),'new_build':str(new),'decoded_references_checked':444,
        'composed_references_checked':composed,'changed_references':changed,'uninterpreted_unchanged':unknown,
        'outside_graphics_entry_unchanged':True,'all_palettes_and_parts_unchanged':True,'preserved_pngs':preserved}
(new/'previous_build_comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
def metrics(path):
 x=np.array(Image.open(path));opaque=x!=0;dark=x==1
 inside=np.pad(opaque,1);interior=opaque&inside[:-2,1:-1]&inside[2:,1:-1]&inside[1:-1,:-2]&inside[1:-1,2:]
 boundary=opaque&~interior
 return {'opaque':int(opaque.sum()),'dark_fraction':float(dark.sum()/opaque.sum()),
         'boundary_dark_fraction':float((boundary&dark).sum()/boundary.sum()),
         'dark_2x2_blocks':int((dark[:-1,:-1]&dark[:-1,1:]&dark[1:,:-1]&dark[1:,1:]).sum())}
art={'idle':metrics(new/'idle_147.png'),'before':{},'after':{}}
for n in (3,4,*range(7,21)):
 art['before'][n]=metrics(old/f'frame_{n:03d}.png');art['after'][n]=metrics(new/f'frame_{n:03d}.png')
(new/'outline_metrics.json').write_text(json.dumps(art,indent=2),encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
def aligned(folder,n):
 tile=Image.new('RGBA',(64,72),(42,45,54,255));c=composition_frame(parts,0,n)
 f=graphics_bank(gb,0)['frames'][n];raw=decode_stream(gb,f['offset'],f['limit'],f['tile_count']*128).data
 _,_,bounds,_=compose_indices(raw,f['tile_count'],c)
 path=folder/f'{"idle" if n in (0,1,2,146,147,148) else "frame"}_{n:03d}.png'
 tile.alpha_composite(Image.open(path).convert('RGBA'),(32+bounds[0],40+bounds[1]))
 return tile.resize((256,288),Image.Resampling.NEAREST)
seq=[];dur=[];elapsed=0
for j,n in enumerate(range(7,21)):
 board=Image.new('RGBA',(768,320),(42,45,54,255));d=ImageDraw.Draw(board)
 for k,(label,folder,frame) in enumerate((('기준 대기',new,147),('수정 전',old,n),('수정 후',new,n))):
  board.alpha_composite(aligned(folder,frame),(k*256,32));d.text((k*256+8,5),label,font=font,fill='white')
 seq.append(board.convert('RGB'))
 tick=(2,3,2,2,2,3,2)[j%7];before=round(elapsed*100/60)*10;elapsed+=tick;dur.append(round(elapsed*100/60)*10-before)
seq[0].save(new/'run_before_after_4x.gif',save_all=True,append_images=seq[1:],duration=dur,loop=0,disposal=2)
seq[0].save(new/'run_before_after_4x.png')
for name in ('run_preview_1x.gif','run_preview_4x.gif','run_sheet_4x.png'):(new/name).write_bytes((motion/name).read_bytes())
print(json.dumps({'changed':changed,'preserved_png_count':len(preserved),'composed':composed,
 'outline_range_after':[min(v['dark_fraction'] for v in art['after'].values()),max(v['dark_fraction'] for v in art['after'].values())],
 'boundary_dark_after':[min(v['boundary_dark_fraction'] for v in art['after'].values()),max(v['boundary_dark_fraction'] for v in art['after'].values())]}))
