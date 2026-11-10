"""현재 얼티밋34 정본총열과 원대시8총구를 별도 추출한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_ultimate_air_shot_inputs import exact_masked,shift
def main():
    o=H/'ultimate_dash_barrel_guard01';need(not o.exists(),'Fresh audit');o.mkdir();p=H/'prepared_ultimate_air01/PL02_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)=='3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7','Wrong parent');mp=H/'air_barrel_guard02/master_034_mask.png';mask=np.array(Image.open(mp))>0;master=exact_masked(a,a.composite(34,0)[0],0,mask);need(int((master>0).sum())==60 and int(mask.sum())==71,'Wrong canonical module');need(set(np.unique(master))=={0,2,5,8,14,15},'Includes skin or sleeve');need(a.rgba(master,0).tobytes()==a.rgba(master,16).tobytes(),'Palette changes module');Image.fromarray(master).save(o/'master_indices.png');Image.fromarray(mask.astype(np.uint8)*255).save(o/'master_mask.png');src=ROOT/'work/ver_buki_riko/shibuki_art/dash_v1/production08/pairs.json';pairs=json.loads(src.read_text('utf8'))['frames'];rows=[];pics=[]
    for r in pairs:
        n=r['run'];mx,my=map(int,r['original_muzzle_world']);gun=shift(master,mx+24,my+10);guard=shift(mask.astype(np.uint8),mx+24,my+10)>0;Image.fromarray(gun).save(o/f'{n+1:03}_indices.png');Image.fromarray(guard.astype(np.uint8)*255).save(o/f'{n+1:03}_mask.png')
        for form,equip,pal in(('before',15,16),('after',0,0)):
            actual=np.array(a.composite(n+1,equip)[0]);expected=np.array(a.rgba(gun,pal));old=np.zeros_like(actual);old[guard]=actual[guard];diff=guard&np.any(actual!=expected,axis=2);pics.extend([(f'{form} {n+1} current gun',Image.fromarray(old)),(f'{form} {n+1} canonical34',a.rgba(gun,pal))]);rows.append({'form':form,'body_ref':n,'shot_ref':n+1,'muzzle_world':[mx,my],'translation':[mx+24,my+10],'opaque_pixels':60,'transparent_guard':11,'old_casing_rgba_diff_pixels':int(diff.sum()),'module_raw_sha256':sha(gun.tobytes()),'mask_raw_sha256':sha(guard.tobytes())})
    for i in range(0,len(pics),8):page(pics[i:i+8],a.composite(0,0)[0],o/f'comparison_{i//8:02}.png',cols=2,scale=5)
    write(o/'report.json',{'parent':p.relative_to(ROOT).as_posix(),'parent_sha256':sha(a.data),'anchor_source':src.relative_to(ROOT).as_posix(),'anchor_source_sha256':sha(src.read_bytes()),'master_mask_source':mp.relative_to(ROOT).as_posix(),'master_mask_sha256':sha(mp.read_bytes()),'master_ref':34,'master_form':'after','master_rgba_same_in_both_forms':True,'rows':rows,'preservation_policy':'원34 수용 총열60+투명11을 각원총구로 평행등록. 옛 각프레임의 왜곡/색차이까지 유지한다는 뜻은 아님.','generated_arms_ready':False,'game_modified':False});print(json.dumps({'conditions':len(rows),'old_diff':[r['old_casing_rgba_diff_pixels']for r in rows]}))
if __name__=='__main__':main()
