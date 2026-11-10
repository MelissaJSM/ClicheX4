"""136의 새 발 모듈만 y+1 강체 등록.원화삭감/전신리사이즈/새도트 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from inspect_ultimate_hurt_common import shift

def main():
    d=H/'ultimate_arrival136_foot_contacts01';need(not d.exists(),'Fresh feet registration');d.mkdir();s=H/'ultimate_arrival_separate_native01';a=Archive((H/'prepared_ultimate_hurt02/PL02_U.ARC').read_bytes());rows=[];pics=[]
    yy,xx=np.indices((384,384));xx-=160;yy-=160
    parts=[(xx>=-18)&(xx<=-7)&(yy>=15)&(yy<=24),(xx>=0)&(xx<=12)&(yy>=15)&(yy<=24)]
    for form,pal,mask in(('before',16,15),('after',0,0)):
        old=np.array(Image.open(s/f'{form}_136_indices.png'));new=old.copy();pr=[]
        for part in parts:
            module=np.where(part,old,0).astype(np.uint8);new[part&(yy>15)]=0;registered=shift(module,0,1);new[registered>0]=registered[registered>0]
            need(np.array_equal(registered,shift(module,0,1)),'Module changed')
            # Upper edge retains the existing calf pixel row; translated foot
            # starts one row lower. Nothing is interpolated or filled.
            pr.append({'source_opaque':int(np.count_nonzero(module)),'source_array_sha256':sha(module.tobytes()),'registered_array_sha256':sha(registered.tobytes()),'translation':[0,1],'source_top_world_y':15,'unchanged_upper_overlap_world_y':15})
        need(np.array_equal(new[yy<=15],old[yy<=15]),'Eye/knee/upper calf changed')
        Image.fromarray(new).save(d/f'{form}_136_indices.png');a.rgba(new,pal).save(d/f'{form}_136.png');Image.fromarray(((new!=old)*255).astype(np.uint8)).save(d/f'{form}_changed_mask.png')
        parent=a.composite(136,mask)[0];pics.extend([(f'136 parent {form}',parent),(f'136 new prior {form}',a.rgba(old,pal)),(f'136 feet+1 {form}',a.rgba(new,pal))])
        legs=[]
        for half in(xx<0,xx>=0):
            cur=(new>0)&half;src=(old>0)&half;par=(np.array(parent)[:,:,3]>0)&half
            legs.append({'parent_bottom_inclusive':int(yy[par].max()),'prior_bottom_inclusive':int(yy[src].max()),'registered_bottom_inclusive':int(yy[cur].max())})
        rows.append({'form':form,'ref':136,'source_sha256':sha((s/f'{form}_136_indices.png').read_bytes()),'modules':pr,'eye_knee_upper_calf_exact':True,'changed_pixels':int((new!=old).sum()),'left_right_bottoms':legs,'metrics':metrics(a.rgba(new,pal))})
    page(pics,a.composite(0,15)[0],d/'comparison.png',cols=3,scale=5)
    write(d/'report.json',{'rows':rows,'wholebody_rescale':False,'new_art_created':False,'interpolated_pixels':0,'source_pixels_only':True,'arc_written':False,'contact_registration':'새발 두 모듈의 y+1 강체 배치. y15 위 종아리/무릎/눈은 exact. 접속행은 기존 원화와 새 모듈의 겹침으로만 구성.'});print(json.dumps(rows))
if __name__=='__main__':main()
