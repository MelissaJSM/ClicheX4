import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
fresh = json.loads((OUT/'freshness.json').read_text('utf-8'))
viewed = json.loads((OUT/'viewed_sheets.json').read_text('utf-8'))
paths = viewed['files']
assert len(paths) == len(set(paths)) == 132
expected = {str((OUT/c/b['path']).relative_to(ROOT)).replace('\\','/') for c in fresh for b in fresh[c]['sheets']}
assert len(expected) == 130 and expected.issubset(paths)
for p in paths:
    assert (ROOT/p).is_file(), p

report = {
  'task': '최신 리코·린 일반/블랙 전신 스프라이트 미술 재점검',
  'date': '2026-11-06',
  'status': '정지 시트 육안 검토 완료; 전수 실기 검증 아님',
  'viewer': viewed['viewer'], 'detail': viewed['detail'],
  'sources': {c: {'bin': x['source_bin'], 'sha256': x['source_sha256'], 'current_rgba_checks': x['current_RGBA_checks'], 'revised_png_references': x['revised_PNG_references'], 'selection_references': x['UI_selection_references_checked'], 'save_references': x['UI_save_references_checked']} for c,x in fresh.items()},
  'visual_review': {'motion_sheets':124, 'UI_sheets':6, 'targeted_sheets':2, 'actually_viewed_total':132, 'idle_reference':'b0_147', 'motion_scale':2, 'ui_scale':3, 'targeted_scale':5, 'nearest_neighbor':True, 'per_pose_rescale':False, 'new_runtime_checks':False},
  'confirmed_new_defects': [],
  'optional_candidates': [
    {'character':'riko','refs':['b1_003','b1_004','b1_005','b1_006'],'finding':'측면 승리/귀환 종아리와 부츠가 정면 대기보다 가늘게 보임','status':'미술 취향 후보; 시점 차이와 분리되지 않아 결함 미확정','recommendation':'현재 보존; 실기 전환에서 불만족이 확인될 경우에만 소량 조정','evidence':'riko/targeted_5x.png'},
    {'character':'riko','refs':['b0_164','b0_166','b0_168','b0_170','b0_172','b0_174..189','b1_148','b1_150','b1_152','b1_154'],'finding':'후면 머리의 녹색 명암 면이 정면보다 단순함','status':'뒤통수 시점과 일치; 뭉개짐 확정 아님','recommendation':'현재 보존; 추가한다면 유사 후면군을 함께 비교','evidence':'riko/targeted_5x.png'}
  ],
  'rin_new_candidates': [],
  'unreconstructed': {c:x['unreconstructed'] for c,x in fresh.items()},
  'limitations': [
    'b1_042..049는 이전 VRAM에 의존하여 완성된 몸체의 육안 검토 대상에서 제외했다.',
    'CLUT2 및 정적 특수효과는 역사 미리보기 팔레트가 포함되므로 현재 실기 효과색을 증명하지 않는다.',
    '연속 재생, 실제 배경, 차량, 무기 객체, 반투명 합성, GPU 좌우 경계는 이번 새 실기 검증 범위가 아니다.',
    'UI는 선택 41참조와 저장 2참조/캐릭터만이며 HUD·잔기·대형 일러스트는 미열람이다.',
    '설정화/원작 제로 전체와의 새로운 병렬 비교가 아니라 현재 수용 대기 도트를 기준으로 했다.'
  ],
  'changes': 'work/sprite_reaudit_20261106/zero 아래 비교시트·감사 자료만 작성. 게임/BIN/원화/공유코드/포인터/저장자료 불변.',
  'viewed_files': [{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in paths],
  'report_markdown':'work/sprite_reaudit_20261106/zero/REPORT.md'
}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
for name in ('report.json','REPORT.md','freshness.json'):
    value = (OUT/name).read_text('utf-8')
    assert '\ufffd' not in value
print(json.dumps({'actually_viewed':len(paths),'confirmed_new_defects':0,'report_sha256':hashlib.sha256((OUT/'report.json').read_bytes()).hexdigest()}))
