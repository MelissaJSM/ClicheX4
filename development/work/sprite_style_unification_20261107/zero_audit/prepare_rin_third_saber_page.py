"""Prepare authored-Rin-only fixed-grid references; no game mutation."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'third_saber01';assert not O.exists();O.mkdir()
P=D/'prepared_burst_pair_final_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='10f1cc28662a8ceae3b3e00c305fdbeeb0e7e16bc21c13d65a05fadc19e19ca3'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,124,208,188);scale=8
native=Image.new('RGBA',(192,128));frames=[]
for i,n in enumerate([109,111,113,115]):
 a=render(arc,0,0,n)[0];im=rgba(a,pal);native.paste(im.crop(crop),(i%2*96,i//2*64))
 Image.fromarray(a).save(O/f'b0_{n:03}_before_indices.png')
 frames.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[i%2,i//2],'bounds':im.getbbox()})
native.save(O/'native_input.png');native.resize((1536,1024),Image.Resampling.NEAREST).save(O/'input.png')
for name,n in [('idle147',147),('refined61',61)]:
 rgba(render(arc,0,0,n)[0],pal).crop(crop).resize((768,512),Image.Resampling.NEAREST).save(O/f'{name}.png')
meta={'actual_input_arc':str(P.relative_to(ROOT)),'archive_sha256':sha(arc),'character':'rin',
      'crop':crop,'native_cell':[96,64],'columns':2,'rows':2,'scale':scale,'native_origin':[160,160],
      'palette_words':list(pal),'frames':frames,'exact_display_aliases':{'b0_115':[115,117,119]},
      'preserve_existing_pose_not_riko_alias_assumption':True,'game_unchanged':True}
(O/'inputs.json').write_text(json.dumps(meta,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit. Edit the FIRST image: a fixed2-column by2-row pixel sprite sheet containing four different poses of the SAME white-haired maid action-game character Rin. Image2 is the approved IDLE style/body-proportion reference; Image3 is her recently refined attack-ready rendering. Draw only the four target poses in Image1, in their existing cells. Preserve all four different original poses and their fixed positions, facing LEFT. Top-left109 has the far hand raised above/behind the head and a braced step; top-right111 leans forward with the near glove low/front and long ribbon flowing right; bottom-left113 braces wide with the forward fist near the chest and the ribbon lifted high diagonally to the right; bottom-right115 has a lower/later swing posture with the arms closer to the chest and the ribbon curving nearly vertically upward. These are distinct frames: do not repeat one pose, rotate another frame, mirror the character, or change the foot stance. Keep both toe contact positions, knee bend, wrists/glove centers, shoulder positions, original eye/head level, same neck length and each frame's particular ribbon curve. The source already gives correct physical movement and anchoring. Repaint fine details to match the idle and refined reference: crisp small cyan eye, cheek and delicate chin, separate white bob-hair strands with cool grey interior shadows, thin selectively colored navy outline, structured maid bodice and blue chest/waist panels, white collar, substantial sleeves and cuffs, folded blue skirt and white apron, and white fitted boots with coherent shin/ankle/instep shading. Preserve the recognizable white bob, cyan eye, dark maid uniform, blue apron/skirt panel and long blue ribbon; no costume redesign. Avoid the target's old broad flat white face and featureless dark bodice. Keep the SAME head volume, upper-arm/waist/thigh thickness as the idle: no oversized doll head, no long skinny neck, no pencil-thin arms/waist/boots, no broad inflated silhouette. Do not add a full sword, broom, projectile, glowing effects, motion blur, text, labels, grid lines, border or backdrop. This is polished late1990s action-game native pixel art with deliberate small clusters, not smooth illustration and not a blocky low-detail caricature. Logical canvas192x128pixels: four equal96x64cells, enlarged8x to1536x1024. Maintain that fixed sheet layout and per-cell locations, with ample fully transparent separation. Fully transparent background. Exactly four sprites and nothing else.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(O)
