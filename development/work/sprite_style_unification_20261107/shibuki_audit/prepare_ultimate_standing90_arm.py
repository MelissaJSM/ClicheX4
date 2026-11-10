"""새90 후폼의 총 아래 잘못된 흰 소매만 바꾸는 국소 입력."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
d=H/'ultimate_standing90_arm01';need(not d.exists(),'새 입력 폴더 필요');d.mkdir();crop=(112,112,208,208)
p=H/'ultimate_standing_followthrough_native01/after_090.png';im=Image.open(p).convert('RGBA').crop(crop).resize((768,768),Image.Resampling.NEAREST);im.save(d/'edit_target.png')
box=(-20,-16,-10,-4);guide=im.copy();dr=ImageDraw.Draw(guide);dr.rectangle(tuple((v+48)*8+(-2 if i<2 else 2)for i,v in enumerate(box)),outline=(255,190,0,255),width=3);guide.save(d/'arm_region_guide.png')
a=Archive((H/'prepared_standing_special_ultimate01/PL02_U.ARC').read_bytes());a.composite(0,0)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST).save(d/'skin_reference.png')
prompt='''Use case: precise-object-edit of one existing console pixel sprite.
Image1 is the EDIT TARGET, a768x768 transparent square representing96x96 logical pixels at8x. Return this entire same canvas with the exact sprite position, scale and blank margins. Image2 marks the only edit region in amber; it is a guide and must not be rendered. Image3 is the accepted skin/outfit reference, not a replacement pose.
The character has a short purple buster angled UP-LEFT. Immediately under that purple weapon, left of the face, there is an erroneous WHITE/PALE-BLUE RECTANGULAR SLEEVE with tiny red cloth details. This pale hanging block is clothing on the raised forearm, not a second gun, glove, hair lock or part of the weapon. Replace that sleeve with a naturally shaded bare peach/pink forearm and hand. Keep the wrist at the same high connection under the purple buster and keep the bent elbow at the same low point beside the cheek. Connect the new skin contour to the already bare upper arm below it. Preserve the compact bent-arm skeleton, length and exact shoulder/elbow/wrist coordinates. Do not lower the hand, lengthen the arm or add an extra hand.
Use warm skin highlights and pink skin shadows with a controlled purple outside outline, matching Image3's bare arms. The right-column jacket-off costume has no cuff, sleeve or glove on this arm. Keep the purple buster, its muzzle angle/location and all its outlines unchanged. Preserve every hair lock, braid, fox ears, gold sunglasses, gold eye/face, other arm/hand, lavender sleeveless one-piece outfit, hip/knees/legs, sandals and soles. No other pose, body, garment or material changes.
Crisp logical-pixel clusters and true transparency. No global resize, smooth painterly fill, glow, halo, ground shadow, text, grid or guide rectangle. One full sprite at the same original location.'''
(d/'prompt.txt').write_text(prompt,'utf8');write(d/'input.json',{'ref':90,'form':'after','fixed_source':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())},'world_guide_bbox':list(box),'logical_canvas':[96,96],'native_origin':[48,48],'input_scale':8,'reason':'후폼90 총 아래 흰/하늘 소매 잔재.총열의미범위밖이며 91새맨팔은별도보호.','files':{q.name:sha(q.read_bytes())for q in d.iterdir()if q.is_file()}})
