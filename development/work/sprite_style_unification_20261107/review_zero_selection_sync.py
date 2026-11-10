"""Native readback sheets for copied character-selection sprites (no repaint)."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_album import selection_image
from scripts.prepare_riko_ui import SELECTION_MAPPING
W=Path(__file__).resolve().parent
for char in ('riko','rin'):
 out=W/'selection_sync01'/char
 plan=json.loads((out/'integration_candidate.json').read_text('utf8'))
 src=ROOT/plan['source_bin'];assert hashlib.sha256(src.read_bytes()).hexdigest()==plan['source_sha256']
 assets=read_disc(src,('ST0E_U1.ARC','COL0E_U1.ARC'))[0]
 assets['ST0E_U1.ARC']=(out/'ST0E_U1.ARC').read_bytes()
 refs=sorted(SELECTION_MAPPING);pages=[]
 for start in range(0,len(refs),8):
  board=Image.new('RGB',(1280,488),'#384553');d=ImageDraw.Draw(board)
  for j,n in enumerate(refs[start:start+8]):
   im=selection_image(assets,{'bank':0,'ref':n})
   # Preserve native pixels and fixed gameplay world origin at (160,160).
   crop=im.crop((80,80,240,190)).resize((320,220),Image.Resampling.NEAREST)
   x,y=j%4*320,j//4*244;board.paste(crop,(x,y+24),crop)
   b,k=SELECTION_MAPPING[n];d.text((x+4,y+4),f'{char} SELECT {n} -> BODY {b}:{k}',fill='white')
  p=out/f'readback_{start//8:02}.png';assert not p.exists();board.save(p)
  pages.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'references':refs[start:start+8]})
 (out/'readback_manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(assets['ST0E_U1.ARC']).hexdigest(),'pages':pages,'actual_redecoded_candidate':True,'gameplay_runtime':False},indent=2)+'\n','utf8')
print('2 characters / 64 selection references / 8 readback sheets')
