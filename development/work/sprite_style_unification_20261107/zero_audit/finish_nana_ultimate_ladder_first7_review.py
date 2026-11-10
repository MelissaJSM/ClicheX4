"""실제 열람한 독립3판+제작자3판의 미술 범위를 기록한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;ROOT=D.parents[2];O=D/'nana_ultimate_ladder_first7_independent01';P=D.parent/'nana_audit/ultimate_ladder_repaint/packed_first7_diagnostic_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
r=json.loads((O/'report.json').read_text('utf8'));assert r['passed']and r['candidate_sha256']=='dcaf1343747fabeab3054c59fc384c3bbd598209eccb6c5a37ac84c1d340d339'
v={'candidate_sha256':r['candidate_sha256'],'technical_report_sha256':sha(O/'report.json'),'actually_viewed':[{'path':rel(f/f'readback_{i}.png'),'sha256':sha(f/f'readback_{i}.png'),'kind':'독립 ARC 재추출'if f==O else'제작자 최종 재추출'}for f in(O,P)for i in(1,2,3)],
 'observations':['143/144/145와146/147의 새 머릿결·손목 검정 커프·재킷/맨팔 구분을 실제 열람했다. 손끝/손목 사이 추가 확정 절단을 찾지 못했다.','154의 접힌 무릎에서 정강이·발목으로 이어지는 외곽과 앞으로 모인 두 손이 연결돼 보인다. 앞손 공통화로 새 손이 다른 의상에 뜨는 추가 확정 결함을 찾지 못했다.','183의 등 머릿결과양쪽들린손/무릎·신발은 두폼에서 같은 위치로 읽힌다. before소매와after맨팔·하의 분리가 유지된다.'],
 'static_art_direction_acceptable_in_viewed_scope':True,'new_confirmed_visual_defects':[],
 'limitations':['정지 재추출 6판 의견이며 실제 사다리 월드 접점·연속 속도·게임 실행의 통과가 아니다.','허용7만 검사했다.148149150151152153155는 부모 보존이며 사다리14전체 완성으로 계산하지 않는다.','생성13셀 재양자화/원MIPS 실행/브라우저 원순서검사는 이 시각기록에 포함하지 않는다.'],
 'runtime_verified':False,'user_accepted':False,'all_ladder_complete':False,'source_or_candidate_modified':False}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha(O/'report.json'),'visual_sha256':sha(O/'visual_review.json')}))
