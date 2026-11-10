"""103 포스 소매 국소 편집용 실제 새 도트와 재질 참조만 구성한다."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
import numpy as np
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write
from prepare_rising_common_layers import polygon
def main():
    out=H/'rising103_sleeve_edit01';need(not out.exists(),'Fresh output required');out.mkdir();a=Archive((H/'rising_base_pack_probe01/PL00_U.ARC').read_bytes())
    need(sha(a.data)=='5e6b8be38f59413938b8515c227b3142a06d4af4c9378645fb696ea145b47a3e','Wrong candidate')
    target=a.composite(103,15)[0];crop=(128,124,192,188);target.crop(crop).resize((1024,1024),Image.Resampling.NEAREST).save(out/'edit_target.png')
    ref=Image.new('RGBA',(1024,1024))
    for col,n in enumerate((0,104)):
        pic=a.composite(n,15)[0].crop(crop).resize((512,512),Image.Resampling.NEAREST);ref.alpha_composite(pic,(col*512,256))
    ref.save(out/'material_reference.png')
    points=[(-18,-13),(-11,-13),(-11,-7),(-8,-2),(-7,3),(-12,3),(-18,0)]
    mask=polygon(points);Image.fromarray(mask.astype(np.uint8)*255).save(out/'sleeve_region.png')
    guide=Image.open(out/'edit_target.png').convert('RGBA');draw=ImageDraw.Draw(guide);draw.line([((x+32)*16,(y+36)*16)for x,y in points+[points[0]]],fill=(40,230,180,255),width=3);guide.save(out/'guide_region.png')
    write(out/'input.json',{'source_candidate_sha256':sha(a.data),'source_ref':103,'source_mask':15,'crop_world':[-32,-36,32,28],'scale':16,'output_size':[1024,1024],'edit_region_world':points,'protected_fist':True,'only_clothing_material_edit':True,'native_pose_all_other_pixels_must_be_preserved':True,'game_changed':False})
if __name__=='__main__':main()
