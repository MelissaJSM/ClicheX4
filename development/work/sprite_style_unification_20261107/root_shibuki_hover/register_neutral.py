"""Character-neutral fixed-cell registration; no Nana-specific eye index rule."""
from pathlib import Path
import sys,json,hashlib,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from scripts.export_x_consistency import Archive
from preview_restore import helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
HASHES={1:'c3d23700267209f703c89c6b1d2d040785f0854ef1cdc71caf541031d29f3a80',2:'dd48886ab4320934e28df9e6b5b6fcaebce3231ff20314298d15f5d0a63f2cf7'}
def quantize(crop,pal,method):
    arr=np.array(crop);rgb=arr[:,:,:3].astype(np.float32);alpha=arr[:,:,3].astype(np.float32)/255
    if method=='nearest':
        q=np.array(crop.resize((96,96),Image.Resampling.NEAREST));z=1+((q[:,:,:3].astype(np.float32)[:,:,None,:]-pal[None,None,1:,:])**2).sum(3).argmin(2).astype(np.uint8);z[q[:,:,3]<128]=0;return z
    labs=np.zeros(arr.shape[:2],np.uint8)
    for y in range(arr.shape[0]):labs[y]=1+((rgb[y,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
    votes=np.stack([np.array(Image.fromarray(np.where(labs==i,alpha,0).astype(np.float32)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
    coverage=np.array(Image.fromarray(alpha).resize((96,96),Image.Resampling.BOX));z=1+votes.argmax(0).astype(np.uint8);z[coverage<.5]=0;return z
def main():
    ap=argparse.ArgumentParser();ap.add_argument('page',type=int,choices=(1,2));args=ap.parse_args();j=args.page;src=D/f'art{j:02}_generated.png';assert sha(src)==HASHES[j]
    p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';assert sha(p)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e';a=Archive(p.read_bytes())
    im=Image.open(src).convert('RGBA');out=D/f'registered_neutral{j:02}';out.mkdir(exist_ok=False);rows=[];frames=[]
    for cell,(n,mask)in enumerate(((221,8),(221,15),(223,8),(223,15))if j==1 else((225,8),(225,15),(227,8),(227,15))):
        form='base_legs'if mask==8 else'fourth';start=0 if mask==8 else 16
        box=tuple(round(v)for v in(cell%2*im.width/2,cell//2*im.height/2,(cell%2+1)*im.width/2,(cell//2+1)*im.height/2))
        pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32);cols=[('idle',a.composite(0,mask)[0]),('current',a.composite(n,mask)[0])]
        for method in('vote','nearest'):
            z=np.zeros((384,384),np.uint8);z[112:208,112:208]=quantize(im.crop(box),pal,method);pic=a.rgba(z,start)
            Image.fromarray(z).save(out/f'{form}_{n:03}_{method}_indices.png');pic.save(out/f'{form}_{n:03}_{method}_rgba.png');cols.append((method,pic))
            frames.append({'ref':n,'mask':mask,'form':form,'method':method,'source_crop':box,'bbox':pic.getbbox(),'old_bbox':a.composite(n,mask)[0].getbbox(),'components8':int(label(z>0,np.ones((3,3)))[1]),'indices_sha256':hashlib.sha256(z.tobytes()).hexdigest(),'body_translation':[0,0],'bbox_rescale':False})
        rows.append((f'{form} hover {n}',cols))
    for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',5)
    data={'source_sha256':sha(src),'parent_sha256':sha(p),'source_size':list(im.size),'palette_rgb':pal.astype(int).tolist(),'method':'고정96셀 면적투표와 최근접 샘플 비교. 다른 캐릭터 눈 색상 규칙 사용 없음.','frames':frames,'prior_registration':'registered01은 Nana용14번 눈강제 규칙을 포함하여 최종후보에서 제외. 이 비교에서 다시등록.','native_packed':False,'runtime_verified':False}
    (out/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'palette':data['palette_rgb'],'frames':frames}))
if __name__=='__main__':main()
