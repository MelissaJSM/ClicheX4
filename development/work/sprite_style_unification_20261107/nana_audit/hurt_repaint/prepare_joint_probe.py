"""새 피격 네 몸체를 부분 의상 소유로 나눈 초기 검토판."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
DATA={106:{'eye':[-1,-10],'lower':7,'arm':[[-16,-5],[-8,-10],[-3,-5],[-4,4],[-8,8],[-16,8]],'right_hand':[4,1,11,9]},
      110:{'eye':[0,-10],'lower':4,'arm':[[-12,-5],[-5,-10],[0,-6],[0,3],[-6,6],[-12,3]],'right_hand':[0,-2,6,4]},
      233:{'eye':[-4,-14],'lower':3,'arm':[[-15,-14],[-6,-16],[-3,-8],[-9,-4],[-15,-9]],'right_hand':[7,-7,14,2]},
      234:{'eye':[1,-12],'lower':3,'arm':[[-13,-23],[0,-24],[3,-17],[0,-12],[-6,-8],[-13,-13]],'right_hand':[-2,-11,7,-4]}}
def poly(points):
    from PIL import ImageDraw
    im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1)
    return np.array(im)>0
def composite(a,ls,mask,arm=2):
    im=a.rgba(ls[0])
    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
        if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
    return im
def main():
    out=D/'joint_layers_probe_v1';out.mkdir(exist_ok=False)
    parent=N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC';a=Archive(parent.read_bytes());src=D/'common_legs_probe_v1'
    rows=[];partials=[];records=[]
    for n,q in DATA.items():
        b=np.array(Image.open(src/f'base_{n:03}_indices.png'));f=np.array(Image.open(src/f'fourth_{n:03}_indices.png'));full=np.where(f,f,b).astype(np.uint8)
        ex,ey=q['eye'];owner=np.full(b.shape,6,np.uint8)
        leg=(Y>=q['lower'])|((X>=ex+13)&(Y>=ey+5))
        head=(Y<ey+6)&((X>=ex-3)|(Y<ey-2))
        owner[leg]=8;owner[head]=5;owner[poly(q['arm'])]=7
        x0,y0,x1,y1=q['right_hand'];hand=np.isin(full,(10,11,12,13))&(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1);owner[hand]=7
        pd=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full]
        change=((full!=b)|((f>0)&pd))&(full>0)
        ls={0:b,**{k:np.where(change&(owner==k),full,0).astype(np.uint8)for k in(5,6,7,8)}}
        exact=a.rgba(b);exact.alpha_composite(a.rgba(f,16))
        need(np.array_equal(np.array(composite(a,ls,15,1)),np.array(exact)),'포스 arm1 합성 원화 불일치')
        for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
        Image.fromarray(owner).save(out/f'owner_{n:03}.png')
        issues=[]
        for mask in range(16):
            for arm in(1,2):
                im=composite(a,ls,mask,arm);lab,count=label(np.array(im)[:,:,3]>0,np.ones((3,3)))
                sizes=np.bincount(lab.flat);sizes[0]=0
                if count>1:
                    issues.append({'mask':mask,'arm':arm,'components':count,'small_pixels':int(sizes[(sizes>0)&(sizes<4)].sum())})
        records.append({'ref':n,'base_sha256':sha(b.tobytes()),'authored_fourth_sha256':sha(f.tobytes()),
                        'layer_hashes':{str(k):sha(z.tobytes())for k,z in ls.items()},'layer_opaque':{str(k):int(np.count_nonzero(z))for k,z in ls.items()},
                        'owner_geometry':q,'partial_component_issues':issues})
        rows.append((f'hurt {n}',[('base idle',a.composite(0)[0]),('new base',a.rgba(b)),('Fourth idle',a.composite(0,15)[0]),('new Fourth arm2',composite(a,ls,15)),('new Fourth arm1',composite(a,ls,15,1))]))
        partials.append((f'partial {n}',[('head only',composite(a,ls,1)),('body only',composite(a,ls,2)),('arms only',composite(a,ls,4)),('legs only',composite(a,ls,8)),('body and legs',composite(a,ls,10))]))
    for k in range(0,4,2):
        helper.grid(rows[k:k+2],out/f'comparison_{k//2+1}.png',6);helper.grid(partials[k:k+2],out/f'partial_{k//2+1}.png',6)
    write(out/'manifest.json',{'parent_arc':parent.relative_to(ROOT).as_posix(),'parent_sha256':digest(parent),'source_manifest_sha256':digest(src/'manifest.json'),
                             'frames':records,'scope':'4몸체의5층 의미소유 초기안. 큰 뒤베일 leg8/윗머리head5 유지. 부수효과 미포함이며 부분착용 미술검토 전.',
                             'native_packed':False,'runtime_verified':False})
    print(json.dumps({q['ref']:{'opaque':q['layer_opaque'],'issues':q['partial_component_issues']}for q in records}))
if __name__=='__main__':main()
