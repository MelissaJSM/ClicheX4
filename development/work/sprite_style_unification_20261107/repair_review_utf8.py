"""Repair only unbound review prose affected by a PowerShell pipe encoding."""
from pathlib import Path
import json, hashlib
W = Path(__file__).resolve().parent; ROOT = W.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text('utf8'))
def save(path, obj):
    body = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    if path.read_text('utf8') != body:
        backup = path.with_name(path.stem + '_before_utf8_fix.json')
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
        path.write_text(body, 'utf8')

p = W / 'root_review_checkpoint49.json'; r = read(p)
r['findings'] = ['최종 일반/레드6판 모두 직접 열람. 새 머리와 의상 세부 및 회복 연결은 개선 방향이나, 준비178..181의 부츠가 회색으로 바뀌어 대기147·직전177·회복186..189의 흰 부츠와 파란/붉은 신발 식별색과 불일치한다.']
r['decision'] = '동결/통합 보류. 원화 또는 색 등록 원인을 추적하여 새 세부를 유지한 국소 수정 뒤 다시 검토한다.'
save(p, r)
p = W / 'root_review_checkpoint52.json'; r = read(p)
r['findings'] = ['일반/레드 재추출6판과 원순서10판을 모두 직접 열람했다. 새 머리/의상/부츠 세부를 유지하면서178..181 신발의 파란색/붉은색 식별색을 회복한 방향을 수용한다.',
                 '177→178..181→기존182..185→186..189의 원순서에서 손과 구체의 연결, 치마와 다리의 연결을 검토했다. 추가 확정 단절은 찾지 못했다.']
r['decision'] = 'v2 미술 검토 통과. 독립/원코드 검사와 결합 후 별도 시험판 통합 가능.'
r['limits'] = ['원순서 정적 미술판 검토이며 새 낙봉파 실제 게임 재생과 별도다.',
               '기존626a 회색 신발 후보의 미수용 기록49는 보존한다.']
save(p, r)
# The UI candidate has already been bound to v14. Do not alter that frozen
# record or its proofs. Supply a corrected explanatory supplement instead.
p = W / 'selection_shibuki_beam13/utf8_note_correction.json'
note = {'supersedes_field': 'guard_checks_v2.json:prior_record_offset_difference',
        'correct_text': '원 부모5300..5348→v13/후보4704..4752. 이전에 검증한 X 전신 재패킹으로 생긴 위치 차이다. 이번 빛기둥 수정은 v13 레코드 위치를 모두 보존한다.',
        'cause': 'PowerShell 표준입력 인코딩으로 설명 문자열이 손상됨. 실제 숫자/검사/ARC/결속된 FROZEN은 그대로 보존한다.'}
if not p.exists():
    p.write_text(json.dumps(note, ensure_ascii=False, indent=2) + '\n', 'utf8')
for i in (49, 52):
    p = W / f'root_review_checkpoint{i}.json'
    assert '????' not in p.read_text('utf8')
    print(json.dumps({'record': i, 'sha256': sha(p)}))
