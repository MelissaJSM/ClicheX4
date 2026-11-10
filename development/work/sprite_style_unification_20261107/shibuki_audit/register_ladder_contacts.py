"""신규 손/손목 덩어리의 정수 접점 등록 및 생성된 짧은 부츠 교정.

전신·팔 배율 변경 없이 생성 원화의 작은 덩어리만 이동한다.
기존 신규 머리/몸통/꼬리는 허용 마스크 밖에서 완전 보존한다.
"""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from native_pose_pack import sha,need,write

def boxmask(box):
    x0,y0,x1,y1=box;m=np.zeros((384,384),bool);m[y0+160:y1+160,x0+160:x1+160]=True;return m

def translate(v,new,source_box,delta,clear_box):
    x0,y0,x1,y1=source_box;dx,dy=delta
    m=boxmask(clear_box);v[m]=0
    target=(x0+dx,y0+dy,x1+dx,y1+dy)
    dest=boxmask(target);v[target[1]+160:target[3]+160,target[0]+160:target[2]+160]=new[y0+160:y1+160,x0+160:x1+160]
    return m|dest,{'source_box':source_box,'integer_translation':delta,'clear_box':clear_box,'target_box':target,'no_rescaling':True}

def main():
    out=H/'ladder_contacts_registered01';need(not out.exists(),'Output exists');out.mkdir()
    a=Archive((H/'prepared_wall_front01/PL00_U.ARC').read_bytes());items={0:[],15:[]};rows=[]
    for form,mask,pal in(('base',0,0),('fourth',15,16)):
        for n in(149,151,153):
            old=np.array(Image.open(H/f'ladder_native_page02/{form}_{n:03}_indices.png'));new=np.array(Image.open(H/f'ladder_contact_raw01/{form}_{n:03}_indices.png'));v=old.copy();allowed=np.zeros_like(v,bool);ops=[]
            if n==149:
                m,op=translate(v,new,(-1,-28,6,-22),(-1,-1),(-2,-31,7,-23));allowed|=m;ops.append(op)
            if n==151:
                m,op=translate(v,new,(-10,-28,-4,-22),(0,-1),(-11,-31,-3,-23));allowed|=m;ops.append(op)
                if form=='base':m,op=translate(v,new,(10,-12,15,-6),(0,-1),(10,-14,16,-7))
                else:m,op=translate(v,new,(10,-13,16,-6),(0,0),(10,-14,16,-7))
                allowed|=m;ops.append(op)
            if form=='fourth':
                box={149:(-2,15,6,26),151:(-5,14,4,26),153:(-2,4,6,15)}[n];m=boxmask(box)
                v[m]=new[m];allowed|=m;ops.append({'generated_boot_patch':box,'scale_unchanged':True})
            need(np.array_equal(v[~allowed],old[~allowed]),'Outside contact region changed')
            Image.fromarray(v).save(out/f'{form}_{n:03}_indices.png');pic=a.rgba(v,pal);pic.save(out/f'{form}_{n:03}.png')
            Image.fromarray(allowed.astype(np.uint8)*255).save(out/f'{form}_{n:03}_allowed.png')
            changed=v!=old;Image.fromarray(changed.astype(np.uint8)*255).save(out/f'{form}_{n:03}_changed.png')
            items[mask].extend([(f'{n} previous new art',a.rgba(old,pal)),(f'{n} contact candidate',pic)])
            rows.append({'form':form,'ref':n,'operations':ops,'changed_pixels':int(changed.sum()),'outside_contact_mask_exact':True,'old_new_art_sha256':sha(old.tobytes()),'new_sha256':sha(v.tobytes()),'new_generated_source_sha256':sha(new.tobytes())})
    for mask,form in((0,'base'),(15,'fourth')):page(items[mask],a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=4)
    write(out/'registration.json',{'rows':rows,'source_generated_sha256':'3e00d0adece722beff477871e1bfd7adcc8d6e332c38e3cf4c0760f16038730a','new_body_head_not_overwritten':True,'whole_arm_or_body_scaling':False,'long_sleeve_strip_added':False,'only_new_source_contacts_registered':True,'visual_review_pending':True,'candidate_not_packed':True})
    print([(r['form'],r['ref'],r['changed_pixels'])for r in rows])

if __name__=='__main__':main()
