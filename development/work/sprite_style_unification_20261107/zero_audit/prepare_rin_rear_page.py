"""Four authored Rin rear poses; 13 precisely verified whole-body aliases."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'rear_continuation01';assert not O.exists();O.mkdir()
P=D/'prepared_third_saber_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)=='11d4c88a17983dd3e106d13af3938075803186c59045b0b372b0f813b3aa09ae'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,120,208,184);scale=8
def mirror(a):
 z=np.zeros_like(a);y,x=np.nonzero(a);z[y,319-x]=a[y,x];return z
aliases={178:{178:False,179:False,180:True,181:True},182:{182:False,183:False,184:True,185:True},186:{186:False,188:False,187:True,189:True},190:{190:False}}
native=Image.new('RGBA',(192,128));frames=[]
for i,n in enumerate(aliases):
 a=render(arc,0,0,n)[0];im=rgba(a,pal)
 for alias,flipped in aliases[n].items():assert np.array_equal(render(arc,0,0,alias)[0],mirror(a)if flipped else a),(n,alias)
 outside=a.copy();outside[crop[1]:crop[3],crop[0]:crop[2]]=0;assert not np.any(outside)
 native.paste(im.crop(crop),(i%2*96,i//2*64));Image.fromarray(a).save(O/f'b0_{n:03}_before_indices.png')
 frames.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[i%2,i//2],'bounds':im.getbbox(),'aliases':{str(k):{'mirror_x_319_minus_x':v}for k,v in aliases[n].items()}})
native.save(O/'native_input.png');native.resize((1536,1024),Image.Resampling.NEAREST).save(O/'input.png')
for name,n in [('idle147',147),('refined_rear174',174)]:rgba(render(arc,0,0,n)[0],pal).crop((112,112,208,192)).resize((768,640),Image.Resampling.NEAREST).save(O/f'{name}.png')
meta={'actual_input_arc':str(P.relative_to(ROOT)),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_bin_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,64],'columns':2,'rows':2,'scale':scale,'native_origin':[160,160],'palette_words':list(pal),'frames':frames,'exact_display_refs_after_expansion':13,'game_unchanged':True}
(O/'inputs.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit. Edit ONLY the FIRST image, a fixed 2-column by 2-row native pixel sprite sheet of four rear-view poses of Rin, a white bob-haired maid. The SECOND image is her recently refined rear-view pose and supplies the hair-strand, back-uniform, cuff and boot detail style. The THIRD image is her approved idle and supplies body proportions and the fine pixel-art quality; do NOT copy its forward-facing head into any rear view. All four targets face AWAY from the viewer, back of head visible. Top-left178 has one hand reaching high above the left of her head, the other bent at her right, one knee folded and the opposite boot down. Top-right182 has the right arm reaching diagonally high and the left arm low near her side, legs folded for climbing. Bottom-left186 reaches up/right with a distinctly different tucked knee and long ribbon hanging diagonally. Bottom-right190 has BOTH elbows bent outwards and both hands near shoulder height, skirt around the hips, one boot low. Preserve these exact different limb arrangements, directions and locations. Each input sprite already defines the correct head position and size, shoulders, both glove centers, elbows, knees, both boot tips and scarf/ribbon tip. Keep every one of those contact anchors fixed; no body rescaling, no vertical head bob change, no moving or straightening a limb. Repaint the insufficient details: separate the white bob into restrained cool grey interior shadow planes and fine strands, give the navy/white maid back clear seams/folds, keep the white apron straps and waist panel, restore crisp cuff volumes and layered pleated skirt/apron hem, and give the fitted boots coherent shin/ankle/foot shading. The long blue ribbon must retain its existing curve and length. The hair should be delicate clustered native pixel art, not a noisy scribbled white cloud, not thick black outlines. Match the approved idle's slender-but-solid upper arms, waist, thighs and boots; do not shrink the body or use pencil-thin limbs. Preserve the clothing design and rear orientation; do not invent visible front eyes, a face on the back of her head, new accessories, changed knee-length skirt or equipment. No ladder, weapon, effects, labels, text, borders, grid, backdrop or extra sprites. Transparent background. Polished late-1990s action-game native pixel art with selective thin navy outlines and clear small shadow planes, not smooth illustration and not flat colored blocks. Fixed logical canvas 192x128 pixels, four 96x64 cells, enlarged 8x to1536x1024. Keep the four cells and all per-cell positions exactly. Exactly four finished transparent sprites.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(json.dumps({'input':str(O),'alias_refs':13}))
