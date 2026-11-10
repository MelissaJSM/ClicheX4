"""82 회복 사격의 정확히 접힌 팔/총구 국소 편집 입력. 분석 안내만 추가."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'dash82_arm_retry01';need(not d.exists(),'Fresh output required');d.mkdir();source=H/'dash_shot_inputs02/page04/edit_target.png';im=Image.open(source).convert('RGBA');im.save(d/'edit_target.png');guide=Image.new('RGBA',im.size,(24,30,40,255));guide.alpha_composite(im);q=ImageDraw.Draw(guide)
    for off in (0,512):
        q.rectangle((232,off+208,320,off+272),outline=(255,190,30),width=3)
        q.line([(320,off+264),(344,off+304),(352,off+280)],fill=(80,255,170),width=3)
    guide.convert('RGB').save(d/'anchor_guide.png')
    prompt='''Precise localized edit of Image1, exactly1536x1024 transparent sprite page with2columns by2rows, native96x64 each cell shown8x. This is a recoil/recovery pose, NOT a fully extended attack. Modify ONLY the two LEFT-COLUMN figures (top BASE, bottom FOURTH), original animation82. Keep the RIGHT COLUMN unchanged. The ONLY edit is replacing the lowered foreground/image-left sleeve+hand with a VERY SHORT BENT firing forearm beneath the existing cannon. The cannon in Image1 is CORRECT and unusually close to the face by design. Its muzzle is at native world(-18,-6); source left-column x240,y240(top) ory752(bottom). DO NOT shift it left to make a longer arm. Previous incorrect result shifted it6nativepixels=48sourcepixels left. Keep each existing cannon pixel exactly where it is in Image1, even where its rear overlaps the front cheek in this original game pose. Image2 is an analytical guide: orange box fixes the cannon, green line is compact bent-elbow path below it. Remove guide colors in output.
The short wrist/fist must join the cannon rear at approximatelysourcex312..328,y264..280, with bent elbow atsourcex344,y296 and shoulder atsourcex352,y272, add512to y forbottom. This arm bends DOWN and then BACK toward the shoulder. Do not extend horizontally left. Remove the original dangling foreground hand so exactly2arms remain. Preserve the rear arm/hand exactly. Top sleeve white/lightblue with red cuff, bottom SAME short arm geometry in navy/purple with gold trim. Preserve every existing detailed head/eyes/fox ears/flower/hair/neck/torso/hips/knees/feet pixel and source positions outside this foreground arm region. Keep accepted compact47px proportions. Native game pixel art, fixed8x scale,2~3tone fabric clusters. No entirebody orhead scaling, long strip arm, thirdhand, haze, colored background or glow. Actual transparent background. The short elbow is essential; cannon MUST stay within the orange box instead of moving it left.'''
    (d/'prompt.txt').write_text(prompt,encoding='utf8');write(d/'manifest.json',{'source_sha256':sha(source.read_bytes()),'only_refs':[82],'forms':['base','fourth'],'muzzle_world':[-18,-6],'scale':.125,'rest_original_new_body_preserved':True})
    print(str(d))
if __name__=='__main__':main()
