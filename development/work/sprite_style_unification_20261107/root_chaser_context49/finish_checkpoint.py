from pathlib import Path
import hashlib,json,shutil
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1]
read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def artifact(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
protection=W/'protection_checkpoint56.json';j=read(protection)
for source,copy in [('work/ver_buki_riko/sprite_style_checkpoint13/cards/fourth_source_copy.mcr','work/ver_rin_nana/sprite_style_checkpoint49/cards/fourth.mcr'),('work/ver_rin_nana/sprite_style_checkpoint13/cards/rin_allboss.mcr','work/ver_rin_nana/sprite_style_checkpoint49/cards/rin.mcr')]:
    assert sha(ROOT/source)==sha(ROOT/copy)
    if not any(q['copy']==copy for q in j['test_cards']):j['test_cards'].append({'source':source,'copy':copy,'sha256':sha(ROOT/copy)})
protection.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
out=ROOT/'out/sprite_style_unification_20261107/chaser_context49'
for name in ('shibuki_current_context.png','nana_current_context.png','riko_current_context.png','rin_current_context.png','shibuki_hover_partial_masks.png','nana_hover_partial_masks.png'):shutil.copyfile(O/name,out/name)
shutil.copyfile(O/'rn43_lowhp_actual01/actual_six_vs_idle.png',out/'nana_lowhp_actual.png')
flash=read(O/'rn43_intro_flash03/evidence.json');low=read(O/'rn43_lowhp_actual01/evidence.json');later=read(O/'rn43_lowhp_actual02/evidence.json');assert [q['ref']for q in low['samples']]==list(range(120,126))
viewed=[O/'rn43_intro_flash03/capture01_page0.png',O/'rn43_intro_flash03/capture02_page256.png',O/'rn43_lowhp_actual01/ref120_page0.png',O/'rn43_lowhp_actual01/actual_six_vs_idle.png',O/'lowhp_display_probe.png']
summary={'checkpoint':49,'builds_unchanged':['BR31','RN43'],'sprite_pixels_changed':False,'new_confirmed_pixel_defects':[],
 'static_review':artifact(O/'visual_review.json'),'chaser_sequence':artifact(O/'sequence_report.json'),'browser_check':artifact(O/'browser_verification.json'),'hover_partials':artifact(O/'hover_partial_manifest.json'),'lowhp_condition':artifact(O/'lowhp_trigger_native.json'),
 'live_session':'work/ver_rin_nana/emulator_sessions/20261108T031908550454Z','bin_sha256':flash['bin_sha256'],'fresh_boot':True,'memory_writes':False,'F1_F3_sent':False,
 'flash140':{'scope':'Nana base only','samples':len(flash['samples']),'active_decode_matches':sum(q['active_decode_matches']for q in flash['samples']),'GPU_upload_matches':sum(q['gpu_upload_matches']for q in flash['samples']),'opaque_framebuffer_exact_pixels':649,'evidence':artifact(O/'rn43_intro_flash03/evidence.json'),'framebuffer_matches':artifact(O/'rn43_intro_flash03/flash_screen_match.json'),'fourth_added_armor_flash_runtime_verified':False},
 'lowhp':{'scope':'Nana base only','actual_animation':6,'actual_refs':[q['ref']for q in low['samples']],'whole_assets_decode_GPU_all_six_equal':True,'evidence':artifact(O/'rn43_lowhp_actual01/evidence.json'),'later_capture':artifact(O/'rn43_lowhp_actual02/evidence.json'),'framebuffer_comparison':artifact(O/'rn43_lowhp_actual01/screen_matches.json'),'full_opaque_framebuffer_matches':[122],'full_opaque_framebuffer_matched_pixels':554,'all_six_full_screen_match':False,'later_capture_safety_stop':later['stop_reason']},
 'actually_viewed_runtime_files':[artifact(p)for p in viewed],
 'observations':['기본형140의 흰 섬광을 실제로 보았고 최신 원화649불투명 픽셀이 프레임버퍼에 일치했다. 포스 추가149픽셀 표시를 확인한 증거로 확대하지 않는다.','일반 입력으로 적에게 피격된 뒤 자동 후퇴, 체력4에서 저체력6의120..125를 모두 관측했다. 최신 리소스 전체와 디코드/GPU 업로드가 일치한다.','저체력 모음에서 보이는 머리·얼굴·옷 경계의 추가 확정 결함은 발견하지 못했다. 일부 캡처에 전경 포대 가림이 있고, 업로드/그리기 시점 차이도 있어122 외5참조의 전체 불투명 화면 일치는 얻지 못했다.','후속 재포착은 체력0/128을 감지하고 즉시 입력을 중단했다. 첫 접근 때 수동 후퇴 전 사망한 것과 함께 실기 한계로 기록하며 성공 표본에 섞지 않는다.'],
 'session_closed':True,'protection':artifact(protection),'protected_files':80,'test_card_pairs':7,'overall_complete':False,
 'remaining':['도구 거부로 보존 중인 시부키Ultimate전후135 및 나나Ultimate전후 사다리7참조','체이서의 실제 움직임/가림 순서, 다른 의상 차량, 발파츠만 있는 호버의 실기','포스아머 추가 등장 섬광과 저체력5참조의 가림 없는 전체 화면 표본']}
assert read(ROOT/summary['live_session']/'close.local.json')['exited']
(O/'checkpoint49_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'static_review_files':10,'flash140_samples':4,'lowhp_actual_refs':6,'protected_files':80,'test_card_pairs':7,'session_closed':True,'whole_task_complete':False}))
