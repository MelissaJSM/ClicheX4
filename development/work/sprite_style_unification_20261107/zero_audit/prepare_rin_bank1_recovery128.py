"""뇌신격 마지막 회복128과 정확같은129/130/131의 원화 입력."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent/'rin_extension';P=D/'prepared_bank1_special02/PL01_U.ARC';O=D/'bank1_recovery128';assert not O.exists();O.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();arc=P.read_bytes();assert sha(arc)=='0f6073c262c0b851a1330b86fec51d1bae62838a73241b3e9140a0b7727a5d1e'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,104,208,200);n=128;z=render(arc,1,5,n)[0];outside=z.copy();outside[104:200,112:208]=0;assert not outside.any()
pic=rgba(z,pal);pic.save(O/'b1_128_before.png');Image.fromarray(z).save(O/'b1_128_before_indices.png');pic.crop(crop).save(O/'native_input.png');pic.crop(crop).resize((1536,1536),Image.Resampling.NEAREST).save(O/'input.png')
aliases=[]
for b in(0,1):
 for f in graphics_bank(entry(arc,2),b)['frames']:
  k=f['index']
  if b==1 and 42<=k<=49:continue
  if np.array_equal(z,render(arc,b,b*5,k)[0]):aliases.append(f'b{b}_{k:03}')
assert aliases==['b1_128','b1_129','b1_130','b1_131']
for label,b,n in [('idle147',0,147),('refined_preparation105',1,105),('refined_thrust119',1,119)]:rgba(render(arc,b,b*5,n)[0],pal).crop(crop).resize((1536,1536),Image.Resampling.NEAREST).save(O/(label+'.png'))
bank=graphics_bank(entry(arc,2),1);f=bank['frames'][128]
j={'actual_input_arc':str(P.relative_to(ROOT)),'archive_sha256':sha(arc),'crop':crop,'native_cell':[96,96],'output_canvas':[1536,1536],'scale':16,'origin':[160,160],'palette_words':list(pal),'frames':[{'key':'b1_128','bank':1,'ref':128,'cell':[0,0],'bounds':pic.getbbox(),'source_canvas_sha256':sha(z.tobytes()),'exact_aliases':aliases,'same_stream_refs':[q['index']for q in bank['frames']if q['offset']==f['offset']],'tile_count':f['tile_count'],'part_count':len(composition_frame(entry(arc,3),5,128)['parts'])}],'game_changed':False,'scope':'원래 마지막 회복 한 자세의 상세 통일. 정확같은128~131 네 참조에만 공유하며 손·발·눈높이와 원표를 보존.'}
(O/'inputs.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit. Edit only FIRST image, a SINGLE Rin maid pixel-art recovery pose on a fully transparent1536x1536 canvas. It is96x96 native pixels enlarged16x. Keep the exact native grid, canvas margins, character position and full figure. Other three images are accepted detailed STYLE references only; do not copy their different poses.
Preserve the first pose's forward lean, left-facing head angle and eye center, extended forward glove and short-tool grip endpoint, rear bent elbow, shoulder/collar position, original hips/knees, bent front shin, extended rear boot and both soles. It is the transitional recovery after a low thrust. Do not stand it upright or replace it with the reference idle. Keep natural substantial arms/thighs and the original short neck, body width and compact head scale.
Repaint coarse color blocks as coherent native pixel clusters: cool gray layered hair with subtle interior shadow, clearly visible compact cyan eye and small face, selective navy contours, defined chest ribbon and collar, dark bodice structure, layered white cuffs, pleated skirt/apron with delicate cool-gray folds, and boot material details. The accepted references show the requested level of detail. Keep the original scarf/ribbon sweep and hand/weapon connection. No new/longer weapon, effect, extra fingers/arms, text, guides, background, smoothing, silhouette expansion, body shrinking or elongated calves. Preserve all transparent padding.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(json.dumps(j))
