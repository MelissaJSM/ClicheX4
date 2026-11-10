from pathlib import Path
import hashlib, html, json

D = Path(__file__).parent
ROOT = D.parents[2]
O = D / 'shibuki_standing_fire8_independent01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
r = json.loads((O / 'report.json').read_text('utf8'))
assert sha(O / 'report.json') == 'dbd043d42eddbe6e944382c826576b6ecf24bc489a7b7a27c907882f684a7e20'
native = D / 'shibuki_standing_fire_directory_native01/report.json'
assert sha(native) == '185145c45dbdcfbea6ce89ee1f44dd036d9e986b9ea24cdddfd4b9e5d8c92204'
assert sha(ROOT / r['candidate']) == r['candidate_sha256']
notes = {
 'full_0.png': '85/86 양폼의 새 머릿결·소매·다리 명암을 확인했다. 수평 총열과 손의 연결에서 추가 확정 절단을 찾지 못했다.',
 'full_1.png': '87 복귀와 88 상향 자세를 보았다. 새 머리·의상 세부가 이어지고 88의 원래 큰 효과가 머리 위에 유지된다.',
 'full_2.png': '89/90의 들린 팔과 머리, 허리, 신발이 이어진다. 포스 상의·소매의 보라/금색과 기본 흰 소매가 구별된다.',
 'full_3.png': '91 수평으로 내민 팔 및 92 복귀 자세에서 새 소매·몸·머리 연결을 확인했다. 두 폼의 총열 위치와 발 배치에서 새 확정 단절을 찾지 못했다.',
 'partial_85.png': '머리/몸/팔/다리/몸+다리의 다섯 조합을 보았다. 장식과 의상 전환에 떠 있는 새 조각이나 손목 절단은 보이지 않았다.',
 'partial_86.png': '다섯 조합에서 반동 중 총열과 팔이 이어진다. 기본 소매와 포스 팔의 경계에 추가 확정 단절은 보이지 않았다.',
 'partial_87.png': '다섯 조합에서 내린 팔과 상체, 양 다리 연결을 보았다. 새 팔 외에 별도 손이 남는 모습은 보이지 않았다.',
 'partial_88.png': '다섯 조합에서 머리 위 원효과가 유지되고 소매/머리 전환에 새 잘림이 보이지 않았다. 효과의 실제 발생 시간 검증은 아니다.',
 'partial_89.png': '다섯 조합에서 위로 든 팔·귀·머리 장식과 상의 전환을 확인했다. 총과 귀를 구별할 수 있고 떠 있는 조각은 찾지 못했다.',
 'partial_90.png': '다섯 조합에서 기울어진 상체와 앞팔이 연결된다. 기본 소매와 포스 소매의 색 경계 외에 새 절단은 보이지 않았다.',
 'partial_91.png': '다섯 조합에서 수평 총열/손/커프가 이어진다. 팔 아머만 바뀌는 판에서도 기본 머리와 포스 팔의 접속이 유지된다.',
 'partial_92.png': '다섯 조합에서 복귀 팔과 허리, 굽힌 다리를 확인했다. body-only와 legs-only에서 새 부유 조각을 찾지 못했다.'
}
seen = []
for q in r['readback_sheets']:
    p = ROOT / q['path']
    assert sha(p) == q['sha256']
    seen.append({**q, 'actually_viewed': True, 'finding': notes[p.name]})
assert len(seen) == 12
v = {
 'candidate_sha256': r['candidate_sha256'],
 'technical_report_sha256': sha(O / 'report.json'),
 'native_report': {'path': str(native.relative_to(ROOT)).replace('\\', '/'), 'sha256': sha(native)},
 'scope': '시부키 기본/포스 85..92 독립 재추출 완성4판·부분8판 실제 정적 열람',
 'sheets': seen, 'new_confirmed_art_defect_found': False,
 'runtime_verified': False, 'user_accepted': False, 'overall_complete': False,
 'limits': [
  '새 14원화 셀의 생성/재양자화를 독립 반복하지 않았다. 등록35층과 88의 효과파생5층, 실제40층의 일치를 확인한 reader와 결합한다.',
  '기계검사 대상256부분 및 저장변경576부분 중 실제 육안은 기록한 12판이다. 원시간표 재생/실제 게임/전체 GPU 최종렌더는 이 시각보고의 범위가 아니다.',
  '508참조 원MIPS는 RAM완료 로더→scratchpad→directory→객체+38/+3c→decode/upload queue 경로다. Python 은행포인터 주입 검사가 아니며 새 부팅 실기와는 구분한다.',
  '기존18참조 저장변경은 원시바이트 불변이 아니라 9공유stream의 전체32타일/256nibble 역순열 보존이다.',
  '선택화면1..8 사본 동기화와 최종 사용자 수용은 별도 후속이다.'
 ]
}
(O / 'visual_review.json').write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', 'utf8')
page = ['<!doctype html><meta charset="utf-8"><title>시부키 85~92 독립 검사</title><style>body{font:16px sans-serif;background:#182333;color:#eee;margin:24px}img{max-width:100%}a{color:#9cddff}</style><h1>시부키 기본/포스 85~92 독립 검사</h1><p>후보4fe71736. 새40층·256부분, 기존18참조의 전체타일 역순열·576부분, 원로더508참조를 검증했습니다. 실제 게임과 선택화면 사본은 별도입니다.</p><p><a href="report.json">독립 기술 보고</a> · <a href="visual_review.json">실제 열람12판 기록</a> · <a href="../shibuki_standing_fire_directory_native01/report.json">원MIPS 로더/디렉터리508 보고</a></p>']
for q in seen:
    page.append(f'<p>{html.escape(q["finding"])}</p><img src="{Path(q["path"]).name}">')
(O / 'INDEX.html').write_text('\n'.join(page), 'utf8')
print(json.dumps({'technical': sha(O/'report.json'), 'visual': sha(O/'visual_review.json'), 'native': sha(native), 'sheets': len(seen)}))
