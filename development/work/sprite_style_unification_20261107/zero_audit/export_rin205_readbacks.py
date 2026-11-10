"""긴 새 리본까지 자르지 않는 고정 원점 실제 ARC 재독출 시트."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';P=D/'prepared_followthrough01';old=(D/'prepared_spin01/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();keys=[(1,146),(1,156),(1,158),(0,197),(0,212)]
box=(112,104,216,200);scale=4;w,h=104*scale,96*scale;rows=[]
for form,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(new,9),row*32)
 for start in(0,4):
  group=keys[start:start+4];sheet=Image.new('RGB',(w*3,(h+26)*len(group)),'#64717b');dr=ImageDraw.Draw(sheet)
  for iy,(b,n)in enumerate(group):
   for ix,(label,arc,gb,ref)in enumerate([('idle',new,0,147),('before',old,b,n),('packed detailed',new,b,n)]):
    a=render(arc,gb,gb*5,ref)[0];outside=a.copy();outside[104:200,112:216]=0;assert not outside.any(),(form,b,n,label)
    im=rgba(a,pal).crop(box).resize((w,h),Image.Resampling.NEAREST);sheet.paste(im,(ix*w,iy*(h+26)+26),im);dr.text((ix*w+5,iy*(h+26)+4),f'b{b}:{n} {label}',fill='white')
  path=P/f'{form}_readback_{start//4:02}.png';sheet.save(path);rows.append({'path':path.relative_to(ROOT).as_posix(),'refs':group,'form':form,'crop':box,'scale':scale,'no_clipping':True})
(P/'readback_manifest.json').write_text(json.dumps({'origin':[160,160],'sheets':rows,'old_fixed80px_preview_replaced':True},ensure_ascii=False,indent=2)+'\n','utf8');print(len(rows))
