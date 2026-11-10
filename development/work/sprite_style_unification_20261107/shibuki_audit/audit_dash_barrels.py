"""대시 실제 총구와 수용34 총열 모듈 비교. 신규 아트 아닌 입력/보호자료 추출."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_ultimate_air_shot_inputs import exact_masked,shift
P=H/'prepared_rising_right_base01/PL00_U.ARC'
def main():
    o=H/'dash_barrel_guard02';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive(P.read_bytes())
    source=ROOT/'work/ver_buki_riko/shibuki_art/dash_v1/production08/pairs.json';pairs=json.loads(source.read_text('utf8'))['frames']
    mp=H/'air_barrel_guard02/master_034_mask.png';mask=np.array(Image.open(mp))>0;master=exact_masked(a,a.composite(34,0)[0],0,mask)
    need(int((master>0).sum())==60,'Canonical34 opaque count changed');need(set(np.unique(master))=={0,2,4,5,8,14,15},'Gun module includes unexpected material')
    need(np.array_equal(master,np.array(Image.open(H/'air_barrel_guard02/master_034_indices.png'))),'Accepted basic34 master changed')
    Image.fromarray(master).save(o/'master_034_indices.png');Image.fromarray(mask.astype(np.uint8)*255).save(o/'master_034_mask.png');rows=[];pics=[]
    for r in pairs:
        n=r['run'];mx,my=map(int,r['original_muzzle_world']);dx,dy=mx+24,my+10;gun=shift(master,dx,dy);guard=shift(mask.astype(np.uint8),dx,dy)>0
        Image.fromarray(gun).save(o/f'{n+1:03}_indices.png');Image.fromarray(guard.astype(np.uint8)*255).save(o/f'{n+1:03}_mask.png')
        for form,equipment in(('base',0),('fourth',15)):
            current=np.array(a.composite(n+1,equipment)[0]);expected=np.array(a.rgba(gun));old=np.zeros_like(current);old[guard]=current[guard];diff=guard&np.any(current!=expected,axis=2)
            rows.append({'form':form,'body_ref':n,'shot_ref':n+1,'muzzle_world':[mx,my],'translation':[dx,dy],'opaque':int((gun>0).sum()),'guard_pixels':int(guard.sum()),'changed_rgba_from_old':int(diff.sum()),'different_world':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero(diff))],'module_index_sha256':sha(gun.tobytes()),'guard_sha256':sha(guard.tobytes())})
            pics.extend([(f'{form} {n+1} old casing',Image.fromarray(old)),(f'{form} {n+1} accepted34 at same muzzle',a.rgba(gun))])
    for i in range(0,len(pics),8):page(pics[i:i+8],a.composite(0,0)[0],o/f'comparison_{i//8:02}.png',cols=2,scale=5)
    write(o/'report.json',{'source_parent_sha256':sha(P.read_bytes()),'source_anchor_file':source.relative_to(ROOT).as_posix(),'source_anchor_sha256':sha(source.read_bytes()),'master_ref':34,'master_mask_sha256':sha(mp.read_bytes()),'master_indices_sha256':sha(master.tobytes()),'rows':rows,'scope':'원총구 고정. 수용된34의 총열60픽셀+11투명칸 모듈 평행등록. 옛 소매·총열 혼입까지 보존한다는 뜻은 아님.','game_modified':False})
    print(json.dumps([{'form':r['form'],'shot':r['shot_ref'],'muzzle':r['muzzle_world'],'diff':r['changed_rgba_from_old']}for r in rows]))
if __name__=='__main__':main()
