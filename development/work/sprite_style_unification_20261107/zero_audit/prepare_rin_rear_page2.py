"""Prepare the remaining distinct rear locomotion poses from frozen Rin75."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
from src.psx_player import graphics_bank
D=Path(__file__).parent/'rin_extension';O=D/'rear_continuation02';assert not O.exists();O.mkdir()
P=D/'prepared_rear_continuation_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)=='806b3871055233a5c37c1c2c17685e02aadd07d647be62ea69bf696787f3fbe4'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,104,208,184);scale=8
aliases={191:[191],192:[192],194:[194],195:[195,196]}
native=Image.new('RGBA',(192,160));frames=[];comparisons=[]
for i,n in enumerate(aliases):
 a=render(arc,0,0,n)[0];im=rgba(a,pal)
 for alias in aliases[n]:assert np.array_equal(render(arc,0,0,alias)[0],a),(n,alias)
 outside=a.copy();outside[crop[1]:crop[3],crop[0]:crop[2]]=0;assert not np.any(outside)
 native.paste(im.crop(crop),(i%2*96,i//2*80));Image.fromarray(a).save(O/f'b0_{n:03}_before_indices.png')
 bank=graphics_bank(entry(arc,2),0);f=bank['frames'][n]
 frames.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[i%2,i//2],'bounds':im.getbbox(),'aliases':aliases[n],'shared_stream_refs':[q['index']for q in bank['frames']if q['offset']==f['offset']],'native_tile_count':f['tile_count']})
 comparisons.append((f'b0_{n:03} current',im))
native.save(O/'native_input.png');native.resize((1536,1280),Image.Resampling.NEAREST).save(O/'input.png')
for name,n in [('idle147',147),('refined_rear186',186)]:rgba(render(arc,0,0,n)[0],pal).crop((112,104,208,184)).resize((768,640),Image.Resampling.NEAREST).save(O/f'{name}.png')
page(comparisons,rgba(render(arc,0,0,147)[0],pal),O/'selection_review.png',cols=2,scale=6)
meta={'actual_input_arc':str(P.relative_to(ROOT)),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,80],'columns':2,'rows':2,'scale':scale,'native_origin':[160,160],'palette_words':list(pal),'frames':frames,'exact_display_refs_after_expansion':5,'game_unchanged':True,'review_reason':'남은 후면191/192/194/195의 머리 흰 면과 등·치마·부츠 명암이 새178~190 및 대기147보다 단순하다.193은 정면이라 이 페이지와 분리한다.','generated':False}
(O/'inputs.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit. Edit only the FIRST image, a fixed 2-column by 2-row transparent pixel sprite sheet containing four distinct rear/side-rear poses of Rin, the white bob-haired maid. The second image is her recently completed detailed rear pose and is the exact target for the layered hair, uniform seams, cuff, pleated skirt and boot rendering. The third image is her approved idle; use its fine pixel-art and solid slender body proportions, never transplant its front-facing head onto these rear poses. Preserve all four source silhouettes' pose meanings, directions and exact spatial anchors. Top-left191 reaches high at the LEFT of her head with one gloved hand, has her back almost upright, one knee tucked and a long lower leg down; her whole body is visibly HIGHER in the cell than the other poses, do not recenter it. Top-right192 leans diagonally forward/left, arm bent upward/left, bent knee and foot reaching below; preserve that forward lean. Bottom-left194 has her right arm stretched overhead at the RIGHT of the head and the other arm bent out to the LEFT, one knee folded up and opposite leg descending diagonally; do not replace it with the top-left pose. Bottom-right195 has the high hand at the LEFT of the head, side/rear body facing left, rounded folded thigh and a boot down-left, and the ribbon trailing right; preserve its distinct knee and arm positions. Keep the crown position, head size, chin/neck, both glove centers, shoulders, elbows, both knees, ankles and boot toe contact points in the original logical pixel locations. No whole-body translations, no resizing, no new head bob or altered stride. Repaint the overly plain hair as layered cool-white hair with small cool-grey interior shadow planes, crisp individual locks and restrained navy selective outlines. Refine the back seam, white apron straps and fitted waist, cuff volume, pleated skirt/apron hem, stocking and boot material. Preserve the existing maid design, scarf/ribbon path and blue accents. Match the approved idle's solid slender arms, waist and legs: the long shin must have believable calf volume, roughly5-7 native pixels at its visible broadest cross section where appropriate, a distinct ankle and properly connected toe/heel, not a pencil-thin line. Do not lengthen limbs to achieve width; retain bent-knee geometry and shorten nothing. No visible front face or front apron pasted on the back. No extra accessories, ladder, weapon, labels, grid, borders, effects or scenery. Native late-1990s action-game pixel art: fine but readable clustered highlights and folds, no scribbled noise, smooth painting or flat featureless blocks. Exactly four sprites, transparent background. Logical192x160 canvas with four96x80 cells, enlarged8x to1536x1280. Keep every cell, anchor and offset exactly. Repaint details throughout the four sprites while preserving poses.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(json.dumps({'input':str(O),'alias_refs':5,'frames':frames}))
