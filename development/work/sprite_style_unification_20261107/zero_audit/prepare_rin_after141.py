"""Prepare three residual ground/movement art pages; generated replacement art only."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent/'rin_extension';P=D/'prepared_ground_wall_v1/PL01_U.ARC';sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
arc=P.read_bytes();assert sha(arc)=='247b47bcbf91eea64697305ba5a705de02207682c46fbbab0b527f9df00d6bb6'
pal=struct.unpack_from('<16H',entry(arc,9));banks=[graphics_bank(entry(arc,2),b)for b in(0,1)]
displays={(b,f['index']):render(arc,b,b*5,f['index'])[0]for b,bank in enumerate(banks)for f in bank['frames']if not(b==1 and 42<=f['index']<=49)}
ap=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json';animations=json.loads(ap.read_text('utf8'))['animations']
pages=[('ground_second01',[83,85,87,89],[('refined_attack71',71),('refined_attack109',109)]),('ground_recovery01',[91,105,107,130],[('refined_attack73',73),('refined_recovery131',131)]),('movement_returns01',[133,134,3,4],[('refined_recovery131',131),('refined_run8',8)])]
plans=[]
for name,keys,styles in pages:
 out=D/name;assert not out.exists();out.mkdir();crop=(112,112,208,208);native=Image.new('RGBA',(192,192));records=[]
 for i,n in enumerate(keys):
  a=displays[0,n];assert a.max()<16;pic=rgba(a,pal);outside=a.copy();outside[112:208,112:208]=0;assert not np.any(outside)
  native.paste(pic.crop(crop),(i%2*96,i//2*96));Image.fromarray(a).save(out/f'b0_{n:03}_before_indices.png');f=banks[0]['frames'][n]
  records.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[i%2,i//2],'bounds':pic.getbbox(),'source_canvas_sha256':sha(a.tobytes()),'exact_display_expansion_refs':[f'b{bb}_{nn:03}'for(bb,nn),v in displays.items()if np.array_equal(a,v)],'same_stream_refs':[g['index']for g in banks[0]['frames']if g['offset']==f['offset']],'tile_count':f['tile_count'],'part_count':len(composition_frame(entry(arc,3),0,n)['parts']),'native_animation_uses':[{'id':q['id'],'matching_positions':[s['position']for s in q['steps']if s['frame']==n],'sequence_refs':[s['frame']for s in q['steps']]}for q in animations if q['graphics_bank']==0 and any(s['frame']==n for s in q['steps'])]})
 native.save(out/'native_input.png');native.resize((1536,1536),Image.Resampling.NEAREST).save(out/'input.png')
 for label,n in [('idle147',147)]+styles:rgba(displays[0,n],pal).crop(crop).resize((768,768),Image.Resampling.NEAREST).save(out/f'{label}.png')
 data={'actual_input_arc':rel(P),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,96],'columns':2,'rows':2,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':records,'animation_evidence':rel(ap),'animation_evidence_sha256':sha(ap.read_bytes()),'generated':False,'game_unchanged':True,'scope':'현재 교체 린 스프라이트만 입력. 기존 동작·발·손·짧은 자루 접점은 유지하며 세부묘사를 보완한다.'}
 (out/'inputs.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
 specific={'ground_second01':'These are four distinct second-swing ground poses. Keep every original elbow, glove, wrist, short tool-grip, wide knee angle, toe and floor contact. The arms move through different positions across the four frames; do not replace them by one idle arm. The white gloves must remain connected to the cuffs and short handle. Do not extend the weapon or draw a blade.',
 'ground_recovery01':'These are four distinct ground attack follow-through and recovery poses. The bottom-left lifts the rear glove while bottom-right has a lower center and forward glove. Preserve these original motions and differences, do not stand them all upright. Preserve short mop-handle/grip, exact wrists, elbow bends and fixed knee/boot contacts.',
 'movement_returns01':'Top row are two attack recovery motions with different rear glove/arm positions. Bottom row are two transition-to-movement poses; bottom-right bends and lifts a leg. Preserve the original head/neck tilt, raised-foot angle, toe positions and stance widths. Do not merge different motions or move any contact to match the idle pose.'}[name]
 prompt='Use case: precise-object-edit. Edit only the FIRST four-pose sheet. Preserve its exact2x2 layout, fixed cell positions, original facing, pose, motion and native scale. The other images are accepted detailed pixel-art references for the same Rin character: white bob hair, cyan eyes, blue-and-white maid clothes, navy outlines, blue ribboned trailing hair. Repaint the coarse existing faces and plain cuffs/apron/skirt/boots into the detail level of idle147: separated cool-gray hair locks, small cyan eyes and face planes, selective navy outlines, collar/ribbon structure, cuff folds, apron seams, pleated skirt edges and boot planes. No fuzzy antialiasing, dithering or blocky fat contours. Keep the original head/eye center, short neck, shoulders, upper-arm thickness, waist, thighs and calves at idle proportion; no swollen heads or stick-thin legs. '+specific+' Do not paste the idle body or turn angle-specific faces into a front-facing face. All four original poses must stay immediately recognizable. Native cell96x96 is shown at8x: output exactly1536x1536 with four sprites and unchanged blank margins. Transparent background. No text, labels, grid, extra sprites, floor shadows, new accessories, effects or environment.'
 (out/'prompt.txt').write_text(prompt+'\n','utf8');plans.append({'page':rel(out),'keys':[r['key']for r in records],'exact_groups':{r['key']:r['exact_display_expansion_refs']for r in records}})
report={'source_sha256':sha(arc),'prepared_pages':plans,'generated':False,'current_frozen_count':141,'remaining_whole_project':True,'priority_reason':'완료 첫타/3타 사이의 구형2타·회복과 새달리기 진입3/4를 우선 연결한다. 기존 참조는91/93 외 전신 동일 관계가 없다.'}
(D/'next_after141.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(report,ensure_ascii=False))
