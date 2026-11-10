"""새로 길이를 그린 실제 소매만 의미 폴리곤으로 분리한다. 목장식은 제외."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register
from prepare_next_guides import body_path
POLYS={
68:[(65,98),(95,99),(135,112),(173,115),(184,110),(200,114),(215,123),(215,151),(65,155)],
70:[(65,105),(100,109),(137,116),(166,109),(178,108),(191,110),(200,116),(200,133),(174,137),(140,151),(65,151)],
72:[(65,82),(106,83),(142,94),(167,98),(184,110),(215,117),(230,121),(230,142),(65,141)],
76:[(65,75),(104,75),(141,88),(170,95),(186,109),(215,114),(229,119),(229,132),(65,135)],
78:[(65,73),(105,79),(137,92),(168,95),(183,101),(205,103),(205,121),(154,129),(65,112)],
80:[(65,73),(104,74),(137,90),(166,93),(183,101),(197,102),(197,121),(152,127),(65,111)],
82:[(65,111),(108,111),(139,117),(173,112),(199,100),(221,103),(221,128),(173,139),(137,155),(65,149)],
84:[(65,115),(106,117),(142,117),(173,109),(199,102),(222,104),(222,130),(175,146),(137,158),(65,153)]}
# Nonfiring gun/hand remnants, identified in the actual body source and the
# indexed coordinate review. Excluding these source pieces is not repainting
# clothes or copying the old game body. Newly authored firing arm stays above.
OLD_HAND_BOXES={70:(-15,5,-9,9),72:(-18,13,-13,16),76:(-17,13,-11,16),78:(-8,1,-1,5),80:(-5,-1,-3,0)}
def source_folder(n):return D/('basic_firing_reach_a2_registered_v1'if n<78 else'basic_firing_reach_b2_registered_v1')
def native(crop,r,pal):
    split=r['split'];w=r['native_width'];upper=register(crop.crop((0,0,crop.width,split)),(w,r['height_above']),pal,'area_vote');lower=register(crop.crop((0,split,crop.width,crop.height)),(w,r['height_below']),pal,'area_vote');data=np.concatenate((upper,lower));out=np.zeros((384,384),np.uint8);ox,oy=r['native_position'];out[160+oy:160+oy+len(data),160+ox:160+ox+w]=data;return out
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(a.data)==plan['parent_arc_sha256'],'Parent');pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],float);out=D/'firing_reach_joint_v3';need(not out.exists(),'Fresh output');out.mkdir();Y,X=np.indices((384,384));x=X-160;y=Y-160;rows=[];proof=[]
    for n,poly in POLYS.items():
        poly=[list(p)for p in poly];poly[0][0]=50;poly[-1][0]=50
        folder=source_folder(n);doc=json.loads((folder/'registration.json').read_text('utf8'));r=next(r for r in doc['frames']if r['ref']==n);crop=Image.open(folder/f'source_{n:03}.png').convert('RGBA');mask=Image.new('L',crop.size);ImageDraw.Draw(mask).polygon(poly,fill=255);rgba=np.array(crop);rgba[np.array(mask)==0,3]=0;Image.fromarray(rgba).save(out/f'source_arm_{n:03}.png');arm=native(Image.fromarray(rgba),r,pal);b=np.array(Image.open(body_path(n-1)));ex,ey=r['target_eye']
        need(not np.any(arm==14),'Green neck ornament must not be copied into arm')
        head=(x>=ex-2)&((y<=ey+2)|((y<=ey+5)&np.isin(b,[5,6,7,8,9,10,11,12,13,14])));arm[head]=0;rest=b.copy();remove=(((x<=ex+2)&(y>=ey+8)&(y<ey+15))|((x<=ex-2)&(y>=ey+3)&(y<ey+8)))&~head;rest[remove]=0;merged=np.where(arm,arm,rest).astype(np.uint8)
        extra=np.zeros_like(b,dtype=bool)
        if n in OLD_HAND_BOXES:
            x0,y0,x1,y1=OLD_HAND_BOXES[n];extra=(x>=x0)&(x<x1)&(y>=y0)&(y<y1)&~head
            rest[extra]=0;merged=np.where(arm,arm,rest).astype(np.uint8)
        gun=np.array(Image.open(D/'fire_constraints'/f'barrel_{n:03}.png'));gy,gx=np.nonzero(gun);window=(X>=gx.min())&(X<=gx.min()+7)&(Y>=gy.min())&(Y<=gy.max());arm[window]=0;merged[window]=gun[window]
        for name,ar in [('new_body',b),('new_sleeve',arm),('rest_body',rest),('merged',merged)]:Image.fromarray(ar).save(out/f'{name}_{n:03}.png');a.rgba(ar).save(out/f'{name}_{n:03}_rgba.png')
        proof.append({'ref':n,'source_rgba_sha256':digest(folder/f'source_{n:03}.png'),'source_art_sha256':doc['source_art_sha256'],'source_arm_polygon':poly,'arm_green_texels':0,'source_arm_scale_inherited':True,'arm_stretch':False,'components_8':int(label(merged>0,np.ones((3,3)))[1]),'arm_body_contact_pixels':int(np.count_nonzero(binary_dilation(arm>0,np.ones((3,3)))&(rest>0))),'gun_window_exact':np.array_equal(merged[window],gun[window]),'base_sha256':sha(b.tobytes()),'merged_sha256':sha(merged.tobytes())})
        proof[-1].update(old_nonfiring_gun_hand_box=OLD_HAND_BOXES.get(n),source_piece_exclusion_only=True)
        rows.append((f'dash shot{n}',[('원래',a.composite(n)[0]),('새 몸체',a.rgba(b)),('새로 그린 실제 소매',a.rgba(arm)),('총구 고정 정합',a.rgba(merged))]))
    for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',7)
    write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':proof,'native_packed':False,'runtime_verified':False,'scope':'새 소매만 분리한 정합 후보. 목 장식은 원래 몸체에서 보존. 미술 검토/부분파츠 전.'});print(json.dumps(proof))
if __name__=='__main__':main()
