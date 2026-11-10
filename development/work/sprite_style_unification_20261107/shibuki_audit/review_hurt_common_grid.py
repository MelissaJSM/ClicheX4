"""피격 새 원화의 머리/옷/사지 소유를 정할 좌표판. 픽셀 수정 없음."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,write,sha
from scripts.export_x_consistency import Archive,page

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,default=1);z=ap.parse_args();refs=(106,110)if z.page==1 else(233,234)
    d=H/f'hurt_common_grid{z.page:02}';need(not d.exists(),'Fresh grid');d.mkdir()
    a=Archive((H/'prepared_base_run01/PL00_U.ARC').read_bytes())
    for n in refs:
        out=Image.new('RGB',(1360,790),(30,36,47));dr=ImageDraw.Draw(out)
        for col,form in enumerate(('base','fourth')):
            im=Image.open(H/f'hurt_native{z.page:02}'/f'{form}_{n:03}.png').convert('RGBA');crop=im.crop((136,136,184,188)).resize((576,624),Image.Resampling.NEAREST)
            x=col*680+64;y=64;out.paste(crop,(x,y),crop);dr.text((x,y-36),f'{n} new {form}',fill='white')
            for v in range(-24,25,4):
                px=x+(v+24)*12;dr.line((px,y,px,y+624),fill=(65,72,82),width=1);dr.text((px-4,y-16),str(v),fill='white')
            for v in range(-24,29,4):
                py=y+(v+24)*12;dr.line((x,py,x+576,py),fill=(65,72,82),width=1);dr.text((x-25,py-5),str(v),fill='white')
        out.save(d/f'{n:03}_grid.png')
        page([(f'old {n} layer{b}',a.rgba(a.layer(n,b)[0],0 if b==0 else 16))for b in(0,5,6,7,8)],a.composite(0,15)[0],d/f'{n:03}_old_layers.png',cols=3,scale=4)
    write(d/'report.json',{'read_only':True,'new_native_dir':f'hurt_native{z.page:02}','refs':list(refs),'coordinate_origin':[160,160],'grid_step':4,'art_pixels_modified':False,'grid_crop_note':'233의 왼쪽끝1px는 좌표판96이 아닌48폭에 걸치므로 완성도 판정은 별도96셀 비교판으로 수행한다.'})
if __name__=='__main__':main()
