"""파츠 분리를 위한 원그림/새 원화/팔레트 좌표 시트. 입력을 수정하지 않는다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,write
P=H/'prepared_arrival_victory01/PL00_U.ARC'
REFS={33:1,35:1,39:1,37:2,41:2,43:2,45:3,47:3,49:3,51:4,53:4}
def arrays(n):
    d=H/f'air_detail_native{REFS[n]:02}'
    return tuple(np.array(Image.open(d/f'{form}_{n:03}_indices.png'))for form in('base','fourth'))
def main():
    o=H/'air_layer_diagnosis01';need(not o.exists(),'Fresh output only');o.mkdir();a=Archive(P.read_bytes());f=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
    for n in (33,39,45,49,53):
        base,full=arrays(n);idx=[base,full]+[a.layer(n,b)[0]for b in(0,5,6,7,8)];names=['new base','new Fourth','old base','old head5','old body6','old arm7','old leg8']
        canvas=Image.new('RGB',(7*360,40*18+42),(30,34,43));d=ImageDraw.Draw(canvas)
        for k,(im,name)in enumerate(zip(idx,names)):
            d.text((k*360+3,3),f'{n} {name}',font=f,fill='white')
            rgba=a.rgba(im,0 if k in(0,2) else 16)
            for y in range(40):
                wy=y-25
                for x in range(20):
                    wx=x-10;v=int(im[160+wy,160+wx]);rgb=rgba.getpixel((160+wx,160+wy))
                    xx=k*360+x*18;yy=42+y*18
                    d.rectangle((xx,yy,xx+17,yy+17),fill=rgb[:3]if v else(40,45,54),outline=(75,75,80))
                    if v:d.text((xx+4,yy+2),f'{v:X}',font=f,fill='black'if sum(rgb[:3])>380 else'white')
        canvas.save(o/f'grid_{n:03}.png')
    page([(f'{n} old layer{b}',a.rgba(a.layer(n,b)[0],0 if b==0 else 16))for n in(33,39,45,49,53)for b in(0,5,6,7,8)],a.composite(0,15)[0],o/'old_ownership.png',cols=5,scale=4)
    write(o/'palettes.json',{str(p):[{'index':i,'rgb':[(int(a.words[p+i])>>s&31)*255//31 for s in(0,5,10)]}for i in range(16)]for p in(0,16,32)})
    print(o)
if __name__=='__main__':main()
