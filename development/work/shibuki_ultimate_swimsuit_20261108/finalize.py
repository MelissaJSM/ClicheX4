"""검증한 격리 출력만 활성화한다. 원본/출시본/다른 모드/저장 보호."""
from pathlib import Path
import sys,json,shutil,html
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'work/motion_fixes_20261108')]
from common import write
from src.psx_disc import file_hash
build=json.loads((H/'build.json').read_text('utf8'));out=ROOT/Path(build['cue']).parent;review=out/'review'
validation=json.loads((H/'validation.json').read_text('utf8'));pixels=json.loads((H/'pixel_matches.json').read_text('utf8'))
assert validation['passed'] and validation['idle_and_wrist_v3_exact'] and validation['palette_exact']
assert file_hash(ROOT/Path(build['cue']).with_suffix('.bin'))==build['sha256']
runtime=json.loads((H/'runtime_fire_hover/report.json').read_text('utf8'))
assert runtime['bin_sha256']==build['sha256'] and runtime['resident_entries_exact'] and runtime['engine_owned_armor']==15 and runtime['ultimate']==1
verified=sorted({r['frame'] for r in runtime['frames'] if r['verified'] and r['frame'] in validation['changed_refs']})
assert verified==[85,86,87,88,89,90,91,92,221,223,224,229,230]
assert pixels['garments_matched']==11 and pixels['tested_refs']==13
closed=json.loads((ROOT/runtime['session']/'close.local.json').read_text('utf8'));assert closed['exited']
p=ROOT/'projects/ver_buki_riko/current_build.json';project=ROOT/'projects/ver_buki_riko/project.json'
old=json.loads(p.read_text('utf8'));source=json.loads((H/'source.json').read_text('utf8'));assert old==source['pointer']
protected=json.loads((H/'protection_before.json').read_text('utf8'))['files'];authorized={p.relative_to(ROOT).as_posix(),project.relative_to(ROOT).as_posix()}
for name,r in protected.items():assert file_hash(ROOT/name)==r['sha256'],name
cards={}
for name,src in [('after','work/ver_rin_nana/sprite_style_checkpoint9/cards/nana_allboss.mcr'),('before','work/ver_rin_nana/sprite_style_checkpoint52/cards/preultimate.mcr')]:
 path=ROOT/f'work/ver_buki_riko/ultimate_wrist_20261108/cards/{name}.mcr';assert file_hash(path)==file_hash(ROOT/src);cards[name]=file_hash(path)
receipt=[]
for i in range(4):
 im=H/f'generated_{i}.png';edit=H/f'edit_{i}.png';prompt=H/f'prompt_{i}.txt'
 assert im.exists() and edit.exists() and prompt.exists()
 receipt.append({'page':i,'mode':'built_in_image_gen','task':'edit_existing_garment_reference','source':edit.relative_to(ROOT).as_posix(),'source_sha256':file_hash(edit),'reference':(H/'idle_reference.png').relative_to(ROOT).as_posix(),'prompt':prompt.relative_to(ROOT).as_posix(),'prompt_sha256':file_hash(prompt),'generated':im.relative_to(ROOT).as_posix(),'generated_sha256':file_hash(im),'generated_size':list(Image.open(im).size),'native_registration':'register.py + expand.py; existing palette; garment masks only; other generated parts discarded'})
