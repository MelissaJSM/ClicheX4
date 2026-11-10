"""Read-only extraction of four coarse air-saber poses from frozen Rin154."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent/'rin_extension';P=D/'prepared_ground_remaining_v1/PL01_U.ARC'
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
arc=P.read_bytes();assert sha(arc)=='a8a268fa92912678e70b01b776ffa477dd46c16e791f16f3346c76cd55016319'
out=D/'air_saber01';assert not out.exists();out.mkdir()
pal=struct.unpack_from('<16H',entry(arc,9));banks=[graphics_bank(entry(arc,2),b)for b in(0,1)]
displays={(b,f['index']):render(arc,b,b*5,f['index'])[0]for b,bank in enumerate(banks)for f in bank['frames']if not(b==1 and 42<=f['index']<=49)}
ap=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json';animations=json.loads(ap.read_text('utf8'))['animations']
keys=[213,215,217,219];crop=(112,112,208,208);native=Image.new('RGBA',(192,192));records=[]
for i,n in enumerate(keys):
 a=displays[0,n];assert a.max()<16;pic=rgba(a,pal);outside=a.copy();outside[112:208,112:208]=0;assert not np.any(outside)
 native.paste(pic.crop(crop),(i%2*96,i//2*96));Image.fromarray(a).save(out/f'b0_{n:03}_before_indices.png');pic.save(out/f'b0_{n:03}_before.png');f=banks[0]['frames'][n]
 records.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[i%2,i//2],'bounds':pic.getbbox(),'source_canvas_sha256':sha(a.tobytes()),'exact_display_expansion_refs':[f'b{bb}_{nn:03}'for(bb,nn),v in displays.items()if np.array_equal(a,v)],'same_stream_refs':[g['index']for g in banks[0]['frames']if g['offset']==f['offset']],'tile_count':f['tile_count'],'part_count':len(composition_frame(entry(arc,3),0,n)['parts']),'native_animation_uses':[{'id':q['id'],'matching_positions':[s['position']for s in q['steps']if s['frame']==n],'sequence_refs':[s['frame']for s in q['steps']]}for q in animations if q['graphics_bank']==0 and any(s['frame']==n for s in q['steps'])]})
native.save(out/'native_input.png');native.resize((1536,1536),Image.Resampling.NEAREST).save(out/'input.png')
for label,n in [('idle147',147),('refined_air21',21),('refined_attack109',109)]:rgba(displays[0,n],pal).crop(crop).resize((768,768),Image.Resampling.NEAREST).save(out/f'{label}.png')
data={'actual_input_arc':rel(P),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,96],'columns':2,'rows':2,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':records,'animation_evidence':rel(ap),'animation_evidence_sha256':sha(ap.read_bytes()),'generated':False,'game_unchanged':True,'scope':'동결154 뒤 공중검격4키. 현재 자체 제작 린만 입력하며 원래 손/짧은 자루/발/무릎과 검기 접점을 보호한다. 전체 포즈의 미술 세부만 재작화한다.'}
(out/'inputs.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='Use case: precise-object-edit. Edit only the FIRST four-pose sprite sheet. The other three images are accepted detailed pixel-art style references of the SAME character Rin: white bob hair, cyan eyes, blue-and-white maid clothing, navy outlines, blue trailing ribbon. The first sheet has four different airborne short-mop-handle slash poses in a precise 2x2 grid. Preserve each facing, pose, head center, elbow angle, glove and short-handle contact, knee bend, boot angle and toe location. Keep exactly the same native scale and placement in each96x96cell. This is a detail repaint, not a motion redesign. Replace coarse white hair blobs and flat cuffs/apron/boots with the refined idle reference level: cool-gray separated hair locks, small clear cyan eye, compact cheek and chin planes, selective navy contours, structured collar and bow, cuff folds, apron seams and skirt folds, distinct boot planes. Match idle head/body proportions: neither oversized round face nor thin stick limbs. Keep a short neck, substantial forearms and thighs. Do not paste the idle pose, enlarge gloves or change airborne leg folds. The short dark tool grip must remain in the original hand position; no longer shaft, sword blade, swing trail or effects. Output exactly1536x1536, four sprites only, unchanged blank cell margins. Pixel art on the existing8x native grid, crisp deliberate clusters without blur, antialiasing or dithering. Transparent background. No text, labels, grid lines, shadows, scene or additional characters.'
(out/'prompt.txt').write_text(prompt+'\n','utf8')
print(json.dumps({'output':rel(out),'source_sha256':sha(arc),'frames':records},ensure_ascii=False))
