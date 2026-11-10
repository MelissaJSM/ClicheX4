"""새 린 네 자세의 손/머리를 고정하고 하체 접점만 다시 그릴 입력."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import rgba
D=Path(__file__).parent/'rin_extension';P=D/'followthrough01';O=D/'followthrough_contacts_fix01'
assert not O.exists();O.mkdir()
info=json.loads((P/'inputs.json').read_text('utf8'));pal=info['palette_words'];crop=tuple(info['crop'])
native=Image.new('RGBA',(192,192));original=Image.new('RGBA',(192,192));rows=[]
spec={
 'b1_146':{'edit':'Compress the crouched waist/skirt and bent legs by rearticulating them, without shrinking the head or torso. Front foot toward x+2,y-4; rear foot x-2,y-3. Keep the two boots distinct.', 'original_contact':{'front_floor_y':183,'front_floor_x':[163,168],'rear_floor_y':183,'rear_floor_x':[185,190]},'lower_region_min_y':168},
 'b1_156':{'edit':'Bend/shorten only the long descending shin and boot naturally so the lowest toe returns x-2,y-5. Keep its thigh root and the lifted other knee and boot.', 'original_contact':{'descending_floor_y':183,'descending_floor_x':[161,164]},'lower_region_min_y':169},
 'b1_158':{'edit':'Rearticulate the two lower legs and boots so the front toe returns x+2,y-4 and rear toe x-2,y-3. Keep the knee bend and separated feet; do not narrow the thighs.', 'original_contact':{'front_floor_y':185,'front_floor_x':[153,158],'rear_floor_y':186,'rear_floor_x':[179,184]},'lower_region_min_y':170},
 'b0_197':{'edit':'Bend/shorten only the long descending shin and boot naturally so the lowest toe returns x+2,y-4. Keep the raised glove, head, chest and other bent leg in exactly the same position.', 'original_contact':{'descending_floor_y':179,'descending_floor_x':[147,149]},'lower_region_min_y':162}}
for f in info['frames']:
 key=f['key'];p=P/'anchor_probe'/(key+'_indices.png');a=np.array(Image.open(p));old=np.array(Image.open(P/(key+'_before_indices.png')))
 Image.fromarray(a).save(O/(key+'_source_indices.png'));x,y=f['cell'];native.paste(rgba(a,pal).crop(crop),(x*96,y*96));original.paste(rgba(old,pal).crop(crop),(x*96,y*96))
 rows.append({**f,**spec[key],'source_indices_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_indices':p.relative_to(ROOT).as_posix(),'head_hand_source':'followthrough01 new art, eye-position registration; no old body restoration'})
native.save(O/'native_input.png');native.resize((1536,1536),Image.Resampling.NEAREST).save(O/'input.png')
original.save(O/'native_contact_reference.png');original.resize((1536,1536),Image.Resampling.NEAREST).save(O/'contact_reference.png')
out={**info,'frames':rows,'edit_target_generated_sha256':hashlib.sha256((P/'generated.png').read_bytes()).hexdigest(),'parent_style_archive_sha256':info['archive_sha256'],'preserve':'New detailed hair, face, hands, upper clothes, ribbon and transparency. Rearticulate lower limbs only; no wholebody scale or row deletion.','candidate':False,'applied':False}
(O/'inputs.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit.
Edit FIRST image only, our four newly drawn Rin maid pixel sprites in a 2 by 2 equal-cell sheet. SECOND image is the older version of exactly these four poses, used ONLY for lower-limb joint and foot contact positions, NOT for its coarse rendering. Preserve the first image\'s finely detailed hair, cyan eyes, short neck, face, cuffs, both hands, collar, blue bow, apron detail, flowing blue ribbon, and fixed upper-body position. Do not redraw or move heads, hands or upper torsos.
Correct only the lower-body pose and length. Each cell is96x96 native pixels, enlarged8x. TOP LEFT deep crouch: the newly drawn waist/skirt and legs hang about4 native pixels too low. Rearticulate the crouched hips and knees into the older compact crouch while keeping the rich new pleats; raise front boot about4pixels and move it right2, raise rear boot3 and left2. TOP RIGHT airborne recovery: keep lifted knee; bend the long descending shin and boot so its lowest toe moves up5 native pixels and left2, retaining natural calf thickness and detailed boot seams. BOTTOM LEFT standing recovery: bring front toe right2/up4 and rear toe left2/up3, preserving the bent-knee stance and natural leg width. BOTTOM RIGHT ladder entry: keep raised glove and upper body completely fixed; bend/shorten the descending shin naturally so the lowest toe moves right2/up4; keep the other bent leg.
Use the second image to place the ankle, sole and toe endpoints accurately in the same cell. Do NOT scale entire bodies, erase horizontal bands, shrink heads, turn boots into thin sticks, merge feet, or copy the old coarse artwork. All changed limbs must retain the first image\'s refined contour, distinct highlight/midtone/shadow and coherent knee/ankle joints. Do not add weapons, effects, floor, guide lines, labels or extra sprites. Keep the same equal96x96 cell margins and exact 2x2 layout, output1536x1536 transparent background, crisp pixel art with no smoothing.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(O)