write(H/'generation_receipt.json',{'mode':'built_in_image_gen','CLI_used':False,'pages':receipt})
for name in ['pixel_matches.json','pack.json','generation_receipt.json']:shutil.copyfile(H/name,review/name)
shutil.copyfile(H/'runtime_fire_hover/report.json',review/'runtime_report.json')
shutil.copyfile(H/'runtime_fire_hover/live.gif',review/'actual_gameplay.gif')
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>시부키 얼티밋 수영복 통일</title><style>body{background:#182231;color:#f0f2fa;font:17px/1.65 sans-serif;margin:30px;max-width:1600px}a{color:#aadeff}img{max-width:100%;height:auto;image-rendering:pixelated}.poses{display:flex;flex-wrap:wrap;gap:22px}.poses figure{margin:0}section{margin:38px 0}details{padding:12px;border:1px solid #66758c}pre{white-space:pre-wrap}</style><h1>시부키 얼티밋 획득 후 — 대기 기준 수영복 통일</h1><p>2026-11-08 · 기준은 대기 0의 흰색 몸판, 분홍 장식, 짧은 흰 프릴과 연보라 주름입니다. 관련 77자세를 보정했습니다. 기준 대기와 직전 대시 사격 손목 수정은 그대로 보존했습니다.</p><p><a href="../shibuki_riko.cue">최신 게임 CUE</a> · <a href="../../../../docs/SHIBUKI_ULTIMATE_SWIMSUIT_20261108.md">변경·검증 범위</a></p><section><h2>대기 기준</h2><img src="idle_reference.png" alt="기준 대기"></section><section><h2>실제 게임 화면</h2><p>새 CUE와 게임 내 카드로 부팅한 얼티밋 획득 후 상태입니다. 수정 대상 13자세의 디코드 RAM/VRAM 업로드 일치를 확인했고, 11자세는 화면의 의상 픽셀까지 완전히 일치했습니다. 8자세는 전신도 일치했습니다. 86·91은 RAM/VRAM 검증까지이며 의상 화면 완전 일치 표본을 얻지 못했습니다.</p><img src="actual_00.png"><img src="actual_01.png"><details><summary>실제 플레이 표본 GIF</summary><p>약80ms 표본이며 모든60Hz 프레임의 녹화는 아닙니다.</p><img src="actual_gameplay.gif"></details><p>특수무기 자동 전환은 성공하지 못해 실기 검증으로 계산하지 않았습니다. 아래 특수무기 자세는 최종 ARC 재추출과 이미지 비교 검사 결과입니다.</p></section><section><h2>자세 연결 비교</h2><p>모두180ms 고정 간격 합성 재생이며 원작 타이밍의 실기 녹화와 다릅니다.</p><div class="poses">'''
for name,title in [('fire','사격·차지 사격'),('special','특수무기'),('hover','호버링·이동·사격')]:page+=f'<figure><figcaption>{title}</figcaption><img src="{name}.gif"></figure>'
page+='</div></section><section><h2>재삽입 파일에서 읽어낸 수정 77자세</h2><p>숫자는 게임의 프레임 참조 번호입니다. 좌표·손·총·발은 의상 영역 밖에서 기존과 정확히 같습니다.</p>'
for i in range(4):page+=f'<img src="packed_{i:02}.png" alt="수정 자세 모음 {i+1}">'
page+='</section><details><summary>이미지 도구와 정확한 프롬프트</summary><p>내장 image_gen 편집을 사용했습니다. 생성 결과 중 의상 마스크 부분만 기존 팔레트로 등록했습니다. 원본 생성 시트를 그대로 게임에 넣지 않았습니다.</p>'
for i in range(4):page+=f'<h3>편집 시트 {i+1}</h3><pre>{html.escape((H/f"prompt_{i}.txt").read_text("utf8"))}</pre>'
page+='</details></html>';(review/'index.html').write_text(page,'utf8')
runtime_scope='얼티밋 획득 후 사격·차지샷·호버링 대표13자세 RAM/VRAM 일치, 11자세 의상 픽셀 일치(전신8). 특수무기 전환 미확인으로 특수무기 실기 미완료. 전체77자세 정적 재삽입 검사 통과.'
manifest=json.loads((out/'manifest.json').read_text('utf8'));manifest.update(runtime_verified=True,runtime_scope=runtime_scope,runtime_verified_refs=verified,runtime_pixel_matches=pixels['garments_matched'],runtime_full_sprite_matches=pixels['full_matched'],special_weapons_runtime_verified=False,exhaustive_runtime_verified=False,user_accepted=False,review='review/index.html');write(out/'manifest.json',manifest)
write(H/'current_build_before.json',old);meta=json.loads(project.read_text('utf8'));write(H/'project_before.json',meta)
new={**old,'task':'shibuki_ultimate_swimsuit','stage':'ULTIMATE_COSTUME_UNIFIED_APPLIED_REVIEW','build':out.relative_to(ROOT).as_posix(),'cue':build['cue'],'sha256':build['sha256'],'previous_pointer':(H/'current_build_before.json').relative_to(ROOT).as_posix(),'status_report':'docs/SHIBUKI_ULTIMATE_SWIMSUIT_20261108.md','ultimate_swimsuit_report':'docs/SHIBUKI_ULTIMATE_SWIMSUIT_20261108.md','ultimate_swimsuit_review':(review/'index.html').relative_to(ROOT).as_posix(),'current_session':None,'running_bin_sha256':None,'last_test_session':runtime['session'],'current_runtime_state':'新CUEの試験終了','runtime_verification_scope':runtime_scope,'next_action':'새 CUE와 게임 내 카드로 수영복 통일 결과 확인. 특수무기는 사용자 실기 확인이 남아 있다.','user_accepted':False}
new['current_runtime_state']='새 CUE·정상 카드로 얼티밋 획득 후 사격/호버링 확인 후 시험 창 종료.'
write(p,new);meta.update(active_task=new['task'],active_substage=new['stage'],latest_integrated_build=new['build'],latest_integrated_bin_sha256=new['sha256'],ultimate_swimsuit_report=new['ultimate_swimsuit_report']);write(project,meta)
updates=[{'path':name,'before':protected[name]['sha256'],'after':file_hash(ROOT/name)} for name in sorted(authorized)]
write(H/'application.json',{'new_build':build,'protected_files_unchanged':len(protected)-len(authorized),'authorized_metadata_updates':updates,'test_cards_unchanged':cards,'runtime_scope':runtime_scope,'runtime_verified_refs':verified,'nana_rin_pointer_and_bin_preserved':True,'original_and_final_release_preserved':True,'test_emulator_closed':True,'memory_written':False,'F1_F3_used':False})
print(json.dumps({'applied':build,'protected_unchanged':len(protected)-len(authorized),'changed_refs':len(validation['changed_refs']),'actual_garment_matches':pixels['garments_matched'],'review':str(review/'index.html')}))
