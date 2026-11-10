"""51의 새 부츠 원화를 발목 아래에서만 접지 폭/원점에 등록한다."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'));reg=json.loads((D/'basic_registered_v1/registration.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());out=D/'basic_registered_v2';out.mkdir(exist_ok=True);palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);rows=[];reports=[]
    for r in reg['frames']:
        n=r['ref'];old=np.array(Image.open(D/'basic_registered_v1'/f'base_{n:03}.png'));target=old.copy()
        if n==51:
            crop=Image.open(D/'basic_registered_v1/source_051.png').convert('RGBA');arr=np.array(crop).astype(float);ox,oy=r['native_position'];ey=r['target_eye'][1];scale=8;size=80;Y,X=np.indices((size*scale,size*scale),dtype=float);x=X/scale-40+.5/scale;y=Y/scale-40+.5/scale;weight=np.clip((y-17)/5,0,1)
            # Each shoe stays within its own leg. No cross-leg nearest source,
            # skin fill or horizontal sleeve scaling is used.
            native_sx=np.where(x<0,-7+(x-(-7-weight))/(1-weight*2/7),x+2*weight)
            sx=(native_sx-ox)*crop.width/r['native_width']-.5;sy=np.where(y<ey+1,(y-oy)*r['split']/r['height_above'],r['split']+(y-ey-1)*(crop.height-r['split'])/r['height_below'])-.5
            alpha=arr[:,:,3]/255;aa=map_coordinates(alpha,[sy,sx],order=1,mode='constant',cval=0);rgba=np.zeros((size*scale,size*scale,4),np.uint8)
            for ci in range(3):rgba[:,:,ci]=np.rint(map_coordinates(arr[:,:,ci]*alpha,[sy,sx],order=1,mode='constant',cval=0)/np.maximum(aa,.00001)).clip(0,255).astype(np.uint8)
            rgba[:,:,3]=np.rint(aa*255).astype(np.uint8);native=register(Image.fromarray(rgba),(size,size),palette,'area_vote');auth=np.zeros_like(target);auth[120:200,120:200]=native;region=np.indices(target.shape)[0]>=177;target[region]=auth[region];need(np.array_equal(old[:177],target[:177]),'Ankle-upper changed');need(np.where(target>0)[0].max()==182,'Ground height changed')
        Image.fromarray(target).save(out/f'base_{n:03}.png');a.rgba(target).save(out/f'base_{n:03}_rgba.png');rows.append((f'air {n}',[('대기',a.composite(0)[0]),('기존',a.composite(n)[0]),('새 등록 v1',a.rgba(old)),('국소접지 v2',a.rgba(target))]));rr=dict(r);rr['indexed_sha256']=sha(target.tobytes());rr['boot_local_registration']=n==51;rr['changed_vs_v1']=int(np.count_nonzero(old!=target));reports.append(rr)
    helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'source_art_sha256':reg['source_art_sha256'],'source_arc_sha256':sha(a.data),'frames':reports,'scope':'51 발목 아래 같은 새 원화의 부츠만 국소 좌표정합. 다른3원화와51상체·다리윗부분exact.','native_packed':False,'runtime_verified':False});print(json.dumps({'out':str(out),'changes':{r['ref']:r['changed_vs_v1']for r in reports}}))
if __name__=='__main__':main()
