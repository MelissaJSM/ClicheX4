"""대시 종료83/공중 대시94의 새 전신 원화를 고정 게임 팔레트에 등록."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from refine_second_inputs import one,crop_count
from preview_restore import Archive,sha,digest,need,write,helper
def horizontal_crop(im,i):
    arr=np.asarray(im).copy();labs,_=label(arr[:,:,3]>=128,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0;objects=[]
    for k in np.flatnonzero(counts>1000):
        yy,xx=np.nonzero(labs==k);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];objects.append((float(xx.mean()),int(k),box))
    need(len(objects)==2,'Two full bodies');_,k,box=sorted(objects)[i];arr[labs!=k,3]=0
    return Image.fromarray(arr).crop(box),box
def main():
    doc=json.loads((D/'inputs.json').read_text('utf8'));arc=Archive((ROOT/doc['parent_arc']).read_bytes());need(sha(arc.data)==doc['parent_arc_sha256'],'Parent')
    src=D/'basic_last_v1/generated.png';expected='bd02f987bc27bd5fb8408c122e124b284e0eb9bb6d89bf1ba475cdcd8b3909f8';need(digest(src)==expected,'Art')
    im=Image.open(src).convert('RGBA');out=D/'basic_last_registered_v2';need(not out.exists(),'Fresh output');out.mkdir()
    pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[:16]],np.float32);rows=[];frames=[]
    for i,n in enumerate((83,94)):
        q=next(q for q in doc['frames']if q['ref']==n);crop,box=horizontal_crop(im,i);new,r=one(crop,q,pal);crop.save(out/f'source_{n:03}.png');Image.fromarray(new).save(out/f'base_{n:03}.png');arc.rgba(new).save(out/f'base_{n:03}_rgba.png')
        yy,xx=np.nonzero(new);need(yy.max()-160==q['bbox'][3]-1,'Floor')
        r.update(ref=n,source_crop=box,source_art_sha256=expected,foot_y=int(yy.max()-160),native_bbox=[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],components_8=int(label(new>0,np.ones((3,3)))[1]),old_art_pixels_used=0,indexed_sha256=sha(new.tobytes()));frames.append(r)
        rows.append((f'dash {n}',[('대기',arc.composite(0)[0]),('기존',arc.composite(n)[0]),('새 전신 원화',arc.rgba(new)),('새 연결67',Image.open(D/'basic_contacts_v2/base_067_rgba.png').convert('RGBA'))]))
    helper.grid(rows,out/'comparison.png',8);write(out/'registration.json',{'source_arc_sha256':sha(arc.data),'frames':frames,'native_packed':False,'runtime_verified':False});print(json.dumps(frames))
if __name__=='__main__':main()
