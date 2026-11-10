"""실제 열람한 독립 재추출2판의 정적 미술 범위를 별도 기록."""
from pathlib import Path
import json, hashlib
D = Path(__file__).parent
O = D / 'nana_ultimate_victory4_independent01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
r = json.loads((O / 'report.json').read_text('utf8'))
data = {
    'candidate_sha256': r['candidate_sha256'],
    'independent_report_sha256': sha(O / 'report.json'),
    'actually_viewed': r['readback_sheets'],
    'viewed_scope': '독립 reader가 실제 ARC에서 새로 추출한 2판. 204..207×구/신×전/후 16표시.',
    'observations': [
        '204 가슴 앞 빈손과 205 이마 경례 자세가 유지되고 새 머릿결·재킷/맨팔·다리 명암의 분리가 더 선명하다.',
        '206 얼굴 옆 권총과 207 머리 위 권총은 새 손과 이어져 보이며 이 두 판에서 새로 뜬 총이나 손목 절단을 찾지 못했다.',
        '후폼의 맨팔과 재킷 폼 소매를 구분할 수 있고 새 머리/몸통/허벅지 연결에 추가 확정 절단을 찾지 못했다.',
        '207 위로 든 팔과 총은 206의 접은 팔과 의도적으로 다른 자세다. 같은 형상으로 오인하지 않았다.'
    ],
    'new_confirmed_visual_defects': [],
    'producer_source_requantization_performed_here': False,
    'original_sequence_browser_replay_performed_here': False,
    'native_MIPS_performed_here': False,
    'runtime_verified_here': False,
    'user_accepted': False,
    'limitations': ['정적 두 판의 실제 열람이며 원시간표 루프와 전투/승리 실기 판정은 별도다.',
                    '새아트 전체의 사용자 수용 또는 캐릭터 전체 완료를 뜻하지 않는다.']
}
(O / 'visual_review.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', 'utf8')
print(sha(O / 'visual_review.json'))
