from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/base_settle_repaint';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[D/'packed_settle_candidate_v1/readback.png']+[D/'native_cycle_v1'/f'timeline_{n}.png' for n in(2,95,96)]
out=W/'root_review_checkpoint119.json';assert not out.exists()
result={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in paths],
 'prior_comparisons_actually_viewed':[{'path':(D/f).relative_to(ROOT).as_posix(),'sha256':sha(D/f)}for f in('joint_layers_probe_v2/comparison.png','joint_layers_probe_v2/partial.png','hair_registered_v1/comparison.png')],
 'arc_sha256':'15d01f06aee14e3264d7ce41d1358a530147e4a3464d3ac949b64cde5085a775',
 'findings':['초기138 기본 뒤머리가 큰 분홍 면으로 뭉쳐 보였기 때문에 최종 수용하지 않고 머릿결 국소 원화 수정 요청했다.',
 '새 머리 내부 표본을 반영한 최종138/139 재추출과 원표2/95/96을 직접 열람했다. 전신 donor 교체 없이 가닥별 어둠과 밝음이 생겼고, 손·총·발·눈과139의 원래y-1 관계를 유지한다.',
 '새 권총의 손 접점, 베일·하체 연결과 앞뒤 특수95/96의 크기를 비교했다. 추가 확정 분리·위치 튐을 찾지 못했다.',
 '등장2의133..137 등은 아직 부모 그림이다. 이 순서표에 보인다는 이유로 새 그림 완료에 포함하지 않는다. RN26의 실제 Frost 시험에서 관측한138/139도 이전 그림이며 새15d01 실기 증거가 아니다.'],
 'runtime_verified':False,'continuous_animation_actually_watched_by_model':False,'all_character_art_complete':False,'final_user_accepted':False}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
