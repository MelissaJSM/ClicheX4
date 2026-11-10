"""Prepare authored-sprite-only next pages; do not generate or patch game data."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent/'rin_extension';P=D/'prepared_ground_first_v1/PL01_U.ARC'
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
arc=P.read_bytes();assert sha(arc)=='cf01c08e17c742983abcd566e08f165c2c48205b453d051ce64ea58ca1a8c0c1'
pal=struct.unpack_from('<16H',entry(arc,9));banks=[graphics_bank(entry(arc,2),b)for b in(0,1)]
displays={(b,f['index']):render(arc,b,b*5,f['index'])[0]for b,bank in enumerate(banks)for f in bank['frames']if not(b==1 and 42<=f['index']<=49)}
ap=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json';animations=json.loads(ap.read_text('utf8'))['animations']
pages=[('ground_followup01',[(0,n)for n in(71,73,82,131)],[('refined_attack61',0,61),('refined_attack67',0,67)]),('wall_saber01',[(1,n)for n in(50,51,54,57)],[('refined_wall39',0,39),('refined_attack63',0,63)])]
plans=[]
for name,keys,styles in pages:
 out=D/name;assert not out.exists();out.mkdir();crop=(112,112,208,208);native=Image.new('RGBA',(192,192));records=[]
 for i,(b,n)in enumerate(keys):
  a=displays[b,n];assert a.max()<16;pic=rgba(a,pal);outside=a.copy();outside[112:208,112:208]=0;assert not np.any(outside)
  native.paste(pic.crop(crop),(i%2*96,i//2*96));Image.fromarray(a).save(out/f'b{b}_{n:03}_before_indices.png')
  f=banks[b]['frames'][n]
  records.append({'key':f'b{b}_{n:03}','bank':b,'ref':n,'cell':[i%2,i//2],'bounds':pic.getbbox(),'source_canvas_sha256':sha(a.tobytes()),'exact_display_expansion_refs':[f'b{bb}_{nn:03}'for(bb,nn),v in displays.items()if np.array_equal(a,v)],'same_stream_refs':[g['index']for g in banks[b]['frames']if g['offset']==f['offset']],'tile_count':f['tile_count'],'part_count':len(composition_frame(entry(arc,3),b*5,n)['parts']),'native_animation_uses':[{'id':q['id'],'matching_positions':[s['position']for s in q['steps']if s['frame']==n],'sequence_refs':[s['frame']for s in q['steps']]}for q in animations if q['graphics_bank']==b and any(s['frame']==n for s in q['steps'])]})
 native.save(out/'native_input.png');native.resize((1536,1536),Image.Resampling.NEAREST).save(out/'input.png')
 for label,b,n in [('idle147',0,147)]+styles:rgba(displays[b,n],pal).crop(crop).resize((768,768),Image.Resampling.NEAREST).save(out/f'{label}.png')
 data={'actual_input_arc':rel(P),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,96],'columns':2,'rows':2,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':records,'animation_evidence':rel(ap),'animation_evidence_sha256':sha(ap.read_bytes()),'generated':False,'game_unchanged':True,'scope':'현재 사용자 교체 캐릭터 원화만 생성 입력으로 사용. 정확 같은 표시 공유 목록은 후보이며 무조건 전체 교체 승인으로 간주하지 않는다.'}
 (out/'inputs.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
 specific=('The four poses are ground sword follow-through and recovery. Upper-left follows the low swing, upper-right recovers with long hair curving behind, lower-left opens the arms into recovery, lower-right lifts the rear glove. Preserve their different knee angles and the exact existing short tool/grip positions. Do not extend the tool or add a sword blade. Keep all boots/toes planted at exactly the original contacts.' if name=='ground_followup01'else 'The four poses are wall-mounted sword attacks, including the side/back head view. Preserve each original facing, torso twist, wall glove position, bent knee and wall boot contact; do not turn every head into the idle front view. Keep the tiny short mop-handle grip and the arm/hand/effect attachment at the original coordinates. Do not invent a long mop shaft or blade. The refined wall39 reference illustrates accepted head volume, cuff/waist connection and detail, not a replacement whole-body pose.')
 prompt='Use case: precise-object-edit. Edit only the FIRST four-pose sheet, preserving its exact2x2 layout, fixed cell positions, scale and all four distinct motions. Rin is the white bob-haired blue-and-white maid with cyan eyes and blue ribboned hair. The other images are already approved detailed pixel-art style references. Repaint coarse faces, broad plain white cuffs, simple apron/skirt masses and flat boots into the detailed native pixel-art quality of idle147: separated cool-gray hair locks, small cyan eye with face planes, selective navy outlines, collar/ribbon structure, cuff folds, apron seams, crisp pleated skirt hem and small boot highlight planes. Use intentional small clusters rather than blur or noisy dithering. Preserve original head/eye center, short neck, shoulders/elbows, wrists/gloves, waist, knee and ankle contacts. Match idle upper-arm, waist, thigh and calf proportions; no pin-thin limbs, no swollen child head. '+specific+' All old poses must remain recognizable. Native cell96x96 is presented at8x nearest-neighbor: output exactly1536x1536 with four sprites and unchanged blank margins. Transparent background only. No text, grids, labels, extra sprites, floor shadows, weapons, effects or environment. Do not paste an idle body or replace an angle-specific head with another view.'
 (out/'prompt.txt').write_text(prompt+'\n','utf8');plans.append({'page':rel(out),'keys':[r['key']for r in records],'exact_groups':{r['key']:r['exact_display_expansion_refs']for r in records}})
report={'source_sha256':sha(arc),'prepared_pages':plans,'generated':False,'current_frozen_count':122,'remaining_whole_project':True,'priority_reason':'새 첫타 앞부분62..69와 이어지는71/73/82/131, 새벽 동작39와 이어지는벽공격50/51/54/57의 상세 차이를 먼저 줄인다.'}
(D/'next_after122.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(report,ensure_ascii=False))
