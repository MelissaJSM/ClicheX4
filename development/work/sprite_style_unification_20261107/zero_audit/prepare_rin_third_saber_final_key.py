from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'third_saber121_01';assert not O.exists();O.mkdir()
P=D/'prepared_burst_pair_final_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='10f1cc28662a8ceae3b3e00c305fdbeeb0e7e16bc21c13d65a05fadc19e19ca3'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,124,208,188)
a=render(arc,0,0,121)[0];Image.fromarray(a).save(O/'b0_121_before_indices.png')
for name,arr in [('input',a),('refined115',np.array(Image.open(D/'third_saber01/native/b0_115_indices.png'))),('idle147',render(arc,0,0,147)[0])]:
 rgba(arr,pal).crop(crop).resize((1536,1024),Image.Resampling.NEAREST).save(O/(name+'.png'))
meta={'actual_input_arc':str(P.relative_to(ROOT)),'archive_sha256':sha(arc),
      'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720',
      'character':'rin','crop':crop,'native_cell':[96,64],'columns':1,'rows':1,'scale':16,'native_origin':[160,160],
      'palette_words':list(pal),'frames':[{'key':'b0_121','bank':0,'ref':121,'cell':[0,0],'bounds':rgba(a,pal).getbbox()}],
      'exact_display_aliases':{'b0_121':[121,123,125,127]},'game_unchanged':True}
(O/'inputs.json').write_text(json.dumps(meta,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit. Repaint only Image1, ONE pixel sprite of Rin, a white-haired maid action-game character, in a late1990s console pixel-art style. Image2 is the newly refined preceding animation frame115, a STYLE AND ANATOMY reference only; Image3 is the accepted idle-body-proportion reference. The target121 must retain its own distinct posture, eye/head location, torso angle, front wrist/closed glove contact in front of her chest, both knee bends, both toe locations, ground level, and its shorter blue ribbon curving upward and toward the right. Do NOT copy Image2's taller ribbon or alter121's arm/leg pose. Preserve the original fixed sprite position on the96x64 logical canvas, enlarged16x to1536x1024. Keep the head volume, sleeve thickness, short attached neck, torso/waist and thighs consistent with the idle, without making the character thin. Fine rendering: small readable cyan eye and cheek/chin; separated white bobbed hair strands with cool grey interior shadows; thin selective navy contour; clear white collar and cuffs, dark maid bodice, blue skirt panel, white apron with small folds; coherent shin, ankle and instep shadows on white fitted boots. The target currently has a flat white face and featureless dark body: replace those with refined actual pixel clusters like Image2, while preserving pose and anchors. Maintain her existing costume, blue ribbon length/curve and same face direction LEFT. The front forearms remain together as in Image1. Do not add any sword, broom, weapon, projectile or glowing effect. No alternate pose, duplicate character, labels, grid lines, text, border or shadows on the background. Exactly ONE sprite on a fully transparent background with a clean hard alpha silhouette; NO blue haze, glow, gradient, vignette, backdrop, floor or cast shadow. Deliberate crisp native-scale pixel clusters, not smooth illustration or inflated doll proportions. Do not crop, zoom, enlarge the head, lengthen the neck or change the source's foot stance.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(O)
