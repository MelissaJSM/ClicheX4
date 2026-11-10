"""89 실제 기존 세로 팔 영역을 표시한 별개 국소 교정 입력."""
from pathlib import Path
import sys,json
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
d=H/'ultimate_standing89_arm02';need(not d.exists(),'새 입력 폴더 필요');d.mkdir();crop=(112,112,208,208)
p=H/'ultimate_standing_fire_native01/after_089.png';im=Image.open(p).convert('RGBA').crop(crop).resize((768,768),Image.Resampling.NEAREST);im.save(d/'edit_target.png')
guide=im.copy();dr=ImageDraw.Draw(guide);dr.rectangle(((48-14)*8-2,(48-14)*8-2,(48-7)*8+2,(48-2)*8+2),outline=(255,190,0,255),width=3);guide.save(d/'arm_region_guide.png')
a=Archive((H/'prepared_standing_special_ultimate01/PL02_U.ARC').read_bytes());a.composite(0,0)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST).save(d/'skin_reference.png')
prompt='''Use case: precise-object-edit of ONE console pixel sprite.
Image1 is the full edit target. Keep its transparent square canvas, exact sprite position and pixel size. It shows a compact fox-eared character holding a short buster UP-LEFT above the forehead. Image2 is the same sprite with an amber rectangle marking the ONLY edit region; the rectangle is a guide and must not appear in the output. Image3 is only the accepted bare-arm skin material reference.
Inside the amber guide is a WHITE VERTICAL FOREARM, immediately under the raised purple buster and to the LEFT of the face. This white strip is a mistaken cloth sleeve, not a strand of hair and not part of the buster. Change that vertical strip into a bare peach/pink skin forearm with a purple shadow edge. Keep the UPPER wrist directly touching the buster at its existing high position above eye level. Keep the elbow at the existing LOWER end of that same vertical strip beside the lower cheek. Preserve the exact bent arm skeleton and short forearm length. Do not lower the hand to the chin or chest, do not add a fist beside the mouth, and do not create an additional arm under this one.
Only replace the white/blue cloth material inside the indicated arm shape with detailed skin shading and natural wrist/elbow contours. Preserve the buster and its dark outline, muzzle position and angle, every hair lock and braid, golden sunglasses, face, ears, other lowered arm and hand, sleeveless one-piece outfit, hips, legs, sandals and soles. Exactly two arms, one raised weapon arm and one lowered arm. Keep all other pixels as unchanged as possible. No new garment, cuff, glove, expanded body, global resize, glow, shadow, labels or grid. True transparent background and crisp native pixel clusters. Return one full sprite on the same square canvas, not a crop.'''
(d/'prompt.txt').write_text(prompt,'utf8');write(d/'input.json',{'ref':89,'form':'after','fixed_source':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())},'world_guide_bbox':[-14,-14,-7,-2],'logical_canvas':[96,96],'native_origin':[48,48],'input_scale':8,'prior_edit_not_adopted':'sleeves01의89는윗소매잔존/팔하강으로반려.85는접점후속검토중.','files':{p.name:sha(p.read_bytes())for p in d.iterdir()if p.is_file()}})
