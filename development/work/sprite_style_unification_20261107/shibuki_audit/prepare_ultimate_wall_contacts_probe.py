"""새 원화끼리 주먹·손바닥 위치를 공유하는 국소 접점 후보. 아직 패킹하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from scripts.export_x_consistency import Archive,page,metrics
I=H/'ultimate_wall_shared_probe01';N=H/'ultimate_wall_native02';O=H/'ultimate_wall_contacts_probe01';P=H/'prepared_ultimate_lowhp01/PL02_U.ARC'
RECTS={55:[[-14,-8,-7,-3]],57:[[-13,-7,-5,0]],59:[[-16,-10,-9,-4],[12,-25,18,-18]]}
def main():
    need(not O.exists(),'Fresh output required');O.mkdir();a=Archive(P.read_bytes());lut=np.array([0,15,2,3,2,5,6,7,8,9,10,11,12,13,14,15],np.uint8);rows=[];outputs={}
    for n in(55,57,59):
        b=np.array(Image.open(N/'before'/f'{n:03}_indices.png'));q=np.array(Image.open(I/f'{n:03}_indices.png'));initial=q.copy();bm=b.copy();shared=lut[b]
        cm=np.zeros_like(q,bool)
        for x0,y0,x1,y1 in RECTS[n]:cm[y0+160:y1+160,x0+160:x1+160]=True
        q[cm]=shared[cm];fix=[]
        if n==59:
            for x,y in[(9,-5),(10,-5),(10,-4)]:
                need(b[y+160,x+160]==0 and q[y+160,x+160]in(2,14),'Unexpected shoulder overlap material');fix.append({'world':[x,y],'before_index':int(q[y+160,x+160]),'after_index':0,'reason':'이동된 after 머리끝의 잔여 라벤더 외곽. 새 before 공통 머리 마스크로 환원.'});q[y+160,x+160]=0
        if n==57:
            x,y=-9,6;need(b[y+160,x+160]==0 and q[y+160,x+160]==15,'Unexpected garment rim');b[y+160,x+160]=q[y+160,x+160]
            fix.append({'world':[x,y],'before_index':0,'after_index':15,'form':'before','reason':'after 옷단 외곽1px를 재킷 옷단에도 공유. 피부를 잘라내지 않고 두 폼의 실제 새 외곽을 합침.'})
        outside=(q>0)&(b==0);need(not outside.any(),f'Alpha outside remains:{n}')
        for form,v,start in[('before',b,16),('after',q,0)]:
            d=O/form;d.mkdir(exist_ok=True);Image.fromarray(v).save(d/f'{n:03}_indices.png');a.rgba(v,start).save(d/f'{n:03}.png');outputs[form,n]=v
        Image.fromarray(cm.astype(np.uint8)*255).save(O/f'{n:03}_shared_hand_mask.png')
        rows.append({'ref':n,'shared_hand_rectangles_world':RECTS[n],'shared_hand_shape_exact':True,'after_changed_pixels':int(np.count_nonzero(q!=initial)),'before_changed_pixels':int(np.count_nonzero(b!=bm)),'small_registration_corrections':fix,'after_outside_before_pixels':0,'before_metrics':metrics(a.rgba(b,16)),'after_metrics':metrics(a.rgba(q,0)),'new_before_head_legs_preserved':True,'old_body_or_head_copied':False})
    page([(f'{n} jacket',a.rgba(outputs['before',n],16))for n in(55,57,59)]+[(f'{n} after shared hands',a.rgba(outputs['after',n],0))for n in(55,57,59)],a.composite(0,0)[0],O/'comparison.png',cols=3,scale=6)
    write(O/'registration.json',{'source_probe':str((I/'registration.json').relative_to(ROOT)),'rows':rows,'candidate_only':True,'packed':False,'accepted':False,'foot_contact': '새 before와 동일한 발·다리를 그대로 공유. 이전 게임 발바닥 중심에 등록된 위치 유지.','limitations':['손가락과 원 게임 손의 바이트 동일성이 아니라 새 원화 두 폼의 접점 일치다.','59 위팔/손목 접합과57 옷단1px 확장에 대한 실제 확대 열람이 필요하다.']})
    print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
