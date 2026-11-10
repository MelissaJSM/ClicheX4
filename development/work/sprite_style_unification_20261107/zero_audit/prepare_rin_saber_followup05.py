"""동결168에서 지상 검격의 다음 네 원화 입력을 만든다."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent/'rin_extension';P=D/'prepared_saber_followup04/PL01_U.ARC'
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
arc=P.read_bytes();assert sha(arc)=='8bfbf74ea8b14478d5b34906bbedf0e73d7a17689031c804545fb0a4ebac9c54'
out=D/'saber_followup05';assert not(out/'inputs.json').exists();out.mkdir(exist_ok=True)
pal=struct.unpack_from('<16H',entry(arc,9));banks=[graphics_bank(entry(arc,2),b)for b in(0,1)]
displays={(b,f['index']):render(arc,b,b*5,f['index'])[0]for b,bank in enumerate(banks)for f in bank['frames']if not(b==1 and 42<=f['index']<=49)}
ap=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json';animations=json.loads(ap.read_text('utf8'))['animations']
keys=[244,246];crop=(112,96,208,192);native=Image.new('RGBA',(192,96));records=[]
for i,n in enumerate(keys):
 a=displays[0,n];assert a.max()<16;pic=rgba(a,pal);outside=a.copy();outside[crop[1]:crop[3],crop[0]:crop[2]]=0;assert not np.any(outside),(n,pic.getbbox())
 native.paste(pic.crop(crop),(i%2*96,i//2*96));Image.fromarray(a).save(out/f'b0_{n:03}_before_indices.png');pic.save(out/f'b0_{n:03}_before.png');f=banks[0]['frames'][n]
 records.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[i%2,i//2],'bounds':pic.getbbox(),'source_canvas_sha256':sha(a.tobytes()),'exact_display_expansion_refs':[f'b{bb}_{nn:03}'for(bb,nn),v in displays.items()if np.array_equal(a,v)],'same_stream_refs':[g['index']for g in banks[0]['frames']if g['offset']==f['offset']],'tile_count':f['tile_count'],'part_count':len(composition_frame(entry(arc,3),0,n)['parts']),'native_animation_uses':[{'id':q['id'],'matching_positions':[s['position']for s in q['steps']if s['frame']==n],'sequence_refs':[s['frame']for s in q['steps']]}for q in animations if q['graphics_bank']==0 and any(s['frame']==n for s in q['steps'])]})
native.save(out/'native_input.png');native.resize((1536,768),Image.Resampling.NEAREST).save(out/'input.png')
for label,n in [('idle147',147),('refined_saber213',213),('refined_saber242',242)]:rgba(displays[0,n],pal).crop(crop).resize((768,768),Image.Resampling.NEAREST).save(out/f'{label}.png')
data={'actual_input_arc':rel(P),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,96],'columns':2,'rows':1,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':records,'animation_evidence':rel(ap),'animation_evidence_sha256':sha(ap.read_bytes()),'generated':False,'game_unchanged':True,'scope':'동결163 뒤 공중검격 마지막229 및 지상검격230/232/234. 자체 제작 린의 세부 표현을 재작화하며 원래 손/짧은 자루/발/무릎과 검기 접점을 보호한다.'}
data['scope']='Rin172 to grounded recovery244/246; fixed origin, hand/tool/foot contacts; artwork only.'
(out/'inputs.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='Use case: precise-object-edit. Edit only the FIRST two-pose sprite sheet. The remaining images are accepted detailed pixel-art style references of the SAME character Rin. White bob hair, cyan eyes, blue-and-white maid clothing, navy selective outlines, a trailing blue ribbon. The first image has TWO grounded attack recovery poses in a 2-column 1-row grid, each native cell96x96 enlarged8x. Maintain these exact poses, facing, head centers, elbow angles, glove and short tool handle positions, knee bends and toe locations. Repaint details only: separated cool-gray hair locks, clear small cyan eyes, compact cheek/chin, short neck, collar and chest bow structure, white cuff folds, apron seams/skirt folds, boot planes. Match accepted idle proportions without big round heads or thin limbs. Preserve each original raised rear hand angle and substantial forearms/thighs. No longer weapon, blade or swing effect. Preserve the whole long trailing ribbon shape and its motion. The two sprites stay at their original placement and size with exactly the same blank margins. Output exactly1536x768, transparent background, exactly TWO sprites arranged side by side. Pixel art on the existing 8x grid with crisp deliberate clusters, no blur, antialiasing, dithering, text, labels, grid, shadows, scenes or extra characters.'
(out/'prompt.txt').write_text(prompt+'\n','utf8')
print(json.dumps({'output':rel(out),'frames':records},ensure_ascii=False))
