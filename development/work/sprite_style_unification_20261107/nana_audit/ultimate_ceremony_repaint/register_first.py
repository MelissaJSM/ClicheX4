"""등장4 원화를 고정96셀로 등록하고 원 눈/발 위치를 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
from register_page import register
def bbox(z):
    y,x=np.nonzero(z);return[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]
def eye(z,center=None):
    y,x=np.indices(z.shape);mask=(z%16==14)&(y<160)
    if center:mask&=(abs(x-center[0])<=5)&(abs(y-center[1])<=5)
    yy,xx=np.nonzero(mask);need(len(xx)>0,'눈 실제표본');top=yy.min();return int(np.median(xx[yy==top])),int(top)
def full(a,n,mask):
    z=a.layer(n)[0].copy()
    if mask:
        for pb in(8,5,7,6):v=a.layer(n,pb)[0];z[v>0]=v[v>0]
    return z
def main():
    inputs=D/'first_inputs_v1';meta=json.loads((inputs/'manifest.json').read_text('utf8'));src=ROOT/meta['source_arc'];need(digest(src)==meta['source_arc_sha256'],'부모')
    gen=json.loads((D/'first_v1/generation.json').read_text('utf8'));art=ROOT/gen['workspace_path'];need(digest(art)==gen['workspace_sha256'],'생성물 해시');im=Image.open(art).convert('RGBA');a=Archive(src.read_bytes())
    out=D/'first_registered_v2';out.mkdir(exist_ok=False);records=[];rows=[]
    for q in meta['frames']:
        i,n,mask=q['cell'],q['ref'],q['mask'];form=q['form'];start=16 if mask else 0
        crop=tuple(round(v)for v in(i%2*im.width/2,i//2*im.height/2,(i%2+1)*im.width/2,(i//2+1)*im.height/2));cell=im.crop(crop);arr=np.array(cell)
        labs,k=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;need(sum(sizes>1000)==1,'단일 전신')
        pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
        fixed=np.zeros((384,384),np.uint8);fixed[112:208,112:208]=register(cell,(96,96),pal,'area_vote');old=full(a,n,mask)
        ex=ey=sx=sy=None;dx=dy=0
        if n==133:
            ex,ey=eye(old);sx,sy=eye(fixed,(ex,ey));dx,dy=ex-sx,ey-sy;need(abs(dx)<=3 and abs(dy)<=3,'눈 정합 이탈')
        # 135는 현재 감긴 눈이므로 무관한 초록장식을 홍채로 쓰지 않는다.
        final=np.roll(fixed,(dy,dx),(0,1))
        for name,z in [('fixed',fixed),('registered',final)]:Image.fromarray(z).save(out/f'{form}_{n:03}_{name}_indices.png')
        a.rgba(final,start).save(out/f'{form}_{n:03}_rgba.png');oldbb=bbox(old);newbb=bbox(final)
        red=(arr[:,:,0]>180)&(arr[:,:,1]<60)&(arr[:,:,2]<70);aa,cc=np.unique(arr[:,:,3][red],return_counts=True)
        record={'ref':n,'form':form,'mask':mask,'cell':i,'source_crop':list(crop),'old_bbox_world':oldbb,'fixed_bbox_world':bbox(fixed),'new_bbox_world':newbb,'old_eye_world':[ex-160,ey-160]if ex is not None else None,'fixed_eye_world':[sx-160,sy-160]if sx is not None else None,'translation':[dx,dy],'floor_delta':newbb[3]-oldbb[3],'source_red_alpha_histogram':{str(int(k)):int(v)for k,v in zip(aa,cc)},'native_components_8':int(label(final>0,np.ones((3,3)))[1]),'native_sha256':sha(final.tobytes()),'old_pixels_copied':0}
        records.append(record);rows.append((f'{form} {n}',[('idle',a.composite(0,mask)[0]),('previous',a.composite(n,mask)[0]),('new fixed',a.rgba(fixed,start)),('eye registered',a.rgba(final,start))]))
    for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
    write(out/'registration.json',{'source_art_path':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_size':list(im.size),'parent_arc_sha256':digest(src),'method':'실제627셀→96native 면적투표,전체원화 원점 고정 후 실제녹색홍채 평행정합만. bbox자동축척/행삭제/옛머리덮기 없음.','frames':records,'native_packed':False,'runtime_verified':False})
    print(json.dumps([{k:q[k]for k in('ref','form','translation','floor_delta','native_components_8','old_bbox_world','new_bbox_world')}for q in records]))
if __name__=='__main__':main()
