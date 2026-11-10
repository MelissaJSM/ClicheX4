"""새 Ultimate 의상 원화를 고정 셀에 등록한다. 기존 몸체 재덮기 없음."""
from pathlib import Path
import argparse
import json
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

def bounds(z):
    yy,xx=np.nonzero(z)
    return [int(xx.min())-160,int(yy.min())-160,int(xx.max())-159,int(yy.max())-159]

def eye(z,center=None):
    Y,X=np.indices(z.shape)
    search=(Y<160)
    if center is not None:
        search&=(abs(X-center[0])<=5)&(abs(Y-center[1])<=4)
    points=(z==14)&search
    if center is not None:
        labs,count=label(points,np.ones((3,3)))
        need(count>0,'원 눈 좌표 부근 홍채 없음')
        ranked=[]
        for k in range(1,count+1):
            cy,cx=np.nonzero(labs==k)
            distance=float(((cx-center[0])**2+(cy-center[1])**2).min())
            ranked.append((distance,k))
        points=labs==min(ranked)[1]
    yy,xx=np.nonzero(points)
    need(len(xx)>0,'홍채 표본 없음')
    top=int(yy.min())
    return int(np.median(xx[yy==top])),top

def indices(a,n,mask):
    z=a.layer(n)[0].copy()
    if mask:
        for pb in(8,5,7,6):
            p=a.layer(n,pb)[0]
            z[p>0]=p[p>0]
    return z

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--page',choices=['air','charge','recovery'],required=True)
    ap.add_argument('--version',default='v1')
    args=ap.parse_args()
    art=D/f'ultimate_{args.page}_v1/generated.png'
    gen=json.loads((art.parent/'generation.json').read_text('utf8'))
    expected=gen.get('workspace_sha256',gen.get('generated_sha256'))
    need(digest(art)==expected,'원화 해시 불일치')
    u_path=N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC'
    b_path=D/'packed_base_candidate_v1/PL00_U.ARC'
    meta=json.loads((D/'ultimate_inputs_v1/manifest.json').read_text('utf8'))
    need(digest(u_path)==meta['ultimate_style_arc_sha256'],'Ultimate 부모')
    need(digest(b_path)==meta['pose_arc_sha256'],'신규 포즈 부모')
    u,b=Archive(u_path.read_bytes()),Archive(b_path.read_bytes())
    out=D/f'ultimate_{args.page}_registered_{args.version}'
    out.mkdir(exist_ok=False)
    im=Image.open(art).convert('RGBA')
    rows=[];records=[]
    page=next(q for q in meta['pages']if q['page']==args.page)
    for q in page['frames']:
        i,n,mask=q['cell'],q['ref'],q['ultimate_mask']
        form='before'if mask else'after';start=16 if mask else 0
        crop=tuple(round(v)for v in(i%2*im.width/2,i//2*im.height/2,(i%2+1)*im.width/2,(i//2+1)*im.height/2))
        cell=im.crop(crop);arr=np.array(cell)
        labs,_=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0
        need(sum(sizes>1000)==1,'불투명 전신 1개 필요')
        pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in u.words[start:start+16]],np.float32)
        fixed=np.zeros((384,384),np.uint8)
        fixed[112:208,112:208]=register(cell,(96,96),pal,'area_vote')
        pose=indices(b,n,15)
        ex,ey=eye(pose);sx,sy=eye(fixed,(ex,ey));dx,dy=ex-sx,ey-sy
        need(abs(dx)<=4 and abs(dy)<=4,'원점 예상범위 초과')
        target=np.roll(fixed,(dy,dx),(0,1))
        need(not target[:80].any()and not target[-80:].any()and not target[:,:80].any()and not target[:,-80:].any(),'등록 영역 초과')
        for name,z in [('fixed',fixed),('registered',target)]:
            Image.fromarray(z).save(out/f'{form}_{n:03}_{name}_indices.png')
        u.rgba(target,start).save(out/f'{form}_{n:03}_rgba.png')
        red=(arr[:,:,0]>180)&(arr[:,:,1]<60)&(arr[:,:,2]<70)
        aa,cc=np.unique(arr[:,:,3][red],return_counts=True)
        records.append({'ref':n,'form':form,'mask':mask,'crop':list(crop),'native_cell':[96,96],
                        'source_fixed_eye_world':[sx-160,sy-160],'target_eye_world':[ex-160,ey-160],
                        'whole_translation':[dx,dy],'old_bbox_world':bounds(indices(u,n,mask)),
                        'new_bbox_world':bounds(target),'pose_bbox_world':bounds(pose),
                        'opaque_source_figure_components':int(sum(sizes>1000)),
                        'source_red_alpha_histogram':{str(int(a)):int(c)for a,c in zip(aa,cc)},
                        'native_components_8':int(label(target>0,np.ones((3,3)))[1]),
                        'native_sha256':sha(target.tobytes()),'old_body_pixels_copied':0})
        rows.append((f'{form} {n}',[('accepted idle',u.composite(0,mask)[0]),('old Ultimate',u.composite(n,mask)[0]),
                                   ('approved pose only',b.composite(n,15)[0]),('new fixed registration',u.rgba(target,start))]))
    for j in range(0,len(rows),2):helper.grid(rows[j:j+2],out/f'comparison_{j//2+1}.png',6)
    write(out/'registration.json',{'source_art_path':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),
                                  'source_size':list(im.size),'ultimate_arc_sha256':digest(u_path),'pose_arc_sha256':digest(b_path),
                                  'method':'원화 전체 셀을 96px로 면적투표 등록한 뒤 수용 포즈 눈에 가장 가까운 초록 연결영역을 홍채로 읽어 전체 평행이동. 별도 초록 장식을 홍채로 오인하지 않음. 원화 알파 그대로 사용, 배경색 삭제·낱부위 축척·옛 몸체 재덮기 없음.',
                                  'frames':records,'canonical_pistol_applied':False,'hand_feet_contacts_verified':False,
                                  'native_packed':False,'runtime_verified':False})
    print(json.dumps({'page':args.page,'frames':records},ensure_ascii=True))

if __name__=='__main__':main()
