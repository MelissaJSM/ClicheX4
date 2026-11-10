"""누적200 이후 용염인/사다리 준비 네 자세의 새 미술 입력."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent/'rin_extension';P=D/'prepared_spin01/PL01_U.ARC';O=D/'followthrough01';assert not O.exists();O.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();arc=P.read_bytes();assert sha(arc)=='cf0b079549ea6f1968f3eeb8be37541583f070c134a628c7ea5131fc745dee2a'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,104,208,200);native=Image.new('RGBA',(192,192));frames=[]
for i,(b,n)in enumerate([(1,146),(1,156),(1,158),(0,197)]):
 a=render(arc,b,b*5,n)[0];pic=rgba(a,pal);outside=a.copy();outside[104:200,112:208]=0;assert not outside.any();x,y=i%2,i//2;native.paste(pic.crop(crop),(x*96,y*96));pic.save(O/f'b{b}_{n:03}_before.png');Image.fromarray(a).save(O/f'b{b}_{n:03}_before_indices.png')
 bank=graphics_bank(entry(arc,2),b);f=bank['frames'][n];frames.append({'key':f'b{b}_{n:03}','bank':b,'ref':n,'cell':[x,y],'bounds':pic.getbbox(),'source_canvas_sha256':sha(a.tobytes()),'same_stream_refs':[q['index']for q in bank['frames']if q['offset']==f['offset']],'tile_count':f['tile_count'],'part_count':len(composition_frame(entry(arc,3),b*5,n)['parts'])})
native.save(O/'native_input.png');native.resize((1536,1536),Image.Resampling.NEAREST).save(O/'input.png')
for label,b,n in [('idle147',0,147),('refined_rising144',1,144),('refined_air213',0,213)]:rgba(render(arc,b,b*5,n)[0],pal).crop(crop).resize((768,768),Image.Resampling.NEAREST).save(O/(label+'.png'))
info={'actual_input_arc':rel(P),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,96],'columns':2,'rows':2,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':frames,'game_unchanged':True,'scope':'용염인146 웅크림/156 공중회복/158 지상복귀와 사다리197 진입. 각 손·발목·머리각도 및 원점을 유지하면서 전체 새 상세 원화로 보완. 기존 효과는 입력에 없다.'}
(O/'inputs.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='Use case: precise-object-edit. Edit FIRST image only: FOUR Rin maid pixel sprites in a TWO BY TWO grid, equal96x96 native cells enlarged8x,1536x1536 output. The other images are approved finely detailed sprites of the same Rin, for rendering STYLE and natural body volume. Preserve the FOUR exact original poses and per-cell position and size: TOP LEFT a deep crouching preparation, front glove held near the chest and one foot planted forward; TOP RIGHT an airborne recovery with both arms low and one knee bent up, the other shin descending; BOTTOM LEFT a feet-apart standing recovery, hands at sides; BOTTOM RIGHT a ladder-entry pose with one glove raised above her head and one glove low at chest, one long leg pointing down and the other bent. Preserve their exact head angles, eye centers, neck attachment, shoulder/elbow/hand centers, bent knee directions, ankle and toe endpoints, and trailing blue ribbon direction. Repaint every pose with precise gray-white hair strand planes and a small cyan iris, selective navy contours, actual collar/chest bow construction, substantial folded cuffs, structured apron/skirt panels and hem, and boot seam/highlight/shadow detail comparable to the reference. No broad flat white blobs, no enlarged head or rounded baby face, no tiny stick thighs or narrowing of arms. Do not change leg pose or merge the two feet. Natural short neck, same character proportions as47-native-pixel-high idle; do not make every pose47pixels tall. Keep current per-pose scale. No new tool shaft, slash, fire, ice, light effect, captions, labels, extra sprites, ground or scenery. Crisp pixel clusters, transparent background, no blur. Output exactly1536x1536,2x2 layout with the same blank margins.'
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(O)
