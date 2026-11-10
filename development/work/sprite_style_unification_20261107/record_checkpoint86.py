from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bind=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
D=W/'nana_audit/hurt_repaint/native_cycle_v1';v=json.loads((D/'verification.json').read_text('utf8'));m=json.loads((D/'manifest.json').read_text('utf8'))
assert v['passed'] and v['canvas_native_checks']==84 and m['native_table_bytes_exact']
pages=[D/f'timeline_{i}.png' for i in range(33,38)]
r={'root_actually_viewed':[bind(p) for p in pages],'native_sequence_manifest':bind(D/'manifest.json'),'browser_canvas_checks':bind(D/'verification.json'),
 'findings':['원래33~37 피격 순서에 배열한 기본·포스 비교5판을 직접 열람했다. 몸체/섬광/독립 번개를 원참조 순서대로 대조했고235/236의 몸체 기준점이 교대로 흔들리는 정적 불일치는 찾지 못했다.',
 '원래 지속시간과 상대 스텝이 보존된 재생/정지·84캔버스 픽셀 검사는 별도 자동 근거에 연결한다.'],
 'limits':['직접 열람은 시간표 비교판5장이다. 이 기록만으로 실제 피격/모든 실시간 전환을 눈으로 검증했다고 하지 않는다.',
 '특수 피격의 실제 활성 팔레트와 원래 조건은 후속 새 부팅 관측에서 구분한다.'],
 'final_user_accepted':False}
p=W/'root_review_checkpoint86.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
