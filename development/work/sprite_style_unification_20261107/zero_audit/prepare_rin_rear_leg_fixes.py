from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';arc=(D/'prepared_third_saber_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,120,208,184)
for n in(186,190):
 O=D/f'rear_leg_fix_{n}';assert not O.exists();O.mkdir()
 a=np.array(Image.open(D/f'rear_continuation01/native/b0_{n:03}_indices.png'))
 if n==190:a=np.roll(a,1,axis=0)
 Image.fromarray(a).save(O/'refined_base_indices.png')
 for name,v in [('target',a),('original_pose',render(arc,0,0,n)[0]),('idle',render(arc,0,0,147)[0])]:rgba(v,pal).crop(crop).resize((1536,1024),Image.Resampling.NEAREST).save(O/f'{name}.png')
 spec=('The long lowered leg is the one extending diagonally down/right from the skirt. Its pale calf must stay diagonal and must be about6native pixels wide including the thin outline, instead of the current4-5pixels. Restore a rounded substantial ankle and fitted boot following that leg, with the boot toe center at native worldx160,y179. The other folded leg and its small shoe under the left hem must remain unchanged.'if n==186 else'The long lowered leg is the one extending down/right below the skirt. Its pale calf must be about6-7native pixels wide including the thin outline, instead of the current5pixels. Give the fitted boot a coherent ankle and instep, keep the foot tip centered at native worldx162,y176. The other folded knee and its small shoe under the left skirt hem remain unchanged. The target head and torso have deliberately been restored to their correct height: DO NOT move the whole body down or up while aligning the boot.')
 prompt=f'''Use case: precise-object-edit. Image1 is the edit target: ONE refined Rin rear-view pixel sprite. Image2 is her original identical movement pose for the exact leg gesture/foot contact and body anchors. Image3 is her approved idle for the proper solid calf/boot proportions and pixel detail. Edit only the long lowered visible leg below the skirt, fixing its overly thin calf and boot, while keeping its joint direction and planted/extended endpoint. {spec} Use the detailed new target's existing soft skin/white fitted boot and blue/navy shoe design, with clear pale highlight, cool-grey side shadow, thin selective navy edge and readable ankle. Do not repaint the coarse original outfit or copy its old head. Keep ALL of the target's NEW detailed head, hair strands, neck, arms, both gloves, torso, waist, apron, pleated skirt and long blue ribbon exactly unchanged; no movement, rescaling or redesign of those areas. Only the long lower leg is allowed to change. Keep the pose facing AWAY from the viewer. Do not show a front face, add equipment or effects. Native logical cell96x64 pixels enlarged16x to1536x1024, same sprite location as Image1. World origin160,160 falls at local48,40. The foot endpoint for this pose corresponds to local({160-112 if n==186 else 162-112},{179-120 if n==186 else 176-120}). Preserve fixed crop alignment. Deliberate late1990s pixel clusters, fine detail like the accepted target and idle; no blur, jagged thick outline, giant foot, stick-thin shin, smooth illustration or inflated leg. Fully transparent background, exactly one sprite with no text, grid, shadow or labels.'''
 (O/'prompt.txt').write_text(prompt+'\n','utf8')
 meta={'key':f'b0_{n:03}','crop':crop,'scale':16,'native_cell':[96,64],'base':str((O/'refined_base_indices.png').relative_to(ROOT)),'base_sha256':hashlib.sha256((O/'refined_base_indices.png').read_bytes()).hexdigest(),'only_edit':'long lowered leg','preserve_new_detailed_other_regions':True,'undo_generic_world_dy':1 if n==190 else 0,'foot_anchor':[160,179]if n==186 else[162,176]}
 (O/'inputs.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8')
 print(O)
