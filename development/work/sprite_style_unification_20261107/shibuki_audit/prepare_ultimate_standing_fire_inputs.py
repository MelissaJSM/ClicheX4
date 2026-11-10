"""수용 방향의 새85/89 몸체와 실제 Ultimate 대기 의상으로 네셀 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def main():
    d=H/'ultimate_standing_fire_inputs01';need(not d.exists(),'새 입력 폴더 필요');p=H/'prepared_standing_special_ultimate01/PL02_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)=='26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce','부모 변경')
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size);old=Image.new('RGBA',target.size);crop=(112,112,208,208)
    for row,n in enumerate((85,89)):
        im=Image.open(H/f'standing_fire_targets_probe01/base_{n:03}.png').convert('RGBA')
        for col,mask in enumerate((15,0)):
            pos=(col*768,row*768);target.alpha_composite(im.crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            style.alpha_composite(a.composite(0 if row==0 else 97,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            old.alpha_composite(a.composite(n,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'accepted_style.png');old.save(d/'old_pose_context.png')
    prompt='''Use case: identity-preserve console pixel sprite costume edit.
Image1 is the EDIT TARGET. It is a1536x1536 transparent page with exactly2columns and2rows,768x768 cells representing96x96 logical pixels at8x. Keep each sprite at its exact current scale and position in its cell with the large empty margins. Never fill or crop the cell. Same pose repeats left and right.
TOP row85: short buster aimed horizontally LEFT beside the face, front elbow folded downward. BOTTOM row89: short buster angled up-left above the forehead, front elbow folded upward. Keep the exact muzzle/barrel position, barrel direction and size, wrist and elbow joints, lowered other hand, head tilt/gaze, torso angle, knees/ankles and foot sole positions. Exactly two arms and two hands. Preserve the accepted compact proportions: ear-inclusive head about38percent of total height, short softly rounded torso and limbs. Do not make the body taller, thinner, more adult-proportioned or enlarge the head.
Image2 is the authoritative Ultimate outfit and detail reference. Left column wears the pale short jacket, right column has the jacket removed; top row is accepted idle and bottom row is the accepted detailed special pose. Change Image1's red outfit and boots to those exact Ultimate outfits. LEFT: pale lavender-white jacket with readable navy collar/cuff shadows, opening, zipper/fold details and narrow pink center accent over the reference one-piece outfit, bare lower legs and sandals. RIGHT: the reference lavender one-piece outfit with narrow pink center accent, bare shoulders, bare arms, bare legs and sandals. No jacket sleeve or white cuff remains on the right. No skirt, shorts, stocking or boot. Use the actual reference design, no invented clothing.
Replace the red hair ribbon with the accepted small GOLD SUNGLASSES resting on top of the head; angle them correctly in each pose. Keep detailed lavender hair locks and braid, fox-ear planes, small gold eyes, controlled purple outline and2-3tone shading. Preserve the target head tilt and face direction, instead of pasting an idle head. Both costumes must have identical hair/face, body pose and limb/hand/foot coordinates. Garments are the only difference.
Image3 is only the older Ultimate pose context. Do not copy its plain old hair, coarse clothing, white sleeve in the jacket-off form or black leg masses. Preserve the newer target's detailed body and position. The short purple buster is part of the target: do not replace it with a fist, add another weapon, stretch it or move the muzzle.
True transparent background. Clean pixel clusters at the logical pixel scale, no smooth painting, no tiny noisy scribbles, no halo, glow, projectile, ground shadow, grid, text or labels. Keep the exact four-cell layout and positions.'''
    (d/'prompt.txt').write_text(prompt,'utf8');write(d/'input.json',{'refs':[85,89],'forms_by_column':['before','after'],'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(a.data)},'source_targets':{'path':'standing_fire_targets_probe01/manifest.json','sha256':sha((H/'standing_fire_targets_probe01/manifest.json').read_bytes())},'layout':{'canvas':[1536,1536],'grid':[2,2],'logical_canvas':[192,192],'cell':[96,96],'origin':[48,48],'crop':list(crop)},'policy':'새 기본85/89의 수용 방향 포즈에 Ultimate 의상만 적용. 원US 전체복원 또는 다른85..92 별칭 주장 아님.135 거부 편집과 다른 별개 동작.','files':{q.name:sha(q.read_bytes())for q in d.iterdir()if q.is_file()}});print(d)
if __name__=='__main__':main()
