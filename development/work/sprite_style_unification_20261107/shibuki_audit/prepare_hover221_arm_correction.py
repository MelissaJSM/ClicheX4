"""새221의 내려간 반대팔만 원래 머리 위 손 위치로 교정할 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from prepare_hover_ultimate_inputs import P,PARENT
def main():
    d=H/'hover221_arm_inputs01';need(not d.exists(),'기존입력보호');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모변경');src=H/'hover_ultimate_native01/221_indices.png';z=np.array(Image.open(src));new=a.rgba(z);old=a.composite(221,15)[0];crop=(96,96,224,224);d.mkdir()
    new.crop(crop).resize((1024,1024),Image.Resampling.NEAREST).save(d/'edit_target.png');old.crop(crop).resize((1024,1024),Image.Resampling.NEAREST).save(d/'original_pose_guide.png');a.composite(39,0)[0].crop(crop).resize((1024,1024),Image.Resampling.NEAREST).save(d/'raised_arm_style.png')
    prompt='''Use case: precise local pixel-art limb correction.
Image1 is the ONLY edit target: one transparent1024x1024 full-body sprite on a fixed128x128 native grid enlarged8x, character origin(64,64). Keep the entire canvas, margins, current scale and placement. Image2 is the original POSE/JOINT POSITION guide. Image3 supplies accepted bare-arm pixel shading only, not a pose to copy.
Correct one clear pose error in Image1. The character's viewer-RIGHT arm is currently bent down with its hand at the waist. In the intended hovering pose BOTH hands are above the head. Keep the viewer-LEFT raised arm and hand exactly where they are. Move only the viewer-RIGHT arm from the waist into the raised position shown by Image2: the fist is just above the viewer-right fox ear at approximately native world(+4,-27), meaning canvas native(68,37), and its raised forearm runs along the right side of the head toward the shoulder. Follow the original shoulder-to-elbow-to-wrist-to-fist route in Image2. The new hand must be the same small size as the other hand. Remove the erroneous waist hand and its bent forearm while reconstructing only the tiny local garment area they had covered. Exactly TWO arms and TWO hands, both raised; no third hand, no leftover waist fist and no detached skin fragments.
Preserve ALL other new Image1 pixels and design: detailed lavender hair locks and braid, gold sunglasses resting on the forehead, both fox ears, face/eye, torso height, lavender garment and pink center, legs, knees, dark lavender footwear, heel/toe coordinates and overall silhouette. Do not copy Image2's older flat hair, pale sleeves, simplified clothing or old body. Do not change the costume or add a jacket, gloves, gun, effects or props. The corrected arm is bare skin with the same restrained warm skin highlights, pink midtones and purple shadow contour as the accepted arm style. The hand is ABOVE the head, not across the face or glasses.
This is a local pose correction of a neutral full-body console gameplay sprite. Keep sharp square pixel clusters, actual transparency, no anti-aliased halo, blur, glow, background, shadows, labels or grid. Return one corrected sprite in the same exact1024x1024 placement.'''
    (d/'prompt.txt').write_text(prompt,'utf8');write(d/'input.json',{'parent_sha256':PARENT,'ref':221,'source_new_body':{'path':src.relative_to(ROOT).as_posix(),'sha256':sha(src.read_bytes())},'source_native_registration_sha256':sha((H/'hover_ultimate_native01/registration.json').read_bytes()),'original_hand_coordinate_guide':[4,-27],'coordinate_kind':'원그림의 피부손 중심 부근 시각 가이드이며 외곽 모든 픽셀 exact 의미가 아님','layout':{'logical_canvas':[128,128],'origin':[64,64],'crop':list(crop),'canvas':[1024,1024]},'reason':'첫 새원화에서 오른쪽 높은 팔이 허리로 내려갔다.첫prompt가 정확한 두손높이를 충분히 명시하지 못했으므로 새팔 국소 원화로 바로잡는다.','old_first_candidate_221_accepted':False,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()}})
    print(d)
if __name__=='__main__':main()
