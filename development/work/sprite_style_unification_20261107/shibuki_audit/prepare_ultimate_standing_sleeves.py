"""새85/89 후폼의 잘못 남은 소매 두 부위만 별도 원화 교정 입력."""
from pathlib import Path
import sys,shutil,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
d=H/'ultimate_standing_fire_sleeves01';need(not d.exists(),'새 출력 폴더 필요');d.mkdir()
for old,new in [('generated.png','edit_target.png'),('accepted_style.png','accepted_style.png')]:
    shutil.copyfile(H/'ultimate_standing_fire_inputs01'/old,d/new)
prompt='''Use case: precise-object-edit. Correct TWO small arm-material mistakes in this console pixel sprite sheet.
Image1 is the edit target: a square transparent 2-column by 2-row page. Keep the whole canvas, four sprites and their exact current cell positions and scale. The left column is the jacket costume and must remain unchanged. The right column is the sleeveless costume.
Only edit the FRONT WEAPON ARM on the two RIGHT-column sprites. In the upper-right sprite, the short bent forearm directly below the horizontal purple buster is mistakenly a white/lavender pleated jacket cuff. In the lower-right sprite, the raised forearm directly between the up-left buster and the face has a long white/pale blue jacket sleeve. Replace these two cloth sleeves with correctly articulated bare skin arms matching the right-column lowered bare arm and the accepted reference. Draw a natural narrow wrist, bent elbow and peach/pink skin shading with a controlled dark purple underside outline. There must be no white cuff, cloth folds, long glove or detached arm piece on either right front arm.
Image2 is only the accepted costume/material reference; its right column confirms the sleeveless one-piece outfit and bare arms. Preserve Image1's newer detailed lavender hair, fox ears, small gold sunglasses, face and gaze, torso and existing outfit, lowered other arm/hand, knees, legs, sandals, foot soles and all joint positions. Do not move, resize, rotate or redraw the buster or its muzzle. Keep the current hand at the exact weapon grip and the elbow at its current place; this is an arm material correction, not a new pose. Exactly two arms per sprite. Do not copy the older reference head or body.
Preserve the crisp pixel-cluster style and compact body proportions. No global scaling, changed height, new garment, new accessories, projectile, glow, background, shadow, text or grid. Keep true transparent alpha. Leave both left-column sprites and everything outside the two right front arms as unchanged as possible.'''
(d/'prompt.txt').write_text(prompt,'utf8')
write(d/'input.json',{'target_refs':[85,89],'form':'after','scope':'두 새 후폼 발사팔의 흰소매 재질만 국소 수정. 앞선135 거부 편집과 다른 자세.','source_files':{p.name:sha(p.read_bytes())for p in d.iterdir()if p.is_file()},'before_body_and_all_other_regions_protected':True})
print(json.dumps({'input':str(d),'target_sha256':sha((d/'edit_target.png').read_bytes())}))
