"""같은 자세 국소 재작화에서 피부 경계 texel만 등록. 색 생성 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import register
SRC=D/'skin_edge_first_v1/generated.png';EXPECTED='0dedbd9ce6b3cd447d0f0f4bec84fc7e033ea161701d5307cfd540b9d4e4e9bf'

def main():
    need(digest(SRC)==EXPECTED,'Art SHA');a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32)
    art=Image.open(SRC).convert('RGBA');meta=json.loads((D/'before_first_registered_v2/registration.json').read_text('utf8'));out=D/'skin_edge_registered_v3';out.mkdir(exist_ok=False);rows=[];records=[]
    for rec in meta['frames']:
        n=rec['ref'];old=np.array(Image.open(D/f'before_first_registered_v2/before_{n:03}.png'));new=old.copy();source=np.zeros_like(old);positions=[]
        if n!=51:
            crop=art.crop(rec['source_crop']);w=rec['native_width'];split=rec['split'];hu=rec['upper_height'];hl=rec['lower_height'];ox,oy=rec['native_position']
            value=np.concatenate((register(crop.crop((0,0,crop.width,split)),(w,hu),pal,'area_vote'),register(crop.crop((0,split,crop.width,crop.height)),(w,hl),pal,'area_vote')))
            source[oy+160:oy+160+len(value),ox+160:ox+160+w]=value
            # 33 y>=15 is the original newly-authored ankle/shoe module.
            # It is protected even where its black edge touches skin.
            Y,X=np.indices(old.shape);low,high={33:(0,15),39:(0,9),47:(2,14)}[n]
            skin=np.isin(old,(10,11,12));near=binary_dilation(skin,np.ones((3,3)))
            allowed=near&(old==1)&np.isin(source,(2,3,4,10,11,12))&(Y>=160+low)&(Y<160+high)
            new[allowed]=source[allowed]
            for y,x in np.argwhere(new!=old):positions.append({'world':[int(x-160),int(y-160)],'before':int(old[y,x]),'after':int(new[y,x]),'same_pose_source_registered_index':int(source[y,x])})
        need(np.array_equal(old>0,new>0),'Alpha changed');need(np.array_equal(new[old!=1],old[old!=1]),'Nonoutline changed')
        Image.fromarray(new).save(out/f'before_{n:03}.png');Image.fromarray(source).save(out/f'new_source_registered_{n:03}.png')
        rows.append((f'Ultimate {n}',[('accepted idle',a.composite(0,15)[0]),('new art previous',a.rgba(old,16)),('local skin edge revision',a.rgba(new,16))]))
        shoe_y={33:15,39:9,47:14,51:15}[n]
        need(np.array_equal(old[160+shoe_y:],new[160+shoe_y:]),'Shoe protection')
        records.append({'ref':n,'changes':positions,'changed_pixels':len(positions),'alpha_exact':True,'shoe_region_world_y_at_least':shoe_y,'shoe_region_exact':True,'upper_region_world_y_below_zero_exact':bool(np.array_equal(old[:160],new[:160])),'source_sha256':EXPECTED,'indexed_sha256':sha(new.tobytes())})
    helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'frames':records,'method':'Same full-page crop and exact registration mapping. Only native dark boundary adjacent to original skin can receive authored edited source2/3/4/10/11/12. No invented pixel values or global recolor.51 unchanged.','native_packed':False,'runtime_verified':False})
    print(json.dumps({'out':str(out),'counts':{r['ref']:r['changed_pixels']for r in records}}))
if __name__=='__main__':main()
