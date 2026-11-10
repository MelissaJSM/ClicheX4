from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[W/'nana_audit/ultimate_ceremony_repaint/canonical_cases_probe_v2'/f'comparison_{i}.png' for i in range(1,4)]+[W/'shibuki_audit/ultimate_hurt_common_probe02'/f'{form}_comparison_{i:02}.png' for form in ('before','after') for i in (0,1)]
p=W/'root_review_checkpoint106.json';assert not p.exists()
p.write_text(json.dumps({'root_actually_viewed':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)} for q in paths],
 'findings':['나나 Ultimate 등장133/135/136/137/138의 정본8px권총 후보3판을 직접 봤다. 아래→가슴→턱→머리위로 올라가는 무기 흐름은 더 분명해졌다. 다만138은136/137보다 종아리·옆구리 윤곽이 성겨 보이므로 실제 대기와의 부위 폭/윤곽 분석을 요청했고 미술 확정에서 제외했다.',
 '시부키 Ultimate 피격106/110/233/234 양의상 공통층4판을 직접 봤다. 새 머릿결·금색 안경·의상 경계가 대기와 가까워졌으며 옛 넓고 뭉개진 손/팔을 개선했다. 새234 앞팔이 얼굴을 가로지르던 문제도 수정된 후보를 확인했다.'],
 'limits':['최종 네이티브 패킹·효과·연속 원순서·실기·사용자 수용은 아직 별도다.','시부키110 샌들 접지1px와 나나138 체형 판단은 추가 검토 대상으로 남긴다.'],
 'candidate_only':True,'final_user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(p.name,sha(p))
