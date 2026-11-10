"""새 피격4의 발과 머리 부분을 좌표를 유지하여 확대한다. 등록 변경 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write
def main():
    a=Archive((N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC').read_bytes())
    out=D/'first_contact_review_v2';out.mkdir(exist_ok=False);board=Image.new('RGB',(1120,960),'#b6c0c7');dr=ImageDraw.Draw(board);data=[]
    for i,(n,form,mask,row)in enumerate((n,f,m,r)for n in(106,110)for f,m,r in(('before',15,16),('after',0,0))):
        z=np.array(Image.open(D/'first_registered_v1'/f'{form}_{n}_registered_indices.png'));old=a.composite(n,mask)[0];im=a.rgba(z,row)
        y,x=np.where(z>0);bottom=int(y.max()-160);yy,xx=np.indices(z.shape);fy,fx=np.where((z>0)&(yy>=y.max()-4));ey,ex=np.where((z==14)&(yy<160))
        oy,ox=np.where(np.array(old)[:,:,3]>0);of=ox[oy>=oy.max()-4]
        data.append({'ref':n,'form':form,'sole_y':bottom,'original_sole_y':int(oy.max()-160),'new_feet_bottom5_x':[int(fx.min()-160),int(fx.max()-160)],'original_feet_bottom5_x':[int(of.min()-160),int(of.max()-160)],'green_upper_world':[[int(x-160),int(y-160)]for y,x in zip(ey,ex)]})
        pics=[('old feet',old,(140,169,176,187)),('new feet',im,(140,169,176,187)),('old head',old,(140,128,184,160)),('new head',im,(140,128,184,160))]
        for j,(title,pic,box)in enumerate(pics):
            dr.text((j*280+4,i*240+4),f'{form} {n}: {title}',fill='black');crop=pic.crop(box);scale=6;crop=crop.resize((crop.width*scale,crop.height*scale),Image.Resampling.NEAREST);board.paste(crop,(j*280+8,i*240+28),crop)
    board.save(out/'comparison.png');write(out/'metrics.json',{'frames':data,'scope':'새 원화 고정등록 후 손대지 않은 좌표 측정. 발5행의폭과원발바닥/머리 확대 비교이며 최종 정합 아님.'});print(json.dumps(data))
if __name__=='__main__':main()
