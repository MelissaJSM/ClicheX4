"""역사 총열의 행별 의미영역을 새 그림 위에 합성하는 미채택 조사판."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
ROWS={
87:{-14:(-15,-10),-13:(-16,-7),-12:(-16,-7),-11:(-15,-7),-10:(-14,-8),-9:(-13,-8),-8:(-11,-9)},
89:{-20:(-15,-12),-19:(-16,-8),-18:(-16,-7),-17:(-16,-7),-16:(-15,-8),-15:(-14,-8),-14:(-13,-8)},
90:{-21:(-20,-19),-20:(-21,-17),-19:(-22,-16),-18:(-22,-15),-17:(-21,-14),-16:(-21,-14),-15:(-20,-14),-14:(-20,-15),-13:(-19,-15),-12:(-18,-16)},
91:{-7:(-24,-20),-6:(-26,-18),-5:(-27,-18),-4:(-27,-18),-3:(-27,-18),-2:(-25,-18),-1:(-24,-18)},
92:{-11:(-13,-12),-10:(-13,-7),-9:(-12,-7),-8:(-12,-7),-7:(-12,-7),-6:(-11,-7),-5:(-11,-5),-4:(-10,-5),-3:(-9,-6),-2:(-9,-7)}}
SOURCES={85:'standing_fire_native02',89:'standing_fire_native02',90:'standing_fire_followthrough_native01',91:'standing_fire_followthrough_native01',86:'standing_fire_recovery_native02',87:'standing_fire_recovery_native02',92:'standing_fire_recovery_native02'}
def main():
    d=H/'standing_fire_modules_probe02';need(not d.exists(),'Fresh module probe');d.mkdir();a=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes());master=np.array(Image.open(H/'base_run_shot_inputs01/barrels/004_indices.png'));mg=np.array(Image.open(H/'base_run_shot_inputs01/barrels/004_mask.png'))>0;rows=[];modules=[]
    for n in(85,86,87,89,90,91,92):
        old=a.layer(n,0)[0];region=np.zeros(old.shape,bool)
        if n in(85,86):
            dx,dy=(8 if n==85 else 9),2;module=np.roll(master,(dy,dx),(0,1));guard=np.roll(mg,(dy,dx),(0,1));region=module>0;need(np.array_equal(old[guard],module[guard]),'Existing gun not canonical')
            policy='현재34 계열 정본60불투명+11투명가드를 평행등록한 값이 현재85/86과exact임을 새로 입증.'
        else:
            for y,(x0,x1)in ROWS[n].items():region[160+y,160+x0:161+x1]=True
            need(np.all(old[region]>0),'Semantic region has blank');module=np.where(region,old,0).astype('uint8');guard=region|(binary_dilation(region)&(old==0));policy='역사 원화/현재 좌표판 육안분리 행별 후보. 독립 정본확정 전 미채택.'
        if n==89:
            for x,y in[(-9,-23),(-10,-22),(-9,-22),(-8,-22),(-10,-21),(-9,-21),(-8,-21)]:need(not guard[160+y,160+x],'Old ear copied')
        Image.fromarray(module).save(d/f'{n:03}_gun_indices.png');Image.fromarray(guard.astype('uint8')*255).save(d/f'{n:03}_gun_guard.png');a.rgba(module).save(d/f'{n:03}_gun.png');modules.append((f'{n} old gun region',a.rgba(module)))
        rr={'ref':n,'policy':policy,'world_rows':{str(y):list(v)for y,v in ROWS.get(n,{}).items()},'module_opaque':int(region.sum()),'transparent_guard':int((guard&~region).sum()),'old_base_fourth_gun_RGBA_exact':bool(np.array_equal(np.array(a.composite(n,0)[0])[region],np.array(a.composite(n,15)[0])[region])),'module_indices_sha256':sha(module.tobytes()),'guard_sha256':sha(guard.tobytes()),'source_dir':SOURCES[n],'forms':[]}
        for form,pal in [('base',0),('fourth',16)]:
            source=np.array(Image.open(H/SOURCES[n]/f'{form}_{n:03}_indices.png'));pix=np.array(a.rgba(source,pal));out=pix.copy();out[guard]=np.array(a.rgba(module))[guard];Image.fromarray(out).save(d/f'{form}_{n:03}.png');need(np.array_equal(out[~guard],pix[~guard]),'Outside gun changed');rr['forms'].append({'form':form,'source_indices_sha256':sha(source.tobytes()),'restored_rgba_changed':int(np.any(out[guard]!=pix[guard],axis=1).sum()),'outside_guard_exact':True,'base_palette_gun_preserved':True})
        rows.append(rr)
    for form,mask in [('base',0),('fourth',15)]:
        for i,refs in enumerate(((85,86,87,89),(90,91,92))):
            pics=[]
            for n in refs:pics.extend([(f'{n} new source',Image.open(H/SOURCES[n]/f'{form}_{n:03}.png')),(f'{n} old gun only',Image.open(d/f'{form}_{n:03}.png'))])
            page(pics,a.composite(0,mask)[0],d/f'{form}_comparison_{i:02}.png',cols=2,scale=5)
    page(modules,a.composite(0,0)[0],d/'gun_regions.png',cols=4,scale=10)
    write(d/'report.json',{'parent_sha256':sha(a.data),'independent_read':{'path':'work/sprite_style_unification_20261107/zero_audit/shibuki_standing_fire_modules01/report.json','sha256':'017553b6a49501dbba1f9821c44542c2e4c46174d275fc1751060e6e09ee6635'},'rows':rows,'old_whole_tile_copied':False,'ear_wholehead_copied':False,'source_native_body_outside_guards_exact':True,'arc_written':False,'canonical_accepted_refs':[85,86],'semantic_masks_require_visual_review':[87,89,90,91,92],'native_projectile_origin_executed_here':False})
    print(json.dumps([{k:r[k]for k in('ref','module_opaque','transparent_guard','old_base_fourth_gun_RGBA_exact')}for r in rows]))
if __name__=='__main__':main()
