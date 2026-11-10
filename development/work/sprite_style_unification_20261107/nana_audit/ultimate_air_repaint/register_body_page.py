"""신규 공중 몸체 원화를 대기 눈/귀 비율과 기존 원점으로 등록한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import register,crop_cell
from register_first_before import eye
from check_first_geometry import info,full
SRC=N/'native_restore/nova_sync_v1/PL02_U.ARC';SHA='bced7f9086a9e6a72440bab25cda7e0c87ccc121a2ffbbc970f750dee257da45'
def main():
    p=argparse.ArgumentParser();p.add_argument('--art',required=True);p.add_argument('--art-sha',required=True);p.add_argument('--inputs',required=True);p.add_argument('--out',required=True);p.add_argument('--form',choices=['before','after'],default='before');args=p.parse_args()
    art=D/args.art;need(digest(SRC)==SHA and digest(art)==args.art_sha,'Input SHA');out=D/args.out;need(out.parent==D,'Local output');out.mkdir(exist_ok=False)
    a=Archive(SRC.read_bytes());form=args.form;offset=16 if form=='before'else 0;mask=15 if form=='before'else 0;plan=json.loads((D/args.inputs/f'{form}_poses.json').read_text('utf8'));im=Image.open(art).convert('RGBA');palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[offset:offset+16]],np.float32);records=[];rows=[]
    for i,p in enumerate(plan):
        n=p['ref']
        if len(plan)==4:crop,box=crop_cell(im,i)
        else:
            cx=i%2*im.width//2;cy=i//2*im.height//2;cell=im.crop((cx,cy,cx+im.width//2,cy+im.height//2));aa=np.array(cell);labs,_=label(aa[:,:,3]>=128,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0;k=int(counts.argmax());yy,xx=np.nonzero(labs==k);need(len(xx)>1000,'Missing figure');aa[labs!=k,3]=0;box=[int(xx.min()+cx),int(yy.min()+cy),int(xx.max()+1+cx),int(yy.max()+1+cy)];crop=Image.fromarray(aa).crop((xx.min(),yy.min(),xx.max()+1,yy.max()+1))
        crop.save(out/f'source_{n:03}.png');sx,sy=p.get('source_eye_override',eye(crop));ex,ey=map(int,p['eye_world']);ar=np.array(crop);Y,X=np.indices(ar.shape[:2]);ys,_=np.nonzero((ar[:,:,3]>=128)&(X<sx+crop.width*.18));crown=int(ys.min())
        scale=17/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);ntop=ey-round(split*scale)+1;hu=ey-ntop+1;bottom=p['bbox_world'][3];hl=bottom-ey-1
        upper=register(crop.crop((0,0,crop.width,split)),(width,hu),palette,'area_vote');lower=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),palette,'area_vote');native=np.concatenate((upper,lower));ec=round((sx+.5)*width/crop.width-.5);ox=ex-ec
        native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14
        target=np.zeros((384,384),np.uint8);target[ntop+160:ntop+160+len(native),ox+160:ox+160+width]=native
        Image.fromarray(target).save(out/f'{form}_{n:03}.png');a.rgba(target,offset).save(out/f'{form}_{n:03}_rgba.png');yy,xx=np.nonzero(target);need(int(yy.max()-160)==bottom-1,'Foot height')
        rec={'ref':n,'source_crop':box,'source_eye':[sx,sy],'source_crown':crown,'scale_x':scale,'native_width':width,'upper_height':hu,'lower_height':hl,'split':split,'native_position':[ox,ntop],'eye_world':[ex,ey],'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'indexed_sha256':sha(target.tobytes()),'old_body_pixels_used':0,'old_geometry':info(full(a,n),[ex,ey]),'new_geometry':info(target,[ex,ey])};records.append(rec)
        rows.append((f'Ultimate {n}',[('accepted idle',a.composite(0,mask)[0]),('current pose',a.composite(n,mask)[0]),('new authored native',a.rgba(target,offset))]))
    helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'parent_arc_sha256':SHA,'source_art_sha256':args.art_sha,'frames':records,'method':'Eye and ear17px anchor; current sole height. Source upper/lower area-vote. No old sprite surface pixels. Hand/foot x contacts pending.','runtime_verified':False,'native_packed':False,'whole_air_completed':False});print(str(out))
if __name__=='__main__':main()
