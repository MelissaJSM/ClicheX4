"""새71 국소교정 원화의 다리/부츠만 이전 새 상체에 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint'),str(D.parent/'wall_repaint'),str(D.parent/'air_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register
from register_air_page import crop_count
from register_fourth_wall import eye
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());need(sha(a.data)==p['parent_arc_sha256'],'Parent');src=D/'dash71_boots_v1/generated.png';im=Image.open(src).convert('RGBA');crop,box=crop_count(im,0,1);sx,sy=eye(crop);q=next(q for q in p['frames']if q['ref']==71);ex,ey=[int(np.floor(v))for v in q['eye']];arr=np.array(crop);Y,X=np.indices(arr.shape[:2]);yy,_=np.nonzero((arr[:,:,3]>=128)&(X<sx+crop.width*.15));crown=float(yy.min());scale=10/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);top=ey-round(split*scale)+1;hu=ey-top+1;hl=q['bbox'][3]-ey-1;pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
    native=np.concatenate((register(crop.crop((0,0,crop.width,split)),(width,hu),pal,'area_vote'),register(crop.crop((0,split,crop.width,crop.height)),(width,hl),pal,'area_vote')));ec=round((sx+.5)*width/crop.width-.5);ox=ex-ec;source=np.zeros((384,384),np.uint8);source[top+160:top+160+len(native),ox+160:ox+160+width]=native;old=np.array(Image.open(D/'basic_registered_v1/base_071.png'));Y,X=np.indices(old.shape);mask=(Y>=175)&(X>=151)&(X<=174);new=old.copy();new[mask]=source[mask]
    need(np.array_equal(new[~mask],old[~mask]),'Upper preservation');need(int(np.nonzero(new)[0].max())==182,'Foot y');out=D/'dash71_boots_registered_v1';need(not out.exists(),'Fresh output');out.mkdir();crop.save(out/'source.png');Image.fromarray(source).save(out/'new_source_native.png');Image.fromarray(new).save(out/'base_071.png');a.rgba(new).save(out/'base_071_rgba.png');Image.fromarray(mask).save(out/'source_region.png');helper.grid([('dash71', [('대기',a.composite(0)[0]),('원래',a.composite(71)[0]),('첫 원화',a.rgba(old)),('새 다리만 등록',a.rgba(new)),('새 원화 전체 진단',a.rgba(source))])],out/'comparison.png',10);write(out/'registration.json',{'source_arc_sha256':sha(a.data),'source_art_sha256':digest(src),'source_crop':box,'source_eye':[sx,sy],'source_crown':crown,'native_position':[ox,top],'native_width':width,'height_above':hu,'height_below':hl,'edit_region_world':[-9,15,15,23],'changed_pixels':int(np.count_nonzero(old!=new)),'upper_exact':True,'alpha_components_8':int(label(new>0,np.ones((3,3)))[1]),'candidate_only':True,'native_packed':False,'runtime_verified':False});print(json.dumps({'out':str(out),'changed':int(np.count_nonzero(old!=new))}))
if __name__=='__main__':main()
