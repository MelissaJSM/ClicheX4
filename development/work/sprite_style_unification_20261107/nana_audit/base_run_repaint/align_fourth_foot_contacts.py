"""수용된 새 원화 발은 강체 이동, 발목 위 접점만 국소 좌표 정합."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive,sha,write,helper,need
from PIL import Image
import numpy as np
D=Path(__file__).parent
def align(source,n):
    target=source.copy();links=[]
    if n==1:
        # New Fourth left shoe bbox (-6,19)..(1,21) is one pixel right/up
        # from the already anchored basic boot. Move the whole shoe (-1,+1).
        # The shin transition samples only the same authored shin (no color fill).
        source_rect=(-8,12,3,22);x0,y0,x1,y1=source_rect;target[160+y0:160+y1,160+x0:160+x1]=0
        for y in range(12,23):
            sy=round(np.interp(y,[12,18,22],[12,17,21]));dx=round(np.interp(y,[12,15], [0,-1]))
            for x in range(x0,x1):
                value=int(source[160+sy,160+x])
                if value:
                    target[160+y,160+x+dx]=value;links.append([x+dx,y,x,sy,value])
    elif n==27:
        # The extended right ankle is 3 pixels to the right of the basic contact.
        # Preserve its complete shoe, and ease the translation along the shin.
        for y in range(11,24):
            dx=round(np.interp(y,[11,14,17],[0,-2,-3]));xmin=round(np.interp(y,[11,14],[8,9]))
            target[160+y,160+xmin:160+22]=0
            for x in range(xmin,22):
                value=int(source[160+y,160+x])
                if value:target[160+y,160+x+dx]=value;links.append([x+dx,y,x,y,value])
    return target,links
def main():
    out=D/'fourth_contacts_v1';out.mkdir(exist_ok=True);a=Archive((D/'baseline_PL00_U.ARC').read_bytes());report=[]
    for n in range(1,33,2):
        src=np.array(Image.open(D/'fourth_body_scale'/f'run_{n:03}.png'));target,links=align(src,n);Image.fromarray(target).save(out/f'run_{n:03}.png');report.append({'ref':n,'source_sha':sha(src.tobytes()),'target_sha':sha(target.tobytes()),'source_links':links})
    write(out/'report.json',{'ready_to_apply':False,'method':'새 포스 원화 발 1/27 접점 정합. 신발 모양/재질 보존. 신발위 정강이만 원화좌표 정합.','frames':report})
if __name__=='__main__':main()
