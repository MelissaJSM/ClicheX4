"""136/137 원화를 전체 셀 고정 축척으로 등록하고 효과 없는 몸을 대조한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,digest,sha,write,need,helper
from register_page import register
from register_first import bbox,full
def optional_eye(z):
    y,x=np.indices(z.shape);m=(z%16==14)&(y<160)&(x>140)&(x<180)
    yy,xx=np.nonzero(m)
    if not len(xx):return None
    top=yy.min();return [int(np.median(xx[yy==top])-160),int(top-160)]
def main():
    inputs=D/'second_inputs_v1';meta=json.loads((inputs/'manifest.json').read_text('utf8'));src=ROOT/meta['source_arc'];need(digest(src)==meta['source_arc_sha256'],'부모')
    gen=json.loads((D/'second_v1/generation.json').read_text('utf8'));art=ROOT/gen['workspace_path'];need(digest(art)==gen['workspace_sha256'],'생성물')
    im=Image.open(art).convert('RGBA');a=Archive(src.read_bytes());out=D/'second_registered_v1';out.mkdir(exist_ok=False);records=[];rows=[]
    for q in meta['frames']:
        i,n,mask=q['cell'],q['ref'],q['mask'];form=q['form'];start=16 if mask else 0
        crop=tuple(round(v)for v in(i%2*im.width/2,i//2*im.height/2,(i%2+1)*im.width/2,(i//2+1)*im.height/2));cell=im.crop(crop);arr=np.array(cell)
        labs,k=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;need(sum(sizes>1000)==1,'단일 전신')
        pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
        fixed=np.zeros((384,384),np.uint8);fixed[112:208,112:208]=register(cell,(96,96),pal,'area_vote')
        old=full(a,n,mask);fx=np.array(Image.open(inputs/f'effect_{n:03}_indices.png'));old[fx>0]=0
        oldbb=bbox(old);bb=bbox(fixed);red=(arr[:,:,0]>180)&(arr[:,:,1]<60)&(arr[:,:,2]<70);aa,cc=np.unique(arr[:,:,3][red],return_counts=True)
        Image.fromarray(fixed).save(out/f'{form}_{n:03}_indices.png');a.rgba(fixed,start).save(out/f'{form}_{n:03}_rgba.png')
        records.append({'ref':n,'form':form,'mask':mask,'cell':i,'source_crop':list(crop),'old_body_bbox_world':oldbb,'fixed_bbox_world':bb,'old_eye_world':optional_eye(old),'fixed_eye_world':optional_eye(fixed),'translation':[0,0],'floor_delta':bb[3]-oldbb[3],'source_red_alpha_histogram':{str(int(k)):int(v)for k,v in zip(aa,cc)},'native_components8':int(label(fixed>0,np.ones((3,3)))[1]),'native_sha256':sha(fixed.tobytes()),'old_pixels_copied':0})
        rows.append((f'{form} {n}',[('idle',a.composite(0,mask)[0]),('previous body',a.rgba(old,start)),('new fixed',a.rgba(fixed,start))]))
    for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
    write(out/'registration.json',{'source_art_path':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_size':list(im.size),'parent_arc_sha256':digest(src),'method':'실제 전체 셀을96native 면적투표로 등록. 알파/팔레트 고정, 원점이동·자동bbox축척·옛머리덮기 없음.','frames':records,'effects_reinserted':False,'native_packed':False,'runtime_verified':False})
    print(json.dumps([{k:q[k]for k in('ref','form','floor_delta','old_eye_world','fixed_eye_world','native_components8','old_body_bbox_world','fixed_bbox_world')}for q in records]))
if __name__=='__main__':main()
