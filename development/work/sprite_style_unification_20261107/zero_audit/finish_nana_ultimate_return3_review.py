from pathlib import Path
import hashlib, json

D = Path(__file__).parent
O = D / 'nana_ultimate_return3_independent01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
r = json.loads((O / 'report.json').read_text('utf8'))
assert sha(O / 'report.json') == 'e13407379ca22f52efe8630a138f958aaccbc93ae85a9754ec41577c525cdff3'
review = {
    'candidate_sha256': r['candidate_sha256'],
    'independent_report_sha256': sha(O / 'report.json'),
    'actually_viewed': [{'file': f'readback_{n}.png', 'sha256': sha(O / f'readback_{n}.png')} for n in (156,157,158)],
    'observations': [
        '최종 ARC에서 별도로 재추출한 156/157/158 세 판을 직접 열람했다. 각 판은 구/신 재킷과 구/신 획득 후 의상을 나란히 표시한다.',
        '156의 새 머릿결·뒤쪽 머리·재킷 명암과 후폼의 검정/분홍 하의가 구분된다. 잘못된 흰 반바지 잔재나 새 팔·다리의 확정 단절을 찾지 못했다.',
        '157의 분홍/크림색 테두리는 새 머리·다리 윤곽을 따라가며 몸 안의 상세가 유지된다. 옛 몸의 외곽이 따로 남는 확정 결함을 찾지 못했다.',
        '158의 원래 원형 빛과 기둥이 위로 이동한 새 몸체와 함께 표시된다. 몸 밖의 효과 형상과 새 몸의 세부가 유지되며 새 확정 분리를 찾지 못했다.'
    ],
    'new_confirmed_visual_defects': [],
    'new_runtime_or_native_execution': False,
    'user_accepted': False,
    'limits': [
        '원표 연속판은 이 열람 기록에 포함하지 않는다. 루트의 원표 직접 열람 및 제작자의 재생 검사는 별도 근거다.',
        '실제 게임 귀환 장면의 검증이나 전체 미술 완료를 주장하지 않는다.'
    ]
}
(O / 'visual_review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'report': sha(O / 'report.json'), 'visual': sha(O / 'visual_review.json')}))
