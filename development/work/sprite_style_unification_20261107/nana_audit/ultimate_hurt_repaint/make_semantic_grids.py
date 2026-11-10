"""새 원화 의미 경계를 읽기 위한 좌표 격자. 원화 변경 없음."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive

def main():
    a=Archive((N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC').read_bytes())
    out=D/'semantic_grids_v1';out.mkdir(exist_ok=True)
    for n in (106,110,233,234):
        page='first' if n<200 else 'extra'
        board=Image.new('RGB',(1530,865),'#b6c0c7');dr=ImageDraw.Draw(board)
        for i,(f,pal) in enumerate((('before',16),('after',0))):
            z=np.array(Image.open(D/f'{page}_registered_v1/{f}_{n:03}_registered_indices.png'))
            x0,y0,x1,y1=-17,-25,20,15;s=20;ox=i*765+25;oy=40
            pic=a.rgba(z,pal).crop((160+x0,160+y0,160+x1,160+y1));pic=pic.resize((pic.width*s,pic.height*s),Image.Resampling.NEAREST)
            board.paste(pic,(ox,oy),pic);dr.text((ox,4),f'{n} {f}',fill='black')
            for x in range(x0,x1):dr.text((ox+(x-x0)*s,22),str(x),fill='black')
            for y in range(y0,y1):dr.text((ox-25,oy+(y-y0)*s),str(y),fill='black')
            for x in range(x0,x1+1):dr.line((ox+(x-x0)*s,oy,ox+(x-x0)*s,oy+(y1-y0)*s),fill='#879099')
            for y in range(y0,y1+1):dr.line((ox,oy+(y-y0)*s,ox+(x1-x0)*s,oy+(y-y0)*s),fill='#879099')
        board.save(out/f'grid_{n}.png')
if __name__=='__main__':main()
