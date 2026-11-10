"""다음 네이티브 자세를 원점 보존 입력으로 추출한다. 원화 편집 없음."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,digest,need,sha
SRC=N/'native_restore/nova_sync_v1/PL02_U.ARC'
EXPECTED='bced7f9086a9e6a72440bab25cda7e0c87ccc121a2ffbbc970f750dee257da45'
def main():
    p=argparse.ArgumentParser();p.add_argument('--keys',type=int,nargs='+',required=True);p.add_argument('--out',required=True);args=p.parse_args()
    need(len(args.keys)<=4 and len(set(args.keys))==len(args.keys),'Up to four unique poses')
    need(digest(SRC)==EXPECTED,'Parent changed');a=Archive(SRC.read_bytes());out=D/args.out;need(out.parent==D,'Local output');out.mkdir(exist_ok=False)
    for mask,form in [(15,'before'),(0,'after')]:
        board=Image.new('RGBA',(1280,1280));records=[]
        for i,n in enumerate(args.keys):
            im=a.composite(n,mask)[0];board.alpha_composite(im.crop((120,120,200,200)).resize((640,640),Image.Resampling.NEAREST),(i%2*640,i//2*640))
            yy,xx=np.nonzero(np.array(im)[:,:,3]);index=a.layer(n)[0].copy()
            if mask:
                for pb in (8,5,7,6):
                    q=a.layer(n,pb)[0];index[q>0]=q[q>0]
            gy,gx=np.nonzero((index==14)&(np.indices(index.shape)[0]<165));need(len(gx)>0,'Eye not found')
            records.append({'ref':n,'mask':mask,'cell':[i%2,i//2],'eye_world':[float(np.median(gx))-160,float(np.median(gy))-160],'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'rgba_sha256':sha(im.tobytes())})
        board.save(out/f'{form}_pose_targets.png');write(out/f'{form}_poses.json',records)
    write(out/'manifest.json',{'parent_sha256':EXPECTED,'keys':args.keys,'native_window_world':[-40,-40,40,40],'scale':8,'cell':[640,640],'images':{p.name:digest(p)for p in out.glob('*.png')},'new_art':False})
    print(str(out))
if __name__=='__main__':main()
