"""공중 기존 픽셀·대기 기준을 고정 원점 2x2 입력으로 보존한다. 새 그림 없음."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];N=Path(__file__).parent.parent;D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,digest,need,sha
SRC=N/'native_restore/nova_sync_v1/PL02_U.ARC'
EXPECTED='bced7f9086a9e6a72440bab25cda7e0c87ccc121a2ffbbc970f750dee257da45'
KEYS=[33,39,47,51];SCALE=8;WINDOW=(120,120,200,200)

def main():
    need(digest(SRC)==EXPECTED,'Parent changed');a=Archive(SRC.read_bytes());out=D/'inputs_first_v1';out.mkdir(parents=True,exist_ok=False)
    for mask,form in [(15,'before'),(0,'after')]:
        board=Image.new('RGBA',(1280,1280));records=[]
        for i,n in enumerate(KEYS):
            im=a.composite(n,mask)[0];pic=im.crop(WINDOW).resize((640,640),Image.Resampling.NEAREST);board.alpha_composite(pic,(i%2*640,i//2*640))
            ar=np.array(im);alpha=ar[:,:,3]>0;ys,xs=np.nonzero(alpha);rows=[]
            index=a.layer(n)[0].copy()
            if mask:
                for pb in (8,5,7,6):
                    q=a.layer(n,pb)[0];index[q>0]=q[q>0]
            gy,gx=np.nonzero((index==14)&(np.indices(index.shape)[0]<165));eye=[float(np.median(gx))-160,float(np.median(gy))-160]if len(gx)else None
            records.append({'ref':n,'mask':mask,'cell':[i%2,i//2],'eye_world':eye,'bbox_world':[int(xs.min()-160),int(ys.min()-160),int(xs.max()+1-160),int(ys.max()+1-160)],'rgba_sha256':sha(im.tobytes())})
        board.save(out/f'{form}_pose_targets.png');write(out/f'{form}_poses.json',records)
    refs=Image.new('RGBA',(1280,640))
    for i,(n,mask)in enumerate([(0,15),(85,15),(0,0),(85,0)]):
        im=a.composite(n,mask)[0].crop((132,116,188,184)).resize((280,340),Image.Resampling.NEAREST)
        refs.alpha_composite(im,(i*320+20,140))
    refs.save(out/'accepted_idle_and_shot.png')
    write(out/'manifest.json',{'parent':str(SRC.relative_to(ROOT)),'parent_sha256':EXPECTED,'keys':KEYS,'native_window_world':[-40,-40,40,40],'scale':8,'cell':[640,640],
     'images':{p.name:digest(p)for p in out.glob('*.png')},'new_art':False,'identity':'Nana Ultimate; before jacket,after swimsuit; both current design only','prompt_scope':'first4 nonshooting bodies. Gun arms and remaining7 bodies follow;not wholeair completion.'})
    print(str(out))
if __name__=='__main__':main()
