"""종아리 길이가 늘어난 세 자세의 국소 원화 보완 입력을 만든다."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
D=Path(__file__).parent/'rin_extension'/'dash_saber_followup02';O=D/'local_legs01';assert not O.exists();O.mkdir()
info=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();assert hashlib.sha256(arc).hexdigest()==info['archive_sha256'];pal=info['palette_words']
native=Image.new('RGBA',(192,192));reference=native.copy();rows=[]
for i,n in enumerate((166,170,172)):
 a=np.array(Image.open(D/'anchor_probe'/f'b0_{n:03}_indices.png'));old=render(arc,0,0,n)[0];crop=(112,104,208,200)
 native.paste(rgba(a,pal).crop(crop),((i%2)*96,(i//2)*96));reference.paste(rgba(old,pal).crop(crop),((i%2)*96,(i//2)*96))
 Image.fromarray(a).save(O/f'b0_{n:03}_before_indices.png')
 rows.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[i%2,i//2],'upper_body_down_native_pixels':2 if n==166 else 3,
              'current_bbox':rgba(a,pal).getbbox(),'original_bbox':rgba(old,pal).getbbox(),'target_floor':int(np.nonzero(old)[0].max()),
              'old_eye':np.argwhere(old==15)[:,::-1].tolist(),'new_eye':np.argwhere(a==15)[:,::-1].tolist(),
              'before_indices_sha256':hashlib.sha256((O/f'b0_{n:03}_before_indices.png').read_bytes()).hexdigest()})
native.save(O/'native_input.png');reference.save(O/'native_pose_reference.png')
native.resize((1536,1536),Image.Resampling.NEAREST).save(O/'input.png');reference.resize((1536,1536),Image.Resampling.NEAREST).save(O/'pose_reference.png')
result={**info,'frames':rows,'scope':'새 세밀한 상체를 그대로 유지하며 길어진 종아리만 국소 원화 보완. 원게임 자산 입력 없음. 왼쪽 위166, 오른쪽 위170, 왼쪽 아래172, 오른쪽 아래 투명.',
        'source_art_sha256':hashlib.sha256((D/'generated.png').read_bytes()).hexdigest(),'native_cell':[96,96],'columns':2,'rows':2,'scale':8}
(O/'inputs.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit. Edit the FIRST transparent sprite image only. Three detailed Rin maid sprites sit in a fixed 2x2 grid: top-left166, top-right170, bottom-left172; keep bottom-right completely empty. Each cell is96x96 native pixels enlarged8x, total1536x1536. Second image shows the same poses before detailed repaint and is only the original joint-position reference, NOT an art style reference.
Correct ONLY the overlong lower legs of these three sprites. Keep all the new fine hair, head viewing angle, face, maid collar, sleeves/cuffs, bodice, apron pleats, pelvis, thigh volume and hand gestures. Move the complete existing head/torso/hips as a rigid unit DOWN by2 native pixels for top-left, and DOWN by3 native pixels for top-right and bottom-left; do not squash or redraw their details. Re-articulate only the knee-to-ankle area with naturally shorter boot shafts, preserving the existing knees and feet orientations and the exact current floor baseline. Match the original reference's foot contact positions and natural bent-knee lengths. Do not simply trim rows, shrink the entire body, stretch a thigh, merge shoes, narrow calves to sticks, or move the floor. Both boot interiors need gray/white modeled shading and selective navy outline like the existing detailed art. Keep the same character proportions and original stance width. No weapons, effects, labels or background. Truly transparent background; preserve exact grid margins and image dimensions.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(json.dumps(result,ensure_ascii=False))
