"""Bind BR15 base/Fourth actual play, full-width reviews and protection."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bind=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
proof=read(W/'protection_checkpoint27.json');assert proof['passed'] and proof['protected_files']==80
cards=read(ROOT/'work/ver_rin_nana/sprite_style_checkpoint16/cards/copies.json')
for c in cards:assert sha(ROOT/c['source'])==sha(ROOT/c['copy'])==c['sha256']
all_pages=[];runs=[]
for name,frames,page_count,suffix in [('shibuki_base_run15',288,16,'_full_review'),('shibuki_fourth_run15',287,16,'_full_review'),('shibuki_fourth_aux15',192,4,'_review')]:
 watch=read(R/(name+'_watch')/'evidence.json');record=read(R/(name+'_play')/'evidence.json')
 review=read(R/(name+suffix)/'manifest.json');pages=review['pages']
 assert record['frames']==frames and not record['error'] and record['keys_released'] and not record['memory_written'] and not record['save_keys_sent']
 assert watch['character']==0 and watch['ultimate_or_black']==0 and watch['weapon']==0
 assert all(watch['resident_assets_still_exact']['PL00_U.ARC'].values())
 new_refs=list(range(1,33)) if 'run15' in name else []
 assert all([0,n] in watch['verified_bank_frames'] for n in new_refs)
 assert len(pages)==page_count
 for p in pages:assert sha(ROOT/p['path'])==p['sha256']
 session=ROOT/record['session'];assert read(session/'close.local.json')['exited']
 runs.append({'name':name,'actual_captures':frames,'encoded_webp_frames':review['encoded_webp_frames'],
  'session':record['session'],'close':bind(session/'close.local.json'),'fresh_boot':True,
  'new_references_verified':new_refs,'verified_bank_frames':watch['verified_bank_frames'],
  'unverified_events':[watch['events'][i] for i in watch['unverified_events']],
  'watch':bind(R/(name+'_watch')/'evidence.json'),'record':bind(R/(name+'_play')/'evidence.json'),
  'review':bind(R/(name+suffix)/'manifest.json'),'root_actually_viewed':pages})
 all_pages.extend(pages)
findings=['基本/포스의 대기→양방향 이동·이동 사격→대기 및 대시 연결32판을 직접 검토했다. 새 머리결·소매·옷깃의 묘사가 유지되며 추가 확정 파츠 분리·축소·윤곽 손실은 찾지 못했다.'.replace('基本','기본'),
 '새로 바뀐1..32 참조 모두 각각의 기본/포스 실제 RAM·GPU 일치 표본을 확보했다. 원래 효과 자원 배치의 후속검사로 포스 차지샷 양방향192창/4판을 보았으며 발사 효과가 표시되고 복귀하는 것을 확인했다.']
limits=['기본29/16/74 사건3개와 포스9 사건1개는 비동기 단발 읽기에서 일치가 입증되지 않았다. 다른 사건의 같은 참조 성공으로 이 순간까지 성공이라고 덮지 않는다.',
 '약16fps 창 기록이며 전체60Hz 전환·모든 부분 아머 조합/모든 무기효과/캡슐 동시 버퍼 수명의 전수실기를 뜻하지 않는다.',
 '포스 차지샷 후속은 화면과 몸체 상주 검사다. 별도 이펙트 객체 각각의 GPU 업로드 전수 추적은 원코드 격리 검사와 구분한다.',
 '첫 기본 DATA1 불러오기 시 포인터 내용 검사가 거부되어 확인 키를 보내지 않았다. 안정된 동일 슬롯의48HP/파츠0 레코드를 다시 읽고 별도 재개 도구로 정상 로드했다. 최초 거부 표본의 원인은 미확정이다.',
 '포스 첫 부팅 FMV의 프레임버퍼 규격 검사가 거부되었고 원래 Start로 넘긴 뒤 새로 탐색했다. 첫 잘린 검토 크롭은 전체 가로폭 판으로 대체했다.',
 '전체 캐릭터 미술 통일은 계속 진행 중이며 사용자 최종수용은 아니다.']
report={'project':'ver_buki_riko','test_build':'sprite_style_unification_20261107_v15',
 'disc_sha256':'dfd1b9d09e8fad846aebfd51a89aecc46bff98bc6281619bb21abf1c8dbf27fc',
 'asset_sha256':'381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce',
 'runs':runs,'root_visual_findings':findings,'limits':limits,
 'disc_and_native_checks':[bind(ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v15/manifest.json'),bind(W/'staging_br_v15_native_checks.json'),bind(W/'zero_audit/shibuki_run32_directory_native01/report.json'),bind(W/'zero_audit/shibuki_run32_independent01/report.json')],
 'album':bind(ROOT/'out/sprite_style_unification_20261107/review_v18/manifest.json'),
 'browser_checks':bind(ROOT/'out/sprite_style_unification_20261107/review_v18/browser_checks.json'),
 'protection':bind(W/'protection_checkpoint27.json'),'additional_test_cards_unchanged':cards,
 'f1_f3_used':False,'process_memory_written':False,'active_build_pointers_changed':False,'all_character_runtime_complete':False,'final_user_accepted':False}
p=R/'shibuki_run15_summary.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
r={'root_actually_viewed':all_pages,'runtime_summary':bind(p),'findings':findings,'limits':limits,'final_user_accepted':False}
q=W/'root_review_checkpoint82.json';assert not q.exists();q.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'summary_sha256':sha(p),'root82_sha256':sha(q),'actual_captures':sum(x['actual_captures'] for x in runs),'root_reviewed_pages':len(all_pages)}))
