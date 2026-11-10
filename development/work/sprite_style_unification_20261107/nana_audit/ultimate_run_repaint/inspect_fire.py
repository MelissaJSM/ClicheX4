"""팔 의미영역 등록을 위한 실제 인덱스 좌표 판. 새 아트 생성은 하지 않는다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive
def main():
 p=argparse.ArgumentParser();p.add_argument('--page',required=True);p.add_argument('--form',default='before');args=p.parse_args();a=Archive((D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC').read_bytes());reg=json.loads((D/f'firing_{args.page}_{args.form}_registered_v1/registration.json').read_text('utf8'));out=D/f'firing_{args.page}_{args.form}_grids_v1';out.mkdir(exist_ok=False);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',10)
 for q in reg['frames']:
  n=q['ref'];roi=(-32,-18,8,9);w,h=40,27;scale=18;c=Image.new('RGB',(w*scale*2,h*scale+50),'#bdc7cf');dr=ImageDraw.Draw(c)
  for j,path in enumerate((ROOT/q['body_path'],D/f'firing_{args.page}_{args.form}_registered_v1/{args.form}_{n:03}.png')):
   idx=np.array(Image.open(path));im=a.rgba(idx,16 if args.form=='before'else 0).crop(tuple(v+160 for v in roi)).resize((w*scale,h*scale),Image.Resampling.NEAREST);c.paste(im,(j*w*scale,50),im);dr.text((j*w*scale+3,3),f'{n} '+('new fixed body'if j==0 else'new arm source'),fill='black')
   for y in range(h):
    for x in range(w):
     v=int(idx[roi[1]+y+160,roi[0]+x+160]);px=j*w*scale+x*scale;py=50+y*scale;dr.rectangle((px,py,px+scale-1,py+scale-1),outline='#89969c')
     if v:dr.text((px+2,py+1),str(v),font=font,fill='white'if v in(1,2,3,5,6,7)else'black')
   for x in range(0,w,2):dr.text((j*w*scale+x*scale,29),str(roi[0]+x),font=font,fill='black')
   for y in range(0,h,2):dr.text((j*w*scale+2,50+y*scale),str(roi[1]+y),font=font,fill='#b01818')
  c.save(out/f'{n:03}.png')
 print(out)
if __name__=='__main__':main()
