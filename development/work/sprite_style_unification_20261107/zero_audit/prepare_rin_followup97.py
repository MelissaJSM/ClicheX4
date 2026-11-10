"""Prepare fixed-origin remaining movement and hurt master inputs only."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank
D=Path(__file__).parent/'rin_extension';P=D/'prepared_wall_followup_v2/PL01_U.ARC';arc=P.read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert sha(arc)=='289370272eb51e377435e3fea0591921f4497fe3774d1f41e1d15d4d76d22ca2'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,208)
anim_path=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json'
animations=json.loads(anim_path.read_text('utf8'))['animations']
playback_path=ROOT/'work/sprite_consistency_20261105/playback/manifest.json'
labels={a['id']:a['label']for a in json.loads(playback_path.read_text('utf8'))['characters']['rin']['forms']['normal']['animations']}
bank=graphics_bank(entry(arc,2),0);displays={n:render(arc,0,0,n)[0]for n in range(len(bank['frames']))}
def create(name,refs,columns,notes,prompt):
 out=D/name;assert not out.exists();out.mkdir();rows=(len(refs)+columns-1)//columns
 native=Image.new('RGBA',(96*columns,96*rows));records=[]
 for i,n in enumerate(refs):
  a=displays[n];im=rgba(a,pal);outside=a.copy();outside[112:208,112:208]=0;assert not np.any(outside)
  native.paste(im.crop(crop),(i%columns*96,i//columns*96));Image.fromarray(a).save(out/f'b0_{n:03}_before_indices.png')
  b=bank['frames'][n]
  records.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[i%columns,i//columns],'bounds':im.getbbox(),'source_canvas_sha256':sha(a.tobytes()),'exact_display_expansion_refs':[k for k,z in displays.items()if np.array_equal(a,z)],'same_stream_refs':[f['index']for f in bank['frames']if f['offset']==b['offset']],'tile_count':b['tile_count'],'native_animation_uses':[{'id':q['id'],'label':labels.get(q['id']),'steps':[{'frame':s['frame'],'duration_signed':s['duration_signed'],'event_signed':s['event_signed'],'position':s['position']}for s in q['steps']]}for q in animations if q['graphics_bank']==0 and any(s['frame']==n for s in q['steps'])]})
 native.save(out/'native_input.png');native.resize((native.width*8,native.height*8),Image.Resampling.NEAREST).save(out/'input.png')
 for label,n in [('idle147',147),('refined_wall36',36),('refined_ladder190',190)]:rgba(displays[n],pal).crop(crop).resize((768,768),Image.Resampling.NEAREST).save(out/f'{label}.png')
 dump(out/'inputs.json',{'actual_input_arc':rel(P),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,96],'columns':columns,'rows':rows,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':records,'animation_evidence':rel(anim_path),'animation_evidence_sha256':sha(anim_path.read_bytes()),'label_evidence':rel(playback_path),'label_evidence_sha256':sha(playback_path.read_bytes()),'generated':False,'game_unchanged':True,'scope':notes})
 (out/'prompt.txt').write_text(prompt+'\n','utf8')
 return {'path':rel(out),'frames':refs,'expanded_refs':sorted({k for r in records for k in r['exact_display_expansion_refs']})}
common='''Use case: precise-object-edit. The character is Rin, a white bob-haired blue-and-white maid. Repaint only the first source sheet into finely clustered native pixel art, matching the approved following idle/style references. Keep each source pose and its exact cell position, head/eye center, shoulder, elbow, wrist, hand and glove contact, hips, knee bend, ankles and toes. Each pose is distinct; do not replace them with an idle pose. No overall stretching, shrinkage, broad blank colors, thick black border, smeared details, disconnected waist, pencil-thin legs or tiny face. Match idle upper-arm, waist, thigh and calf solidity relative to head while respecting foreshortening. Layer cool-gray hair strands, precise face shadow planes and cyan eye when visible, selective navy contours, cuff folds, apron straps and seam, pleated skirt edge and boot shading. Preserve each facial expression and viewpoint. No added long tool, unrelated accessory, environment or effects. Transparent background, empty margins, no text or grid. Input cells96x96 at8x nearest-neighbor, fixed origin. Visual detail refinement only, no motion redesign. '''
movement=create('movement_finish01',[37,45,193],3,'벽차기37·대시 전환45·사다리 꼭대기193. 서로 다른 실제 동작이며 193을 벽 모션으로 오기하지 않는다.',common+'''Exactly THREE sprites in ONE horizontal row. Left is airborne wall-kick follow-through with the original hand and bent/spread leg pose. Middle is the very low forward-leaning dash transition; keep its original eye-to-floor distance and separate hands/boots, do not stretch the torso. Right is the ladder-top recovery posture, preserve the different viewpoint and original foot contacts. The following references are style only; do not copy their body poses.''')
hurt=create('hurt_lowhp01',[135,139,149,152],2,'피격135/139와 저체력149/152의 새4몸체 입력. 파생 피격136..145는 기존 불꽃/CLUT를 별도 보존하며 새몸체에 맞춰야 한다.',common+'''Exactly FOUR sprites in a2x2 sheet. Upper-left and upper-right are different recoil/hurt body poses, not standing or attacking. Keep the original facial expressions, hand positions and recoil angle. Lower-left and lower-right are two low-health breathing poses: keep the same planted boot positions and natural bowed head/shoulder difference between them, no separate moving lower legs or elastic waist. Preserve the original solid leg thickness despite the crouch. No electric arcs, aura, white flashes, stars, blood or injuries in this sheet; effects are separate game layers and must not be drawn.''')
review={'candidate':rel(P),'candidate_sha256':sha(arc),'root_final_packed_review_approved':True,'evidence':'루트가 일반·레드00/01 네 장을 직접 열람하고 목/허리 연결·의상 상세 개선을 확인했다.36 장갑 약2px 차이를 기록하며 중간판 가능으로 판단했다.','user_accepted':False,'runtime_verified':False,'root_additional_native_plan':'rn_pending_v7c native 통과 메시지 수신. 별도 증거는 루트가 관리한다.'}
dump(D/'wall97_root_review.json',review)
out={'movement':movement,'hurt_lowhp':hurt,'generation_started':False,'source_frozen':True};dump(D/'next97_inputs.json',out)
print(json.dumps(out))
