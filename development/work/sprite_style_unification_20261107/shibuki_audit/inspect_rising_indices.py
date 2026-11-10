"""새 원화의 색인과 월드 좌표만 표시한다. 원화/자원 변경 없음."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.export_x_consistency import Archive

a=Archive((H/'prepared_double_cyclone_base01/PL00_U.ARC').read_bytes())
u=Archive((H/'prepared_double_cyclone_ultimate01/PL02_U.ARC').read_bytes())
o=H/'rising_index_review01';o.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
for n in(100,101,102,103,104,231):
    page=1 if n<103 else 2
    board=Image.new('RGB',(1040,1190),(25,29,40));draw=ImageDraw.Draw(board);lines=[]
    for i,(form,arc,pal)in enumerate((('base',a,0),('fourth',a,16),('ultimate_before',u,16),('ultimate_after',u,0))):
        d=H/(f'rising_fire_native{page:02}'if i<2 else f'rising_ultimate_native{page:02}')
        if n==104 and i<2:d=H/'rising104_arm_native02'
        v=np.array(Image.open(d/f'{form}_{n:03}_indices.png'))
        c=arc.rgba(v,pal).crop((136,128,184,186)).resize((480,580),Image.Resampling.NEAREST)
        ox=(i%2)*520+30;oy=(i//2)*595+20;board.paste(c,(ox,oy),c)
        draw.text((ox,oy-18),f'{form} {n}',font=font,fill='white')
        for x in range(-24,24,4):draw.text((ox+(x+24)*10,oy+562),str(x),font=font,fill=(150,170,190))
        for y in range(-32,26,4):draw.text((ox-28,oy+(y+32)*10),str(y),font=font,fill=(150,170,190))
        lines.append(form+' x=-24..23');lines.extend(f'{y-160:3}: '+''.join(format(int(c),'x')if c else'.'for c in v[y,136:184])for y in range(128,186))
    board.save(o/f'{n:03}.png');(o/f'{n:03}.txt').write_text('\n'.join(lines)+'\n','utf8')
