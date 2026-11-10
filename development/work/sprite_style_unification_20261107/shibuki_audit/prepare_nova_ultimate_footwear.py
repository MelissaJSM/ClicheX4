"""새 Ultimate 준비 자세의 잘못된 긴 신발만 국소 교정할 입력을 만든다."""
from pathlib import Path
import sys
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive

def main():
    d=H/'nova_ultimate_footwear_inputs01';need(not d.exists(),'새 입력만')
    a=Archive((H/'prepared_chaser_ultimate01/PL02_U.ARC').read_bytes())
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size)
    for row,n in enumerate((213,215)):
        for col,(form,mask)in enumerate((('before',15),('after',0))):
            pos=(col*768,row*768);im=Image.open(H/f'nova_ultimate_native01/{form}_{n:03}.png').convert('RGBA')
            target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),pos)
            style.alpha_composite(a.composite(0 if row==0 else 205,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),pos)
    prompt='''Precise local correction of four game pixel-art sprites. Image1 is the EDIT TARGET, a1536x1536 transparent sheet with2columns and2rows. Each768x768 cell is a96x96 logical pixel canvas enlarged8x, origin(48,48). Preserve every figure's position and scale. Image2 is the accepted costume reference in the same column order: jacket on the LEFT, sleeveless version on the RIGHT.
Edit ONLY the lower legs and footwear on Image1. The newly generated tall white/lavender boots or stockings are erroneous. Match Image2's exposed skin calves and ankles with compact white-and-pink open sandals: skin continues from each bent knee down the shin to the narrow sandal straps at the FOOT, with small pale soles and restrained purple outline. No boots, stockings, socks or shin armor. Retain the exact current knee, ankle and sole coordinates, foot direction, bent leg proportions, and total pose height. Do not elongate, straighten, reposition, resize or reconstruct the legs. The top row is compactly crouched with folded feet; the bottom row has two distinct bent legs. Use the same pose-specific silhouette and sandal design in both columns.
All other existing artwork is protected: detailed ears, layered hair and braid, gold glasses and eyes, face, jacket or sleeveless upper costume, torso, hips, thighs, both arms and fists. The bottom row fist stays above the head on viewer-left. Exactly two arms and two legs. Keep the same garment coverage as the supplied reference. Do not change any upper costume or create shorts/skirt.
Preserve sharp native pixel clusters, subtle skin shading and tiny sandal strap details. The result must keep all four complete characters in their original cells, on actual transparent background, with no glow, shadow, labels, guides or grid. No crop or recentering. This is a lower-leg footwear correction only.'''
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'accepted_style.png');(d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'refs':[213,215],'forms_by_column':['before','after'],'parent':{'path':(H/'prepared_chaser_ultimate01/PL02_U.ARC').relative_to(ROOT).as_posix(),'sha256':sha(a.data)},'source_native':{'path':(H/'nova_ultimate_native01/report.json').relative_to(ROOT).as_posix(),'sha256':sha((H/'nova_ultimate_native01/report.json').read_bytes())},'layout':{'canvas':[1536,1536],'logical_canvas':[192,192],'cell':[96,96],'origin':[48,48],'crop':[112,112,208,208]},'policy':'새 머리·상체·팔·무릎/발바닥 좌표를 보존하며 종아리/신발 재질만 국소 donor로 검토. 전체 원화 교체 아님.','files':{p.name:sha(p.read_bytes())for p in d.iterdir()if p.is_file()}})
    print(d)
if __name__=='__main__':main()
