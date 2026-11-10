"""첫 대시 4키를 고정 CLUT와 원 눈·발 높이에 등록하는 미술 후보."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint'),str(D.parent/'wall_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register,crop_cell
from register_fourth_wall import eye
EXPECTED='4ef76f709b4e6e6dac3c51d4b3037ee09e028542b66a896d48f59d48e8f27b8a'
PAGES={'first':('basic_first_v1',(67,71,79,93),EXPECTED,'basic_registered_v1'),
       'second':('basic_second_v1',(69,75,77,81),'e5a77b44c03d7b1d7d0274d984da509861fefa26b2132360d152c71ba0d8a8c3','basic_second_registered_v1')}
def quadrant_crop(im,k):
    x0=k%2*im.width//2;y0=k//2*im.height//2;cell=im.crop((x0,y0,x0+im.width//2,y0+im.height//2));arr=np.array(cell);labs,_=label(arr[:,:,3]>=128,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0;objects=np.flatnonzero(counts>1000);need(len(objects)==1,'One connected figure required');yy,xx=np.nonzero(labs==objects[0]);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];arr[labs!=objects[0],3]=0;return Image.fromarray(arr).crop(box),[box[0]+x0,box[1]+y0,box[2]+x0,box[3]+y0]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',choices=PAGES,default='first');args=ap.parse_args();folder,refs,expected,output=PAGES[args.page]
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());need(sha(a.data)==p['parent_arc_sha256'],'Parent');src=D/folder/'generated.png';need(digest(src)==expected,'Source art');im=Image.open(src).convert('RGBA');out=D/output;need(not out.exists(),'Fresh output');out.mkdir();pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);proof=[];rows=[]
    for k,n in enumerate(refs):
        if n==75:continue # Detached boot in generated source: rejected, not silently dropped.
        q=next(q for q in p['frames']if q['ref']==n);crop,box=(crop_cell(im,k)if args.page=='first'else quadrant_crop(im,k));crop.save(out/f'source_{n:03}.png');sx,sy=eye(crop);ex,ey=[int(np.floor(v))for v in q['eye']]
        arr=np.array(crop);Y,X=np.indices(arr.shape[:2]);opaque=arr[:,:,3]>=128;yy,_=np.nonzero(opaque&(X<sx+crop.width*.15));crown=float(yy.min());scale=10/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);top=ey-round(split*scale)+1;hu=ey-top+1;hl=q['bbox'][3]-ey-1
        upper=register(crop.crop((0,0,crop.width,split)),(width,hu),pal,'area_vote');lower=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),pal,'area_vote');native=np.concatenate((upper,lower));ec=round((sx+.5)*width/crop.width-.5);native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14;ox=ex-ec
        target=np.zeros((384,384),np.uint8);target[160+top:160+top+len(native),160+ox:160+ox+width]=native;Image.fromarray(target).save(out/f'base_{n:03}.png');a.rgba(target).save(out/f'base_{n:03}_rgba.png');yy,xx=np.nonzero(target);need(int(yy.max()-160)==q['bbox'][3]-1,'Foot height')
        proof.append({'ref':n,'source_crop':box,'source_eye':[sx,sy],'source_crown':crown,'source_scale_x':scale,'native_position':[ox,top],'native_width':width,'split':split,'height_above':hu,'height_below':hl,'target_eye':[ex,ey],'original_eye_centroid':q['eye'],'head_crown_to_eye_target':9,'foot_max_y':int(yy.max()-160),'native_bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'alpha_components_8':int(label(target>0,np.ones((3,3)))[1]),'old_art_pixels_used':0,'indexed_sha256':sha(target.tobytes())})
        rows.append((f'dash {n}',[('승인 대기',a.composite(0)[0]),('기존 대시',a.composite(n)[0]),('새 원화 직접등록',a.rgba(target)),('새 공중',a.composite(39)[0])]))
    helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'source_arc_sha256':sha(a.data),'source_art_sha256':expected,'frames':proof,'rejected_source_refs':[75]if args.page=='second'else[],'native_packed':False,'runtime_verified':False,'scope':'새 전신 원화 직접등록 미술 후보. 발 X접점·권총 별도검사 전. 옛 머리/하체 덮기 없음.'});print(json.dumps(proof))
if __name__=='__main__':main()
