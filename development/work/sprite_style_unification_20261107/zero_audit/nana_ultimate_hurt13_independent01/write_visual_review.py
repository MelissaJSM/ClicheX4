from pathlib import Path
import hashlib
import json

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
report = json.loads((OUT / 'report.json').read_text('utf8'))
paths = [OUT / f'readback_{i:02}.png' for i in range(5)]
review = {
    'scope': '독립 reader가 실제 후보에서 재추출한 피격13참조의 전후 의상 비교5판을 view_image로 열람했다. 기술 report는 변경하지 않고 실제 열람을 이 기록으로 연결한다.',
    'candidate_sha256': report['candidate_sha256'],
    'independent_report_sha256': sha(OUT / 'report.json'),
    'viewed': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in paths],
    'observations': [
        '106/110/233/234의 새 머리 명암, 재킷 지퍼와 소매, 맨팔 및 다리의 세부가 구분된다. 이 정지판에서 새로 확인되는 파츠 절단은 찾지 못했다.',
        '107/108의 원래 붉은 효과가 새 양폼 몸체와 함께 보인다. 109의 흰 실루엣은 각 새 몸체의 외곽에 맞는다.',
        '111~114의 CLUT2 효과와 공통 섬광은 의도한 별도 표시로 구분했다. 이를 일반 의상 색이 잘못된 것으로 판정하지 않았다.',
        '235/236의 오라는 새 몸체 바깥에 놓여 있고, 236 귀 위의 흰 조각은 별도 불꽃으로 읽힌다. 기존 맨팔 폼에 남던 구형 재킷 같은 몸체 차이는 새 맨팔로 이어진다.'
    ],
    'new_confirmed_art_defects': [],
    'limitations': [
        '원표 연속 재생, 실제 게임, 실시간 효과 겹침은 이 미술 열람에 포함하지 않았다.',
        '235/236은 현재 재킷 몸 바깥에서 확인한 66/135픽셀만 오라 출처로 삼았다. 숨은 원효과의 복원이나 기존 맨팔 추가 10/11픽셀의 효과 보존을 주장하지 않는다.',
        '원화 생성 및 재양자화 재현은 제작자의 별도 증거이며, 이 독립 reader와 실제 열람의 범위에 포함하지 않았다.'
    ],
    'user_final_accepted': False,
    'runtime_verified': False
}
(OUT / 'visual_review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(sha(OUT / 'visual_review.json'))
