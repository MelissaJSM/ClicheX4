"""Prepare four coarse bank1 bodies and exact aliases, without changing resources."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent/'rin_extension';P=D/'prepared_bank1_special01/PL01_U.ARC';O=D/'bank1_special02';assert not O.exists();O.mkdir()
sha=lambda v:hashlib.sha256(v).hexdigest();arc=P.read_bytes();assert sha(arc)=='989b68597fa276164a16902806136f897c16ef3c1c81950b3b16fa039bede7a0'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,104,208,200);canvas=Image.new('RGBA',(192,192));refs=(108,110,112,119)
allframes={(b,f['index']):render(arc,b,b*5,f['index'])[0]for b in(0,1)for f in graphics_bank(entry(arc,2),b)['frames']if not(b==1 and 42<=f['index']<=49)}
ap=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json';animations=json.loads(ap.read_text('utf8'))['animations'];bank=graphics_bank(entry(arc,2),1);frames=[]
for i,n in enumerate(refs):
 z=allframes[1,n];pic=rgba(z,pal);outside=z.copy();outside[104:200,112:208]=0;assert not outside.any();x,y=i%2,i//2;canvas.paste(pic.crop(crop),(x*96,y*96));pic.save(O/f'b1_{n:03}_before.png');Image.fromarray(z).save(O/f'b1_{n:03}_before_indices.png')
 aliases=[f'b{b}_{j:03}'for(b,j),other in allframes.items()if np.array_equal(z,other)];f=bank['frames'][n]
 usages=[{'animation_id':a['id'],'position':s['position'],'frame':s['frame'],'duration_calls_uninterrupted':s['duration_calls_uninterrupted'],'event_bits':s['event_bits']}for a in animations if a['graphics_bank']==1 for s in a['steps']if s['frame']in[int(k[3:])for k in aliases if k.startswith('b1_')]]
 frames.append({'key':f'b1_{n:03}','bank':1,'ref':n,'cell':[x,y],'bounds':pic.getbbox(),'source_canvas_sha256':sha(z.tobytes()),'exact_aliases':aliases,'same_stream_refs':[q['index']for q in bank['frames']if q['offset']==f['offset']],'tile_count':f['tile_count'],'part_count':len(composition_frame(entry(arc,3),5,n)['parts']),'original_animation_usages':usages})
canvas.save(O/'native_input.png');canvas.resize((1536,1536),Image.Resampling.NEAREST).save(O/'input.png')
for label,b,n in [('idle147',0,147),('refined_ground71',0,71),('refined_saber111',0,111)]:rgba(render(arc,b,b*5,n)[0],pal).crop(crop).resize((768,768),Image.Resampling.NEAREST).save(O/(label+'.png'))
info={'actual_input_arc':str(P.relative_to(ROOT)),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,96],'columns':2,'rows':2,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':frames,'animation_source':str(ap.relative_to(ROOT)),'animation_source_sha256':sha(ap.read_bytes()),'candidate_parent_art_pending':True,'game_unchanged':True,'scope':'지상 준비/회복 뱅크의 서로 다른4자세. 기존 몸통의 단색 면과 커프·부츠·머릿결을 정밀화한다. 실제 원표의 손/발/방향은 유지하며 원검기와 소리는 입력 그림에서 제외한다. 전체같은101/103·105/107만 새 그림 공유 허용.'}
(O/'inputs.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit. Edit only FIRST image: four separate Rin maid pixel-art poses in the exact original2x2 layout. Each cell is96x96 native pixels enlarged8x, output1536x1536, truly transparent. Other pictures are approved fine-detail STYLE references only. All four original poses differ: preserve the shown body facing, head angle and eye/ear center, collar/shoulder location, bent elbows, glove/short grip center, hips/knees, boot angles and sole positions. Do not replace a pose with a standing idle, mirror it, move it within its cell or enlarge its silhouette.
Repaint the whole coarse body at the reference level of restrained cool-gray hair locks with internal shadows, compact cyan-eyed face, selective navy contour, structured dark bodice, chest ribbon, layered broad white cuffs, pleated apron/skirt panels and detailed boots. Keep a short neck and substantial natural upper arms/thighs. Preserve the existing movement/weight shift and bent knee geometry. These are LOW FORWARD THRUST poses. Keep the extended forward arm and glove/grip endpoint exactly fixed, with the low bent front knee and extended rear leg in their original orientations. Do NOT stand upright, lengthen the neck, thicken or lengthen the arm, or straighten the bent knee. The original glove centers and short tool contact must remain. No extra or lengthened weapon, blade, effect, new accessory, text, labels, guides or background. Fine native pixel clusters rather than flat white/black blobs; no smoothing, filtering, body shrinking or stretched calves. Keep exact canvas/cell margins and full poses.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(json.dumps({'out':str(O),'refs':refs,'aliases':[f['exact_aliases']for f in frames]}))
