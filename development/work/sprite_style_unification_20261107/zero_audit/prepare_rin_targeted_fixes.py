"""One native pose per transparent image for narrow head/leg corrections."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'rin_extension/targeted_fixes_inputs';OUT.mkdir(exist_ok=True)
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';arc=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,128,208,192);records=[]
for n in(17,18):
 folder=OUT/f'pose{n}';folder.mkdir(exist_ok=True);path=D/'rin_extension/run_inputs/run03_fix02/native'/f'b0_{n:03d}_indices.png';new=np.array(Image.open(path));old=render(arc,0,0,n)[0]
 for name,a in [('current_detail',new),('original_pose',old)]:
  cut=rgba(a,pal).crop(crop);assert np.count_nonzero(np.array(cut.getchannel('A')))==np.count_nonzero(a);cut.resize((1536,1024),Image.Resampling.NEAREST).save(folder/(name+'.png'));Image.fromarray(a).save(folder/(name+'_384_indices.png'))
 meta={'ref':n,'bank':0,'native_cell':[96,64],'crop':crop,'scale':16,'image_size':[1536,1024],'source_new':str(path.relative_to(ROOT)),'source_new_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_bin_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'head_translation_requested':[3,-4]if n==17 else[0,-3],'preserve_front_leg_pose':True,'back_foot_x_correction_approx':6 if n==17 else 0,'native_eye_target':[155,144]if n==17 else[152,144],'game_changed':False};(folder/'inputs.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8');records.append(meta)
(OUT/'manifest.json').write_text(json.dumps({'poses':records,'generated':False},ensure_ascii=False,indent=2)+'\n','utf8')
