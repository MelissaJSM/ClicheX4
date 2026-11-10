"""Prepare source-complete fixed-origin keys, without producing or changing art."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';P=D/'prepared_victory_details_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='1a4e16a126b551e5f9d291401a5b9249e66c84aa0252b929b2fd31fa541b143e'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,208)
O=D/'wall_followup01';assert not O.exists();O.mkdir();native=Image.new('RGBA',(192,192));rows=[]
for i,n in enumerate((34,36,38,41)):
 a,m=render(arc,0,0,n);v=rgba(a,pal);outside=a.copy();outside[crop[1]:crop[3],crop[0]:crop[2]]=0;assert not np.any(outside)
 native.paste(v.crop(crop),(i%2*96,i//2*96));Image.fromarray(a).save(O/f'b0_{n:03}_before_indices.png')
 rows.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[i%2,i//2],'bounds':v.getbbox(),'source_canvas_sha256':sha(a.tobytes()),'exact_display_expansion_refs':[41,42,43]if n==41 else[n]})
native.save(O/'native_input.png');native.resize((1536,1536),Image.Resampling.NEAREST).save(O/'input.png')
for name,n in [('idle147',147),('refined_wall39',39),('refined_air35',35)]:rgba(render(arc,0,0,n)[0],pal).crop(crop).resize((768,768),Image.Resampling.NEAREST).save(O/f'{name}.png')
meta={'actual_input_arc':str(P.relative_to(ROOT)),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,96],'columns':2,'rows':2,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':rows,'game_unchanged':True,'generated':False,'scope':'새35/39 사이에 남은 구형34/36/38/41의 머릿결·커프·가슴/치마/부츠만 같은 대기 품질로 재작화.41과42/43은 실제 전체 표시가 같다.'}
(O/'inputs.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit. Repaint only the FIRST image: four distinct Rin action sprites, a white bob-haired blue-and-white maid, in the exact 2-column 2-row transparent sheet. The following three images show approved idle and newly detailed wall/air poses; match their fine native pixel-art rendering and body proportions, not their motion. Keep each first-image sprite's precise original position within its96x96cell, eye/head center, neckline, shoulder/elbow/wrist/hand anchors, knee bend, ankles, toe positions and ribbon-tail path. These are four different movements: upper-left airborne legs spread and fists forward; upper-right raised front fist near the forehead and separate spread legs; lower-left tightly bent/crossed knees with wall-facing hand near the face and other hand raised behind; lower-right tilted body with rear hand high and forward hand extended, one lower leg dropped. Preserve these distinctions and the viewpoint; no swapping limbs or using one body four times. Keep the existing short glove/tool connection only, no new long weapon. The lower two sprites are tilted, do not stretch them to upright idle height. Restore layered cool-gray hair strands and facial shadow planes, precise cyan iris, thin selective navy contours, clear cuff folds, fitted chest/apron straps, skirt pleats/hem and coherent stocking/boot shading. Keep the approved idle's solid but slender head, upper arms, waist, thighs and calves: no shrunken face, pencil-thin neck, tubular long limb, swollen gloves or thick black contour. Add native cluster detail, not blurry brushwork, checker noise, random dark dots, or flat blank colored masses. No old pose may be replaced by the idle pose. Crisp late-1990s action-game pixels. Exactly four sprites and all empty margins preserved, no text, frames, grid, shadows, background, water, walls or effects. Transparent background. Input logical192x192 at8x nearest-neighbor; preserve its per-cell geometry and foot/hand coordinates. Only visual refinement, no motion redesign.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8')
review=D/'priority_after91';mp=review/'manifest.json';j=json.loads(mp.read_text('utf8'));seen=[]
for group in('movement_wall','hurt_lowhp'):
 for form in('normal','black'):
  for q in sorted(review.glob(f'{group}_{form}_*.png')):seen.append({'path':str(q.relative_to(ROOT)),'sha256':sha(q.read_bytes()),'actually_viewed':True})
assert len(seen)==10
j.update(art_review_pending=False,actually_viewed_sheets=seen,observations=['34/36/37의 머리 안쪽이 큰 흰 면이고 커프·가슴이 새35보다 단순하다. 접힌 다리 자체의 낮은 높이는 크기 오류로 보지 않는다.','38은 얼굴 근처의 손과 커프가 뭉쳐 읽히고41~43은 새39~40보다 머리·가슴·치맛단이 평면적이다.41~43은 실제 인덱스 화면 전체가 같으므로 같은 새41로 연결할 수 있다.','45는 낮게 숙인 자세지만 눈·턱·소매가 덜 분리된다.193은 다른 관점의 연결 자세이므로 후면 원화나 대기 얼굴을 임의 복사하지 않는다.','135/139는 별도 피격 자세이며 가슴/허리와 부츠가 평면적이다.136~145의 전기·외곽·탈색은 새몸체 파생과 기존 효과 보호를 분리해야 한다.이 시트의 보조CLUT는 저장 팔레트 미리보기이며 게임에서 검은 전기가 표시된다는 증거가 아니다.','149~151과152~154는 각각 전체 표시가 같은 저체력/웅크림 묶음이다. 얼굴과 소매,치맛단의 단순화를 새로운 자세2개로 보완하고 원래 자세를 대기 높이로 늘리지 않는다.','146은 기존 대기 변형이며 이번 무수정 장부의 pending 표시만으로 결함이라고 판정하지 않는다. 기준 대기147과 같은 수준의 미술은 보존한다.'],next_authored_page=str(O.relative_to(ROOT)),next_keys=[34,36,38,41],next_exact_expansion=[41,42,43],following_distinct_movement_keys=[37,45,193],following_hurt_lowhp_keys=[135,139,149,152],runtime_verified=False)
mp.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
(review/'REPORT.md').write_text('''# 린91 이후 벽·피격 후속 검토

현재 Rin91에서 벽/이동13참조와 피격·저체력23참조를 일반·레드 각각5장, 합계10장으로 다시 추출하여 실제 열람했다. 기존 전수장부의 남은 모든 항목을 완료로 판정하지 않았다.

우선 새35/39와 바로 이어지는 **34/36/38/41**의 머릿결·얼굴·커프·상의가 단순한 차이를 줄인다. 입력은 `../wall_followup01/`이고, 고정384원점(160,160)에서96×96셀 네 개를 그대로 확대했다.41/42/43은 실제 전체 화면이 완전히 같아 새41을 동일하게 연결할 수 있다.37/45/193은 서로 다른 원화가 필요하여 다음 페이지로 남겼다.

그 다음은 피격135/139와 웅크림149/152이다.149~151 및152~154는 각각 표시가 같지만135/139의 전기·섬광 짝은 별도 파생자원이다. 새 몸체와 효과를 동시에 동기화해야 한다. 보조CLUT 시트의 검정은 저장 팔레트 미리보기 한계이므로 실제 게임의 검정 효과 결함으로 해석하지 않았다.

모든 원화 입력은 이미 제작한 린 비트맵이며 원본게임 그림을 생성 도구로 보내지 않는다. 이 단계는 입력과 미술 검토만이며 새그림 생성·작업ARC 변경·게임 실기는 아직 없다. 실제 열람한 파일 해시는 `manifest.json`에 기록했다.
''','utf8')
print(json.dumps({'input':str(O),'reviewed_sheets':len(seen),'new_keys':4,'mapped_refs':6}))
