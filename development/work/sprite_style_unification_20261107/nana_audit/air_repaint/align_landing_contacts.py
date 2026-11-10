"""49/53의 새 부츠만 같은 원화로 국소 정합하며 머리/무릎은 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,label
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'));reg=json.loads((D/'basic_landing_registered_v2/registration.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes())
    need(sha(a.data)==plan['parent_arc_sha256'],'Parent');out=D/'basic_landing_registered_v5';need(not out.exists(),'Fresh output');out.mkdir()
    palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);records=[];rows=[]
    for q in reg['frames']:
        n=q['ref'];old=np.array(Image.open(D/'basic_landing_registered_v2'/f'base_{n:03}.png'));target=old.copy()
        if n in(49,53):
            crop=Image.open(D/'basic_landing_registered_v2'/f'source_{n:03}.png').convert('RGBA');arr=np.array(crop).astype(float);ox,oy=q['native_position'];ey=q['target_eye'][1]
            size=80;scale=8;Y,X=np.indices((size*scale,size*scale),dtype=float);x=X/scale-40+.5/scale;y=Y/scale-40+.5/scale
            weight=np.clip((y-15)/7,0,1)
            if n==49:
                nx=np.where(x<0,-3.5+(x-(-3.5-weight))/(1-weight/4),x+2*weight)
                ny=np.where((x<0)&(y>=15),15+(y-15)*7.5/8,y)
            else:nx=np.where(x<0,x-2*weight,x+weight);ny=y
            sx=(nx-ox)*crop.width/q['native_width']-.5
            sy=np.where(ny<ey+1,(ny-oy)*q['split']/q['height_above'],q['split']+(ny-ey-1)*(crop.height-q['split'])/q['height_below'])-.5
            alpha=arr[:,:,3]/255;aa=map_coordinates(alpha,[sy,sx],order=1,mode='constant',cval=0);rgba=np.zeros((size*scale,size*scale,4),np.uint8)
            for ci in range(3):rgba[:,:,ci]=np.rint(map_coordinates(arr[:,:,ci]*alpha,[sy,sx],order=1,mode='constant',cval=0)/np.maximum(aa,.00001)).clip(0,255).astype(np.uint8)
            rgba[:,:,3]=np.rint(aa*255).astype(np.uint8);native=register(Image.fromarray(rgba),(size,size),palette,'area_vote');auth=np.zeros_like(target);auth[120:200,120:200]=native
            target[175:]=auth[175:];need(np.array_equal(old[:175],target[:175]),'Upper body changed')
        yy,xx=np.nonzero(target)
        if yy.max()!=q['foot_max_y']+160:
            Image.fromarray(target).save(out/f'diagnostic_invalid_{n:03}.png');a.rgba(target).save(out/f'diagnostic_invalid_{n:03}_rgba.png')
            print(json.dumps({'ref':n,'maxy':int(yy.max()-160),'lastrows':{int(y-160):(np.flatnonzero(target[y])-160).tolist()for y in range(179,int(yy.max()+1))}}),flush=True)
        need(yy.max()==q['foot_max_y']+160,'Whole floor changed');need(label(target>0,np.ones((3,3)))[1]==1,'Disconnected boot')
        Image.fromarray(target).save(out/f'base_{n:03}.png');a.rgba(target).save(out/f'base_{n:03}_rgba.png');record=dict(q);record.update({'indexed_sha256':sha(target.tobytes()),'changed_pixels_vs_v2':int(np.count_nonzero(target!=old)),'above_y15_exact':True});records.append(record)
        rows.append((f'landing {n}',[('대기',a.composite(0)[0]),('기존',a.composite(n)[0]),('새 원화 등록',a.rgba(old)),('새 부츠 국소 정합',a.rgba(target))]))
    helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'source_art_sha256':reg['source_art_sha256'],'source_arc_sha256':sha(a.data),'frames':records,
        'scope':'49/53의 같은 새 원화에서 발목 아래만 접지 정합.45 및 무릎위/상체/머리 불변, 옛 그림 덮기나 단색 채움 없음.','native_packed':False,'runtime_verified':False})
    print(json.dumps({'out':str(out),'changed':{q['ref']:q['changed_pixels_vs_v2']for q in records}}))
if __name__=='__main__':main()
