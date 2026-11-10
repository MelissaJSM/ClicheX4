"""151 손잡이 접점의 남은 2px 오차를 새 원화에 국소 교정할 입력."""
from pathlib import Path
import sys,shutil
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'ultimate_ladder151_arm_edit02';need(not d.exists(),'Fresh edit');d.mkdir()
    src=H/'ultimate_ladder151_arm_edit01/generated.png';need(sha(src.read_bytes())=='5e1a7c24822fb989cd4ceb2ce929729ab0caad6db7ddeca8a20076ed3ec7d47b','Wrong source')
    shutil.copyfile(src,d/'edit_target.png');shutil.copyfile(H/'ultimate_ladder151_arm_edit01/joint_reference.png',d/'joint_reference.png')
    guide=Image.open(src).convert('RGBA');dr=ImageDraw.Draw(guide)
    for row in range(2):
        x=512+(32+12)*8;y=row*512+(32-10)*8
        dr.rectangle((x-8,y-8,x+8,y+8),outline=(0,255,100,255),width=3)
        dr.line((x-24,y,x+24,y),fill=(0,255,100,255),width=2);dr.line((x,y-24,x,y+24),fill=(0,255,100,255),width=2)
    guide.save(d/'palm_target_guide.png')
    p='''Use case: precise-object-edit. Edit image1 only. Image2 is joint-contact reference. Image3 contains green guide crosses that must NEVER appear in output.
Keep exactly1536x1024, six original figures in3 columns and2 rows, same8x pixel scale, fully transparent background. Only the middle column's SCREEN-RIGHT LOWER ARM in BOTH rows changes. The new hand has improved but its flesh still starts2 native pixels too low and2 pixels too far left. Raise that fist16 screen pixels and move it16 screen pixels right. The green square in image3 marks the TARGET PALM: center at absolute(864,176) top row and(864,688) bottom row. Flesh should occupy native worldx11..13,y-11..-9. This lower fist must sit at the height and horizontal position shown in image2. Bend the short forearm upward to connect the fist at that exact point; keep its shoulder anchored behind the same hair. The sleeve elbow should be bent, not a stretched straight strip. Keep the upper raised arm unchanged. Only2 arms per figure.
The top middle figure retains the detailed white/navy jacket sleeve and dark cuff. The bottom middle has a bare flesh arm in exactly the same position, no sleeve. Preserve all other new hair strands, ears, navy side ornament, head position, torso, collar, thighs, knees and sandals. Keep first/third columns completely unchanged. Do not move or scale any complete figure. No new accessories, no front glasses on back hair. No guide marks, cross, text, ladder, halo or opaque background.'''
    (d/'prompt.txt').write_text(p+'\n',encoding='utf8');write(d/'input.json',{'input_sha256':sha(src.read_bytes()),'source_native_hand_top':-9,'target_native_hand_top':-11,'source_native_hand_left':9,'target_native_hand_left':11,'edit_only':'151 양폼 화면오른쪽 낮은 팔','generated':False})
if __name__=='__main__':main()
