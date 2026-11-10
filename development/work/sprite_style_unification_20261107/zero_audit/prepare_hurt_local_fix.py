from pathlib import Path
import json,sys,struct,hashlib
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';S=D/'hurt_lowhp01';O=D/'hurt135139_fix01';assert not O.exists();O.mkdir()
arc=(D/'prepared_movement_finish_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));box=(112,96,208,224)
for label in ('input','pose_reference'):
 page=Image.new('RGBA',(192,128));records=[]
 for k,n in enumerate((135,139)):
  a=np.array(Image.open(S/'native'/f'b0_{n:03}_indices.png'))if label=='input'else render(arc,0,0,n)[0]
  page.paste(rgba(a,pal).crop(box),(k*96,0));records.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[k,0]})
 page.resize((1536,1024),Image.Resampling.NEAREST).save(O/f'{label}.png')
rgba(render(arc,0,0,147)[0],pal).crop(box).resize((768,1024),Image.Resampling.NEAREST).save(O/'idle_style_reference.png')
info=json.loads((S/'inputs.json').read_text('utf8'));info.update({'actual_input_arc':str((D/'prepared_movement_finish_v1/PL01_U.ARC').relative_to(ROOT)),'archive_sha256':hashlib.sha256(arc).hexdigest(),'crop':list(box),'native_cell':[96,128],'columns':2,'rows':1,'frames':[{**f,'cell':[k,0]}for k,f in enumerate(info['frames'][:2])],'scope':'새 피격2자세의 국소 비례/관절 보완. 원래 자세는 이미 저작한 린 스프라이트이며 원본게임 아트가 아니다.'})
(O/'inputs.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Edit the FIRST transparent sprite sheet only. It has two separate pixel-art poses of the SAME authored white-haired blue maid character Rin, side by side, fixed equal 96x128 native pixel cells enlarged 8x to a 1536x1024 sheet. Output the same sheet layout and true transparent alpha, no text or guides. The SECOND image is the exact old authored pose/anchor reference, not the target texture. THIRD is the accepted idle art reference for head proportions and pixel-detail quality.

This is a narrow anatomy and pose alignment correction. Keep the newly detailed hair strands, selective navy contour, white/gray cuffs, blue apron fold planes, thigh/boot shading and the same costume from FIRST. Do not replace them with the older simpler art. But the first sheet made both torsos too tall: faces, shoulders, hands and hips sit 2-3 native pixels too high while the soles are already at the correct height. Redraw just the connecting anatomy so each pose matches SECOND's joint positions naturally, without slicing or squashing the body. Keep both feet at the old ground contact points and preserve the old bent-knee stance and recoil/lean.

LEFT pose 135 anchors in its native cell: visible eye around(40,47), left wrist(30,51), right wrist(47,60), front upper thigh center(27,67), back thigh center(36,70), floor y85. Current FIRST eye is about(41,44), wrists y49/57, thighs y65/67. Move and connect the upper body down about2-3 pixels while the feet stay put. Match original narrow but detailed 3/4 head silhouette; keep hair strands and compact jaw, not an enlarged balloon head. Do not lengthen the neck.

RIGHT pose139 anchors in its own cell: eye(46,48), left wrist near(36,54), right wrist(57,60), thighs near(36,69) and(47,70), rear floor y86. FIRST eye/shoulders are about2 pixels high. Make the head a compact detailed shape compatible with the idle, not a wide round face; preserve the visible cyan eye and layered bangs. Restore natural hip/knee positions while keeping the two new boots' tips and soles aligned to SECOND.

Keep entire sprites centered at exactly the old reference world origin and the two cells unchanged. Work as native game pixel art with clean small tonal clusters, one-pixel selective outline and explicit garment seams, not smooth painting or blur. No overall rescale, no added weapons/effects, no white background, no shadows on a floor. Keep all existing costume colors and pose directions. Only these two corrected poses in the output.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(str(O))
