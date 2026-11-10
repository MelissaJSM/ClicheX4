"""새 발사팔 등록 뒤 남은 굽힌 소매만 같은 새 원화로 정합한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
S=H/'ultimate_wall_shots_native04';O=H/'ultimate_wall_shots_final02'
P=H/'prepared_ultimate_lowhp01/PL02_U.ARC'
def main():
    need(not O.exists(),'Fresh final registration required');O.mkdir();a=Archive(P.read_bytes());targets={};rows=[]
    for form,start,mask in [('before',16,15),('after',0,0)]:
        (O/form).mkdir()
        for n in range(56,67,2):
            ip=S/form/f'{n:03}_indices.png';old=np.array(Image.open(ip));v=old.copy();m=np.zeros(v.shape,bool)
            if form=='before' and n in (56,58,60):
                # The bent sleeve's lower edge is still present below the
                # original elbow mask. Read the vacated cloth region from the
                # SAME new firing drawing, without moving its torso or knee.
                body=np.array(Image.open(H/'ultimate_wall_contacts_probe01'/form/f'{n-1:03}_indices.png'))
                source=np.array(Image.open(S/form/f'{n:03}_unshifted_source.png'))
                m[160:167,144:154]=True
                m&=~np.isin(body,[10,11,12,13]) # Existing lower-limb skin stays exact.
                v[m]=source[m]
                need(np.array_equal(v[167:],old[167:]),'Lower legs moved')
                need(np.array_equal(v[np.isin(body,[10,11,12,13])&(np.indices(v.shape)[0]>=160)],old[np.isin(body,[10,11,12,13])&(np.indices(v.shape)[0]>=160)]),'Lower-limb skin changed')
            targets[form,n]=v
            rows.append({'form':form,'ref':n,'input_sha256':sha(ip.read_bytes()),'source':str(S/form/f'{n:03}_unshifted_source.png'),'vacated_sleeve_pixels_changed':int(np.count_nonzero(v!=old)),'operation':'새 사격 원화의 옷단/투명 영역 등록; 무릎 피부와 하체 원점 보존' if m.any() else '그대로 보존'})
    # The after drawing has one dark arm-outline texel beyond the jacket.
    # Its exact same native colour is shared by both palettes. Extend only
    # that new outline pixel; do not erase the bare-arm silhouette.
    shared=[]
    expected={56:[(-11,5,15),(-10,6,2),(-9,6,14)],58:[(-5,-3,15),(-9,6,15),(-8,6,5)],60:[(-7,1,15),(-10,5,2),(-9,5,8),(-10,6,5),(-9,6,9)]}
    for n in (56,58,60):
        b=targets['before',n];q=targets['after',n]
        ys,xs=np.nonzero((q>0)&(b==0));actual=[(int(x-160),int(y-160),int(q[y,x]))for x,y in zip(xs,ys)]
        need(actual==expected[n],'Unexpected costume-alpha discrepancy')
        # The new uncoated lower hem is common to both costumes. Preserve
        # these few edge texels beneath the jacket, rather than deleting the
        # swim-dress or retaining the obsolete yellow sleeve cuff.
        for x,y,index in actual:
            need(index in (2,5,8,9,14,15),'Unexpected skin material at cloth edge')
            need(np.array_equal(np.array(a.rgba(np.array([[index]],np.uint8),0)),np.array(a.rgba(np.array([[index]],np.uint8),16))),'Common material colour differs')
            b[y+160,x+160]=index;shared.append({'ref':n,'world':[x,y],'index':index})
    report=[]
    for n in range(56,67,2):
        need(not ((targets['after',n]>0)&(targets['before',n]==0)).any(),f'Alpha leak {n}')
        for form,start,mask in [('before',16,15),('after',0,0)]:
            v=targets[form,n];old=np.array(Image.open(S/form/f'{n:03}_indices.png'))
            head=np.array(Image.open(S/form/f'{n:03}_head_guard.png'))>0;br=np.array(Image.open(S/form/f'{n:03}_barrel_mask.png'))>0
            need(np.array_equal(v[head],old[head]),'New head changed')
            need(np.array_equal(np.array(a.rgba(v,start))[br],np.array(a.composite(n,mask)[0])[br]),'Original barrel changed')
            Image.fromarray(v).save(O/form/f'{n:03}_indices.png');a.rgba(v,start).save(O/form/f'{n:03}.png')
            Image.fromarray((v!=old).astype(np.uint8)*255).save(O/form/f'{n:03}_final_delta.png')
            report.append({'form':form,'ref':n,'indexed_sha256':sha((O/form/f'{n:03}_indices.png').read_bytes()),'head_exact':True,'barrel_rgba_exact':True,'delta_from_registration_pixels':int(np.count_nonzero(v!=old))})
    for form,start,mask in [('before',16,15),('after',0,0)]:
        items=[]
        for n in range(55,66,2):
            D=H/('ultimate_wall_contacts_probe01'if n<61 else'ultimate_wall_page02_contacts01')
            items.extend([(f'{n} new body',Image.open(D/form/f'{n:03}.png')),(f'{n+1} new firing',a.rgba(targets[form,n+1],start))])
        page(items,a.composite(0,mask)[0],O/f'{form}_comparison.png',cols=4,scale=5)
    write(O/'registration.json',{'passed':True,'rows':rows,'targets':report,'new_common_hem_and_arm_edge':shared,'after_outside_before':0,'packed':False,'runtime_verified':False,'note':'새 원화의 옷단을 등록한 것으로 옛 몸/머리 복사 및 팔 늘임 없음.'})
    print({'output':str(O),'passed':True,'refs':6,'form_targets':12})
if __name__=='__main__':main()
