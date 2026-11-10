"""새 상세 몸체를 보존하며 138 권총팔 국소 원화만 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
POLY=[(-16,-36),(0,-36),(0,-24),(-5,-24),(-9,-23),(-9,-21),(-10,-20),(-10,-17),(-9,-14),(-6,-11),(-3,-10),(-3,-7),(-5,-4),(-5,0),(-6,2),(-8,5),(-10,8),(-18,8),(-18,-9),(-16,-16)]
def main():
    a=Archive((N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC').read_bytes());out=D/'raised138_local_probe_v1';out.mkdir(exist_ok=False);mim=Image.new('L',(384,384));ImageDraw.Draw(mim).polygon([(x+160,y+160)for x,y in POLY],fill=1);m=np.array(mim)>0;records=[];rows=[]
    for form,pal in(('before',16),('after',0)):
        bp=D/f'settle_registered_v1/{form}_138_indices.png';dp=D/f'raised138_registered_v1/{form}_138_indices.png';base=np.array(Image.open(bp));donor=np.array(Image.open(dp));target=base.copy();target[m]=donor[m];need(np.array_equal(target[~m],base[~m]),'새 얼굴/다리/반대팔 보존')
        Image.fromarray(target).save(out/f'{form}_138_indices.png');Image.fromarray(m.astype(np.uint8)*255).save(out/f'{form}_edit_mask.png');a.rgba(target,pal).save(out/f'{form}_138_rgba.png')
        records.append({'form':form,'ref':138,'base_source':bp.relative_to(ROOT).as_posix(),'base_source_sha256':digest(bp),'donor_source':dp.relative_to(ROOT).as_posix(),'donor_source_sha256':digest(dp),'source_art':(D/'raised138_v1/generated.png').relative_to(ROOT).as_posix(),'source_art_sha256':digest(D/'raised138_v1/generated.png'),'semantic_polygon_world':POLY,'changed_pixels':int((target!=base).sum()),'outside_semantic_edit_pixels':0,'components8':int(label(target>0,np.ones((3,3)))[1]),'target_sha256':sha(target.tobytes()),'old_game_art_pixels_copied':0,'whole_body_scaling':False})
        rows.append((f'{form}138',[('old actual raised pose',a.composite(138,15 if pal else 0)[0]),('rejected lowered gun',a.rgba(base,pal)),('new raised source',a.rgba(donor,pal)),('new local registration',a.rgba(target,pal))]))
    helper.grid(rows,out/'comparison.png',6);write(out/'manifest.json',{'frames':records,'scope':'거부된 낮춘팔 원화의 새 얼굴/머리/다리 상세만 보존하고, 위로 든 권총팔/오해한 긴 귀/기존 아래손 의미영역을 새로운 국소원화로 교체.원손·정본총 정합 및 양폼 공통층은 다음단계.','native_packed':False,'runtime_verified':False});print(json.dumps([{k:q[k]for k in('form','changed_pixels','components8')}for q in records]))
if __name__=='__main__':main()
