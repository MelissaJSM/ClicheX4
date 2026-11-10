"""네 피격 원화의 전체 셀 고정배율 등록. 기존 머리·몸 덮기 없음."""
from pathlib import Path
import json,argparse
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import label

D=Path(__file__).resolve().parent
N=D.parent
ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,digest,sha,need,write,helper
from register_page import register

def bbox(z):
    y,x=np.nonzero(z)
    return [int(x.min())-160,int(y.min())-160,int(x.max())-159,int(y.max())-159]

def eye(z,center=None):
    Y,X=np.indices(z.shape)
    m=(z==14)&(Y<160)
    if center is not None:
        m&=(abs(X-center[0])<=5)&(abs(Y-center[1])<=5)
        labs,n=label(m,np.ones((3,3)))
        need(n>0,'원래 눈 부근에 초록 표본 필요')
        ranked=[]
        for k in range(1,n+1):
            y,x=np.nonzero(labs==k)
            ranked.append((float(((x-center[0])**2+(y-center[1])**2).min()),k))
        m=labs==min(ranked)[1]
    y,x=np.nonzero(m)
    need(len(x)>0,'눈 표본 누락')
    top=int(y.min())
    return int(np.median(x[y==top])),top

def indices(a,n,mask):
    z=a.layer(n)[0].copy()
    if mask:
        for pb in (8,5,7,6):
            p=a.layer(n,pb)[0]
            z[p>0]=p[p>0]
    return z

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',choices=['first','extra'],default='first');args=ap.parse_args()
    meta=json.loads((D/f'{args.page}_inputs_v1/manifest.json').read_text('utf8'))
    arc=ROOT/meta['source_arc']
    need(digest(arc)==meta['source_arc_sha256'],'부모 해시 불일치')
    art=D/f'{args.page}_v1/generated.png'
    gen=json.loads((art.parent/'generation.json').read_text('utf8'))
    need(digest(art)==gen['workspace_sha256'],'원화 해시 불일치')
    a=Archive(arc.read_bytes())
    im=Image.open(art).convert('RGBA')
    out=D/f'{args.page}_registered_v1'
    out.mkdir(exist_ok=True)
    need(not (out/'registration.json').exists(),'기존 등록 결과 덮어쓰기 거부')
    records=[]; rows=[]
    for q in meta['frames']:
        i,n,mask=q['cell'],q['ref'],q['mask'];form=q['form'];start=16 if mask else 0
        crop=tuple(round(v)for v in(i%2*im.width/2,i//2*im.height/2,(i%2+1)*im.width/2,(i//2+1)*im.height/2))
        cell=im.crop(crop);arr=np.array(cell)
        labs,_=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0
        need(sum(sizes>1000)==1,'한 셀에 전신 하나 필요')
        palette=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
        fixed=np.zeros((384,384),np.uint8)
        fixed[112:208,112:208]=register(cell,(96,96),palette,'area_vote')
        old=indices(a,n,mask)
        # 피격 원화의 감긴 눈에는 초록 홍채가 없다. 무관한 가슴 장식을 눈으로 쓰지 않는다.
        ex=ey=sx=sy=None
        dx=dy=0
        if args.page=='extra':
            ex,ey=eye(old);sx,sy=eye(fixed,(ex,ey));dx,dy=ex-sx,ey-sy
            need(abs(dx)<=4 and abs(dy)<=4,'눈 정합 이동 과대')
        final=np.roll(fixed,(dy,dx),(0,1))
        for name,z in [('fixed',fixed),('registered',final)]:
            Image.fromarray(z).save(out/f'{form}_{n:03}_{name}_indices.png')
        a.rgba(final,start).save(out/f'{form}_{n:03}_rgba.png')
        red=(arr[:,:,0]>180)&(arr[:,:,1]<60)&(arr[:,:,2]<70)
        aa,cc=np.unique(arr[:,:,3][red],return_counts=True)
        records.append({'ref':n,'form':form,'mask':mask,'cell':i,'source_crop':list(crop),'fixed_cell_size':[96,96],
                        'old_bbox_world':bbox(old),'fixed_bbox_world':bbox(fixed),'new_bbox_world':bbox(final),
                        'old_eye_world':[ex-160,ey-160]if ex is not None else None,'fixed_eye_world':[sx-160,sy-160]if sx is not None else None,
                        'translation':[dx,dy],'new_eye_world':[ex-160,ey-160]if ex is not None else None,
                        'source_red_alpha_histogram':{str(int(k)):int(v)for k,v in zip(aa,cc)},
                        'native_components_8':int(label(final>0,np.ones((3,3)))[1]),
                        'native_sha256':sha(final.tobytes()),'old_pixels_copied':0})
        rows.append((f'{form} {n}',[('idle',a.composite(0,mask)[0]),('old hurt',a.composite(n,mask)[0]),
                                   ('fixed cell',a.rgba(fixed,start)),('registered',a.rgba(final,start))]))
    for k in range(0,len(rows),2):
        helper.grid(rows[k:k+2],out/f'comparison_{k//2+1}.png',6)
    write(out/'registration.json',{'source_art_path':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),
                                  'source_size':list(im.size),'parent_arc':meta['source_arc'],'parent_arc_sha256':digest(arc),
                                  'method':'전체 627px 셀을 native96px로 면적투표.106/110 감긴 눈은 자동눈정합 거부/이동0.233/234는 원초록눈 인근 홍채로 전신 평행이동. bbox 축척·행 삭제·기존 몸체 복사 없음.',
                                  'frames':records,'geometry_status':'고정 전체셀 초기등록. 얼굴·손·무릎·발과 양의상 공통층은 후속 검사.',
                                  'native_packed':False,'runtime_verified':False})
    print(json.dumps({'out':str(out),'frames':records},ensure_ascii=True))

if __name__=='__main__':
    main()
