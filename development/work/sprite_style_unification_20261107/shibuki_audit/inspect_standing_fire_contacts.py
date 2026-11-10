"""85/89의 원총열 창과 새 원화 총열·손발을 읽기 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
RECT={85:(-21,-11,-11,-5),89:(-17,-24,-7,-14)}
def main():
    d=H/'standing_fire_contacts_probe01';need(not d.exists(),'Fresh contacts');d.mkdir();p=H/'prepared_standing_special_base01/PL00_U.ARC';a=Archive(p.read_bytes());rows=[];parts=[]
    for form,pal,mask in [('base',0,0),('fourth',16,15)]:
        pics=[]
        for n in(85,89):
            idx=np.array(Image.open(H/f'standing_fire_native02/{form}_{n:03}_indices.png'));old=np.array(a.composite(n,mask)[0]);new=np.array(a.rgba(idx,pal));x0,y0,x1,y1=RECT[n];guard=np.zeros(idx.shape,bool);guard[160+y0:160+y1,160+x0:160+x1]=True
            buster=np.zeros_like(old);buster[guard]=old[guard];newbuster=np.zeros_like(new);newbuster[guard]=new[guard]
            Image.fromarray(buster).save(d/f'{form}_{n:03}_old_gun.png');Image.fromarray(guard.astype('uint8')*255).save(d/f'{n:03}_gun_guard.png');parts.extend([(f'{form}{n} old gun',Image.fromarray(buster)),(f'{form}{n} generated gun',Image.fromarray(newbuster))])
            # Probe only: original casing window including transparent edge is restored.
            proposed=new.copy();proposed[guard]=old[guard];Image.fromarray(proposed).save(d/f'{form}_{n:03}_probe.png');pics.extend([(f'{n} new source',Image.fromarray(new)),(f'{n} original casing probe',Image.fromarray(proposed))])
            rows.append({'form':form,'ref':n,'old_guard_world':list(RECT[n]),'guard_cells':int(guard.sum()),'old_gun_pixels':int((buster[:,:,3]>0).sum()),'changed_rgba_inside_guard':int(np.any(old[guard]!=new[guard],axis=1).sum()),'old_gun_rgba_sha256':sha(buster.tobytes()),'new_metrics':metrics(Image.fromarray(new)),'probe_metrics':metrics(Image.fromarray(proposed)),'native_projectile_origin_verified_here':False,'gun_guard_is_visual_module_not_whole_native_part':True})
        page(pics,a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    page(parts,a.composite(0,0)[0],d/'gun_modules.png',cols=4,scale=10)
    write(d/'report.json',{'parent_sha256':sha(p.read_bytes()),'rows':rows,'scope':'현재 수용 총열의 시각적 부위/투명테두리 보존 시험. 최종 채택 아님. 실제 원탄환 발생점·총구와 피부/옷 소유는 후속 확인.','arc_written':False})
    print(json.dumps(rows))
if __name__=='__main__':main()
