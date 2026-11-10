from pathlib import Path
import sys,json,hashlib,math
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT));R=W/'runtime'
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
sha=lambda b:hashlib.sha256(b).hexdigest()
game=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v14/shibuki_riko.bin'
assert sha(game.read_bytes())=='b1e00232f8a62bea766e7b40dded110b0c2e66a2fbd2795725347510a0af581d'
arc=read_disc(game,('ST0E_U1.ARC',))[0]['ST0E_U1.ARC'];tex=entry(arc,0x10102)[90112:]
dump=ROOT/'work/ver_buki_riko/korean_runtime/20261107T132549373265Z/vram_84467744.bin';vram=dump.read_bytes()
rows=[tex[i:i+128] for i in range(0,len(tex),128)]
first=next(i for i,r in enumerate(rows) if len(set(r))>8)
positions=[];at=vram.find(rows[first])
while at>=0:positions.append(at);at=vram.find(rows[first],at+1)
matches=[]
for at in positions:
 x=at%2048;y=at//2048-first
 for height in range(16,513,16):
  if y<0 or y+height>512:continue
  if all(vram[(y+i%height)*2048+x+(i//height)*128:(y+i%height)*2048+x+(i//height)*128+128]==row for i,row in enumerate(rows)):
   matches.append({'byte_x':x,'y':y,'rows_per_column':height})
out=R/'shibuki_selection14_review';assert not out.exists();out.mkdir()
im=Image.open(R/'shibuki_selection14_play/play.webp');times=[]
for i in range(im.n_frames):im.seek(i);im.load();times.append(im.info['timestamp']/1000)
ids=[i for i,t in enumerate(times) if t<=2.0];box=(0,285,330,480);cw,ch=330,195;pages=[]
for start in range(0,len(ids),8):
 nums=ids[start:start+8];board=Image.new('RGB',(cw*2,(ch+24)*math.ceil(len(nums)/2)),'#202630');d=ImageDraw.Draw(board)
 for j,i in enumerate(nums):
  im.seek(i);x,y=j%2*cw,j//2*(ch+24);board.paste(im.convert('RGB').crop(box),(x,y+24));d.text((x+4,y+5),f'WebP {i} / {times[i]:.3f}s',fill='white')
 p=out/f'selection_{start//8:02}.png';board.save(p);pages.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())})
report={'bin_sha256':sha(game.read_bytes()),'arc_sha256':sha(arc),'dump':dump.relative_to(ROOT).as_posix(),'dump_sha256':sha(vram),'atlas_bytes':len(tex),'layout_matches':matches,'full_atlas_exact':bool(matches),'encoded_frames':im.n_frames,'pages':pages,'individual_frame_upload_verified':False,'process_memory_written':False}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report))
