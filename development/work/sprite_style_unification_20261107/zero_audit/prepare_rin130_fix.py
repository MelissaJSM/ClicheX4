from pathlib import Path
import sys,json,struct,hashlib
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'recovery130_fix01';assert not O.exists();O.mkdir()
arc=(D/'prepared_ground_wall_v1/PL01_U.ARC').read_bytes();p=struct.unpack_from('<16H',entry(arc,9));z=np.array(Image.open(D/'ground_recovery01/native/b0_130_indices.png'));crop=(112,128,208,192)
rgba(z,p).crop(crop).resize((1536,1024),Image.Resampling.NEAREST).save(O/'edit_target.png')
old=Image.open(ROOT/'work/ver_rin_nana/ground_production/v1/frame_130.png').convert('RGBA');canvas=Image.new('RGBA',(384,384));canvas.paste(old,(136,136));canvas.crop(crop).resize((1536,1024),Image.Resampling.NEAREST).save(O/'original_arm_pose.png')
prompt='Use case: precise-object-edit. Edit only image1, our detailed pixel-art Rin maid recovery pose. Image2 is an older authored pose reference ONLY for the arm gesture; do not copy its coarse hair, outfit or rendering. Correct ONLY her upper arms, elbows, white cuffs, and two hands: both forearms angle down and inward so the gloved hands meet in front of the lower apron/lap, matching image2. Her hands should be centered just in front of the bent thighs, near native world x151..159,y163..169; no outstretched left fist and no large isolated glove at the far right hip. Exactly two hands, anatomically connected through bent elbows to the existing shoulders. Keep the blue central apron visibly behind the hands, and keep the same short tool-grip if visible. Preserve image1 exact detailed head/face/cyan eye, hair locks and trailing ribbon, shoulders location, torso/waist, skirt, thighs, calves, boots and all foot positions. No new weapon, no blade, no widening the whole character. Maintain crisp native pixel-art with subtle navy/cool-gray cuff folds matching image1. Native crop96x64 enlarged16x; output1536x1024 with the sprite exactly the same scale and placement. Transparent background. No labels, extra sprites, shadows or environment.'
(O/'prompt.txt').write_text(prompt+'\n','utf8')
(O/'inputs.json').write_text(json.dumps({'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,64],'columns':1,'rows':1,'scale':16,'native_origin':[160,160],'frames':[{'key':'b0_130','bank':0,'ref':130,'cell':[0,0]}],'raw_game_assets_sent':False,'edit_scope':'새 원화의 팔·커프만 보완하며 기존 머리·몸·발을 보호한다.'},ensure_ascii=False,indent=2)+'\n','utf8')
print(O)
