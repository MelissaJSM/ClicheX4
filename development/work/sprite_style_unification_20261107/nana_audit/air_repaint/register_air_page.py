"""동일 스타일 공중 원화 페이지를 기존 눈과 발 높이에 등록한다."""
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
PAGES={'middle':('basic_middle_v1',[35,37,41,43],'5adc329339b48664269137ee9ed076cf806832a01cd3eb82f7b617bd9ff3571b'),
       'landing':('basic_landing_v1',[45,49,53],'9fc89d9f0b09e0985cc3e597b8a8689ea6c59ae1da7993878ab470fde370bc8c'),
       'fire_a':('basic_firing_a_v1',[34,36,38,40],'3ddb34470be4fe12db0ee4e0951c3a72cd9c4717546622a9c2cc92079d6bd5e7'),
       'fire_b':('basic_firing_b_v1',[42,44,46,48],'64db1ba9268132f3c8876f3d66a0674a713bfde382cdc6edb9b54b3faa3a7c16'),
       'fire_c':('basic_firing_c_v1',[50,52,54],'e2912a10154a6548cefe50c3e674fd2c13c77ebe16fcf6d233e4c3a0944d06bf'),
       'fire_c_reach':('landing_reach_generated_v1',[50,52],'d3eebcc3a85436d6278b1fe0a9cf0461b9fa03f8efa8ad605c8e2a93507e38f7')}
def crop_count(im,i,count):
    if count==4:return crop_cell(im,i)
    arr=np.array(im);labs,_=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;objects=[]
    for k in np.flatnonzero(sizes>1000):
        y,x=np.nonzero(labs==k);box=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1));objects.append((float(y.mean())>im.height/2,float(x.mean()),int(k),box))
    need(len(objects)==count,'Exact source figure count');_,_,k,box=sorted(objects)[i];arr[labs!=k,3]=0
    return Image.fromarray(arr).crop(box),box
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',choices=PAGES,default='middle');ap.add_argument('--out',default=None);args=ap.parse_args()
    folder,refs,expected=PAGES[args.page];p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes())
    need(sha(a.data)==p['parent_arc_sha256'],'Parent');source=D/folder/'generated.png';need(digest(source)==expected,'Generated art')
    im=Image.open(source).convert('RGBA');out=D/(args.out or folder.replace('_v1','_registered_v2'));need(not out.exists(),'Fresh output');out.mkdir()
    palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);reports=[];rows=[]
    for k,n in enumerate(refs):
        original=next(f for f in p['frames']if f['ref']==n);crop,box=crop_count(im,k,len(refs));crop.save(out/f'source_{n:03}.png');sx,sy=eye(crop);ex,ey=[int(np.floor(v))for v in original['eye']]
        opaque=np.array(crop)[:,:,3]>=128;yy,_=np.nonzero(opaque&(np.indices(opaque.shape)[1]<sx+crop.width*.15));crown=float(yy.min())
        if n==41:
            # The raised back hand crosses the broad head box at source y21.
            # The actual beret crown is y34, confirmed in this authored image.
            # Keep the accepted 9px crown-to-eye scale; do not shrink the head
            # by accidentally measuring from the hand instead of the beret.
            crown=34.0
        if n%2==0:
            # Pistol/raised-back-arm must not become the crown measurement.
            yy,_=np.nonzero(opaque&(np.indices(opaque.shape)[1]>=sx-30)&(np.indices(opaque.shape)[1]<sx+30));crown=float(yy.min())
        scale=10/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);top=ey-round(split*scale)+1;hu=ey-top+1;hl=original['bbox'][3]-ey-1
        upper=register(crop.crop((0,0,crop.width,split)),(width,hu),palette,'area_vote');lower=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),palette,'area_vote');native=np.concatenate((upper,lower));ec=round((sx+.5)*width/crop.width-.5)
        native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14;ox=ex-ec
        target=np.zeros((384,384),np.uint8);target[160+top:160+top+len(native),160+ox:160+ox+width]=native
        Image.fromarray(target).save(out/f'base_{n:03}.png');a.rgba(target).save(out/f'base_{n:03}_rgba.png');yy,xx=np.nonzero(target)
        need(int(yy.max()-160)==original['bbox'][3]-1,'Foot height');components=label(target>0,np.ones((3,3)))[1]
        reports.append({'ref':n,'source_crop':box,'source_eye':[sx,sy],'source_crown':crown,'source_scale_x':scale,'native_position':[ox,top],
                        'native_width':width,'split':split,'height_above':hu,'height_below':hl,'target_eye':[ex,ey],'original_eye_centroid':original['eye'],
                        'head_crown_to_eye_target':9,'foot_max_y':int(yy.max()-160),'native_bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],
                        'old_art_pixels_used':0,'alpha_components_8':components,'indexed_sha256':sha(target.tobytes())})
        rows.append((f'air {n}',[('대기 기준',a.composite(0)[0]),('기존',a.composite(n)[0]),('새 공중',a.rgba(target)),('새 연결키33',Image.open(D/'basic_registered_v2/base_033_rgba.png').convert('RGBA'))]))
    helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'source_arc_sha256':sha(a.data),'source_art_sha256':expected,'frames':reports,
         'scope':'새4키 전신 원화에서 직접 등록; 기존 머리/몸/하체 덮기 없음. 정적 미술 후보이며 네이티브 패킹 전.', 'native_packed':False,'runtime_verified':False})
    print(json.dumps({'out':str(out),'frames':reports}))
if __name__=='__main__':main()
