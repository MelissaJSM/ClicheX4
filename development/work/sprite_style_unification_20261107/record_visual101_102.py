from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
def bind(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,d):
    assert not p.exists(),p
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8');print(p.name,sha(p))
m=read(R/'nana_ultimate_hurt19_approach02_hurt_review/manifest.json')
e=read(R/'nana_ultimate_hurt19_approach02_watch/evidence.json')
assert e['disc_sha256']=='383cd66528a25abf1bef08b4791824d52d3ae676b8e09af567fcae36447cea7c'
assert not e['unverified_events'] and e['observed_uploads_verified']
assert all([0,n] in e['verified_bank_frames'] for n in range(233,237))
write(W/'root_review_checkpoint101.json',{
 'root_actually_viewed':[bind(Path(p['path'])) for p in m['pages']],
 'findings':['나나 Ultimate 피격 실제 화면12판을 직접 열람했다. 첫8판은 직전 작업 구간, 마지막4판은 재개 후 확인했다.',
 '포스 획득 후 몸체233..236의 피격/효과 전환에서 추가 확정 몸체 분리·갑작스러운 축소·오라 절단을 찾지 못했다. 일부 화면의 적/폭발 가림은 몸체 누락으로 판정하지 않았다.'],
 'limits':['16fps 실제 창 기록으로 60Hz 전 프레임·모든 방향·모든 피해원을 증명하지 않는다. 캡슐 전 재킷 및106..114는 이 실기에 포함되지 않았다.','초기 approach 기록은 일시정지 메뉴였으므로 피격 검증에서 제외한다.'],
 'final_user_accepted':False})
write(R/'nana_ultimate_hurt19_summary.json',{
 'project':'ver_rin_nana','test_build':'sprite_style_unification_20261107_v19','disc_sha256':e['disc_sha256'],
 'asset_sha256':e['resident_assets'][0]['archive_sha256'],'session':e['session'],
 'actual_captures':m['captures'],'encoded_webp_frames':m['encoded_webp_frames'],'root_viewed_boards':len(m['pages']),
 'verified_new_references':list(range(233,237)),'verified_bank_frames':e['verified_bank_frames'],'unknown_events':e['unverified_events'],
 'resident_assets_still_exact':e['resident_assets_still_exact'],
 'observer':bind(R/'nana_ultimate_hurt19_approach02_watch/evidence.json'),'actual_review':bind(R/'nana_ultimate_hurt19_approach02_hurt_review/manifest.json'),
 'root_review':bind(W/'root_review_checkpoint101.json'),
 'excluded_run':{'orchestration':bind(R/'nana_ultimate_hurt19_approach_orchestration.json'),'reason':'화면 전환을 잘못 판단하여Start로 일시정지 메뉴를 열었다. 그 상태의160기록은 피격 성공 근거에서 제외한다. 메뉴를 닫고 실제 플레이 화면을 직접 확인한 뒤 approach02를 실행했다.'},
 'close':bind(ROOT/e['session']/'close.local.json'),'protection':bind(W/'protection_checkpoint30.json'),
 'limitations':['실기 범위는 캡슐 후233..236. 새 피격13 전체의 정적/원MIPS 검증과 구분한다.','일반 적과 폭발을 관찰했지만 개별 피해 객체를 계측하지 않았다.','60Hz 전수·양방향·캡슐 전·모든 피해원 전수 실기 아님.'],
 'active_pointer_changed':False,'f1_f3_used':False,'memory_written':False,'final_user_accepted':False})
paths=[W/'root_nana_ladder'/f'registered_page{page:02}'/f'comparison_{n}.png' for page in(3,4) for n in(1,2)]
paths += [W/'root_nana_ladder'/f'contact_registration{v:02}'/f'comparison_{n}.png' for v in(1,2) for n in range(1,5)]
write(W/'root_review_checkpoint102.json',{
 'root_actually_viewed':[bind(p) for p in paths],
 'findings':['새151/153/154/183의 기본/포스 원화와 국소 접점 보정판을 직접 검토했다. 새 그림의 머릿결·의상 주름·얼굴 묘사를 보존하며 발끝 등록차를 줄였다.',
 'contact01의144/149 손 이동은 얇은 손목 공백을 만들므로 제외한다. contact02는 해당 이동을 취소하고 새 팔의 연결을 유지한다. 8방향 연결 성분 수만으로 관절 품질을 합격시키지 않았다.',
 'contact02의4비교판을 재개 후 모두 직접 열람했다. 추가 확정 팔/발 분리를 찾지 못했다. 기본 부츠와 포스 맨다리의 공통 외곽은 다음 정합 대상이다.'],
 'limits':['새 원화와 국소 등록 단계이며 부분아머·사격150/155·원포맷 패킹·실기는 아직 미완료.','올린 손의 일부1픽셀 위치차는 보존된 새 원화 연결을 위해 남겼다. 모든 접점 exact라고 주장하지 않는다.'],
 'final_user_accepted':False})
