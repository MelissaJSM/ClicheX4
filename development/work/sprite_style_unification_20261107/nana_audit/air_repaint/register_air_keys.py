"""새 공중4키를 수용된 벽 머리 스케일과 원래 눈/발 높이로 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint'),str(D.parent/'wall_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register,crop_cell
from register_fourth_wall import eye
EXPECTED='48908914c410d6530acf90c3013adf4a5d353e6ea5ff67d45620d1e9c0f4ea9a'
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(a.data)==plan['parent_arc_sha256'],'Parent');src=D/'basic_keys_v1/generated.png';need(digest(src)==EXPECTED,'Source art');im=Image.open(src).convert('RGBA');out=D/'basic_registered_v1';out.mkdir(exist_ok=True);palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);records=[];rows=[]
    for k,n in enumerate(plan['first_keys']):
        p=next(p for p in plan['frames']if p['ref']==n);crop,box=crop_cell(im,k);crop.save(out/f'source_{n:03}.png');sx,sy=eye(crop);ex,ey=map(lambda v:int(np.floor(v)),p['eye']);opaque=np.array(crop)[:,:,3]>=128;yy,_=np.nonzero(opaque&(np.indices(opaque.shape)[1]<sx+crop.width*.15));crown=float(yy.min())
        # The old air art has a shrinking head in some refs. The accepted new
        # wall master uses nine native pixels from crown to eye; use that scale
        # while fixing the original eye and actual bottom of the feet.
        top=ey-9;scale=10/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);native_top=ey-round(split*scale)+1;hu=ey-native_top+1;bottom=p['bbox'][3];hl=bottom-ey-1
        upper=register(crop.crop((0,0,crop.width,split)),(width,hu),palette,'area_vote');lower=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),palette,'area_vote');native=np.concatenate((upper,lower));ec=round((sx+.5)*width/crop.width-.5);native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14;ox=ex-ec
        target=np.zeros((384,384),np.uint8);target[160+native_top:160+native_top+len(native),160+ox:160+ox+width]=native;Image.fromarray(target).save(out/f'base_{n:03}.png');a.rgba(target).save(out/f'base_{n:03}_rgba.png');yy,xx=np.nonzero(target);need(int(yy.max()-160)==bottom-1,'Foot height')
        records.append({'ref':n,'source_crop':box,'source_eye':[sx,sy],'source_crown':crown,'source_scale_x':scale,'native_position':[ox,native_top],'native_width':width,'split':split,'height_above':hu,'height_below':hl,'original_eye_centroid':p['eye'],'target_eye':[ex,ey],'eye_anchoring':'original pupil cluster upper/left pixel if half-integer','head_crown_to_eye_target':9,'native_bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'foot_max_y':bottom-1,'old_art_pixels_used':0,'indexed_sha256':sha(target.tobytes())})
        rows.append((f'air {n}',[('대기 기준',a.composite(0)[0]),('기존 공중',a.composite(n)[0]),('새 전신 등록',a.rgba(target)),('새 벽 스타일',a.composite(63)[0])]))
    helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'source_arc_sha256':sha(a.data),'source_art_sha256':EXPECTED,'frames':records,'native_packed':False,'runtime_verified':False,'scope':'4키 미술 후보, 원화 전신 직접등록. 옛 단순 머리/하체/팔 덮기 없음.'});print(json.dumps({'out':str(out),'refs':plan['first_keys']}))
if __name__=='__main__':main()
