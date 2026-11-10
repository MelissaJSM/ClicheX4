"""右手 수정 시안의 고정 캔버스 등록과 실제 원효과 위치 비교. 미패킹 후보."""
from pathlib import Path
import sys,json,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--height-source',action='store_true');ap.add_argument('--height-alpha',type=int,default=128);ap.add_argument('--out');args=ap.parse_args();out=H/(args.out or('rising_right_hand_native02'if args.height_source else'rising_right_hand_native01'));need(not out.exists(),'Fresh probe');out.mkdir();a=Archive((H/'prepared_rising_fire_base02/PL00_U.ARC').read_bytes());sources={103:H/'rising_air_hand_fix_inputs01/page01/generated_rejected104.png',104:H/('rising104_height_edit01/generated.png'if args.height_source else'rising104_right_hand_retry01/generated.png')};rows=[]
    for form,row,mask,pal in [('base',0,0,0),('fourth',1,15,16)]:
        pics=[];rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32)
        for n in(103,104):
            im=Image.open(sources[n]).convert('RGBA');need(im.size==(1536,1024),'Wrong source layout')
            if n==103:im=im.crop((0,row*512,512,(row+1)*512))
            else:im=im.crop((row*768,128,(row+1)*768,896))
            cell=np.array(im.resize((64,64),Image.Resampling.NEAREST));q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);threshold=args.height_alpha if n==104 and args.height_source else 128;q[cell[:,:,3]<threshold]=0;v=np.zeros((384,384),np.uint8);v[124:188,128:192]=q;Image.fromarray(v).save(out/f'{form}_{n:03}_indices.png');new=a.rgba(v,pal);new.save(out/f'{form}_{n:03}.png');pics.extend([(f'{n} current wrong left fist',a.composite(n,mask)[0]),(f'{n} fresh right fist candidate',new)]);yy,xx=np.indices((384,384));r=np.array(new);skin=(r[:,:,3]>0)&(xx>=160)&(yy<148)&(np.all(r[:,:,:3]==[238,164,131],2)|np.all(r[:,:,:3]==[255,222,189],2));py,px=np.nonzero(skin);rows.append({'form':form,'ref':n,'source_sha256':sha(sources[n].read_bytes()),'new_metrics':metrics(new),'raised_skin_bbox':[int(px.min()-160),int(py.min()-160),int(px.max()+1-160),int(py.max()+1-160)]if len(px)else None,'fixed_scale':1/8 if n==103 else 1/12,'old_pixels_used':0,'source_alpha_threshold':threshold})
        page(pics,a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5)
    write(out/'report.json',{'rows':rows,'registration_pending':True,'arc_written':False,'gameplay_verified':False});print(json.dumps(rows))
if __name__=='__main__':main()
