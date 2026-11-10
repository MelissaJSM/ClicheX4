"""새 벽사격 팔 아래의 접힌 손/옷 잔여를 원화와 좌표별로 읽는다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,digest
def main():
 p=argparse.ArgumentParser();p.add_argument('--page',default='a');args=p.parse_args();a=Archive((N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes());out=D/f'firing_{args.page}_after_alpha_grids_v1';out.mkdir(exist_ok=False);meta=json.loads((D/f'firing_{args.page}_after_joint_probe_v4/registration.json').read_text('utf8'));f=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',11);roi=(-16,-13,8,4);s=24;w=roi[2]-roi[0];h=roi[3]-roi[1]
 for q in meta['frames']:
  n=q['ref'];dx,dy=q['rigid_arm_translation'];dst=np.array(Image.open(D/f'firing_{args.page}_after_joint_probe_v4'/f'after_{n:03}.png'));raw=np.array(Image.open(D/f'firing_{args.page}_after_registered_v1'/f'after_{n:03}.png'));src=np.roll(raw,(dy,dx),(0,1));c=Image.new('RGB',(w*s*2,h*s+50),'#bdc7cf');dr=ImageDraw.Draw(c)
  for j,idx in enumerate((dst,src)):
   im=a.rgba(idx,0).crop(tuple(q+160 for q in roi)).resize((w*s,h*s),Image.Resampling.NEAREST);c.paste(im,(j*w*s,50),im);dr.text((j*w*s+3,3),f'{n} '+('candidate'if j==0 else'aligned new source'),fill='black')
   for y in range(h):
    for x in range(w):
     v=int(idx[roi[1]+y+160,roi[0]+x+160]);px=j*w*s+x*s;py=50+y*s;dr.rectangle((px,py,px+s-1,py+s-1),outline='#89969c')
     if v:dr.text((px+2,py+2),str(v),font=f,fill='white'if v in(1,2,3,5,6,7)else'black')
   for x in range(0,w,2):dr.text((j*w*s+x*s,29),str(roi[0]+x),font=f,fill='black')
   for y in range(0,h,2):dr.text((j*w*s+2,50+y*s),str(roi[1]+y),font=f,fill='#b01818')
  c.save(out/f'{n:03}.png')
 print(out)
if __name__=='__main__':main()
