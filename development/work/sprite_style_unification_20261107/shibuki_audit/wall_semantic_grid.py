"""새 원화의 native 색인/부위 위치를 읽기 위한 표만 생성한다."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from native_pose_pack import SOURCE

a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC'])
out=H/'wall_semantic_grid';out.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',14)
for n in range(55,67,2):
 board=Image.new('RGB',(960,610),(28,31,41));d=ImageDraw.Draw(board)
 for col,(label,start)in enumerate((('base',0),('fourth',16))):
  v=np.array(Image.open(H/'wall_contact_native03'/f'{label}_{n:03}_indices.png'))
  pic=a.rgba(v,start).crop((138,130,184,185)).resize((460,550),Image.Resampling.NEAREST);board.paste(pic,(col*480,40),pic)
  d.text((col*480+4,4),f'{label} {n} x=-22..23 / y=-30..24',font=font,fill='white')
 board.save(out/f'{n:03}.png')
 # Exact hexadecimal rows, avoiding ambiguity about native palette indices.
 lines=[]
 for label in('base','fourth'):
  v=np.array(Image.open(H/'wall_contact_native03'/f'{label}_{n:03}_indices.png'))
  lines.append(label+' x=-22..23')
  lines.extend(f'{y-160:3}: '+''.join(format(int(c),'x')if c else'.'for c in v[y,138:184])for y in range(130,185))
 (out/f'{n:03}.txt').write_text('\n'.join(lines)+'\n','utf8')
