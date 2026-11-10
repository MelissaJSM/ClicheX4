"""낙봉파 새 원화의 cyan 눈 원색과 원효과/손목 접점을 확대 비교한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
R=D/'rin_extension';A=R/(sys.argv[1]if len(sys.argv)>1 else 'burst_charge01');O=A/'contact_analysis';O.mkdir(exist_ok=True);info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['source_arc']).read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));im=Image.open(A/'generated.png').convert('RGBA');source=np.array(im);rows=[];sheet=Image.new('RGB',(1440,350*len(info['masters'])),'#3c4554');dr=ImageDraw.Draw(sheet)
for i,rec in enumerate(info['masters']):
 n=rec['ref'];cx,cy=rec['cell'];c=rec['world_crop'];cells=[]
 for y in range(135,171):
  for x in range(133,165):
   sx=(x-c[0]+cx*96)*8;sy=(y-c[1]+cy*64)*8;p=source[sy:sy+8,sx:sx+8];r,g,b,a=[p[:,:,k].astype(int)for k in range(4)];mask=(a>=128)&(g>r+15)&(b>r+15)&(g>70)&(g>b*.65)
   if mask.sum()>=16:cells.append({'world':[x,y],'count':int(mask.sum()),'mean':p[mask,:3].mean(0).round(1).tolist()})
 rows.append({'ref':n,'cyan_cells':cells});old=np.array(Image.open(A/f'b1_{n:03}_body_indices.png'));new=np.array(Image.open(A/'native_fixed'/f'b1_{n:03}_indices.png'))
 rect=(130,144,164,174)if n in(186,188)else(137,132,171,162)
 for col,(tag,a)in enumerate([('old',old),('new',new)]):
  pic=rgba(a,pal).crop(rect).resize((340,300),Image.Resampling.NEAREST);sheet.paste(pic,(col*360,i*350+20),pic);dr.text((col*360+3,i*350+3),f'{n} {tag}',fill='white')
 sx=(rect[0]-c[0]+cx*96)*8;sy=(rect[1]-c[1]+cy*64)*8;pic=im.crop((sx,sy,sx+34*8,sy+30*8));sheet.paste(pic,(740,i*350+20),pic)
sheet.save(O/'faces.png');(O/'cyan_samples.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rows))
