from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,write
from register_arm_reach_joint import source_folder
from prepare_next_guides import body_path
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/'pistol_residue_review';out.mkdir(exist_ok=True)
    for n in (68,70,72,76,78,80,82,84):
        q=next(q for q in p['frames']if q['ref']==n);ex,ey=[int(np.floor(v))for v in q['eye']];box=(ex-7+160,ey+2+160,ex+9+160,ey+16+160);sheet=Image.new('RGB',(960,320),(190,199,204));draw=ImageDraw.Draw(sheet)
        arrs=[np.array(Image.open(body_path(n-1))),np.array(Image.open(D/'firing_reach_joint_v2'/f'merged_{n:03}.png')),np.array(Image.open(source_folder(n)/f'base_{n:03}.png'))]
        for k,ar in enumerate(arrs):
            rgba=a.rgba(ar).crop(box).resize((320,280),Image.Resampling.NEAREST);sheet.paste(rgba,(k*320,20),rgba);draw.text((k*320+4,2),f'{n} '+['body','current','new shot source'][k],fill='black')
            for x in range(ex-7,ex+9):
                xx=k*320+(x-ex+7)*20;draw.line((xx,20,xx,300),fill=(145,160,172));draw.text((xx,302),str(x),fill='black')
            for y in range(ey+2,ey+16):
                yy=20+(y-ey-2)*20;draw.line((k*320,yy,k*320+320,yy),fill=(145,160,172));draw.text((k*320+1,yy+1),str(y),fill='black')
        sheet.save(out/f'ref{n}.png')
    for n in (93,94):
        b=np.array(Image.open(body_path(n)));f=np.array(Image.open(D/'fourth_c_registered_v1'/f'fourth_{n:03}.png'))
        print(n,'base floor',np.flatnonzero(b[np.nonzero(b)[0].max()])-160,'fourth floor',np.flatnonzero(f[np.nonzero(f)[0].max()])-160)
if __name__=='__main__':main()
