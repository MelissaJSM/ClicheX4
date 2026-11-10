"""호버10 독립 재추출과 원효과 점유판의 실제 열람 기록."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[2];U=D.parent/'nana_audit/ultimate_hover_repaint';O=D/'nana_ultimate_hover10_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads((O/'report.json').read_text('utf8'))
assert sha(O/'report.json')=='d88f6713a8007e5065909d2ca3b3a22200fccbfaea6a01e9d1e07d61b7795665'
for p,h in r['inputs'].items():assert sha(ROOT/p)==h,p
for q in r['readback_sheets']:assert sha(ROOT/q['path'])==q['sha256']
source_sheets=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in[U/f'muzzle_joint_probe_v1/comparison_{i}.png'for i in(1,2,3)]]
v={'candidate_sha256':r['candidate_sha256'],'independent_report_sha256':sha(O/'report.json'),'actually_viewed_readback_sheets':r['readback_sheets'],'actually_viewed_source_sheets':source_sheets,'observations':['재추출 사격짝5판에서 머릿결·귀장식·의상·부츠의 명암이 새 대기 방향으로 세분화되어 있고, 비사격/사격의 머리·하체가 이어진다. 새로운 명백한 분리나 여분 팔은 찾지 못했다.','222/224는 원발사점으로 더 뻗은 팔이지만 어깨부터 손목까지 이어지고 아래 피부 그늘이 남아 있다. 가는 손목과 권총의 접촉이 끊겨 보이지 않는다.','226/228은 원발사점이 몸에 가까운 접힌 팔이다. 특히228의+3x 등록 뒤 팔꿈치와 검정 상의 앞 경계가 붙어 읽히며, 이 판에서 잘린 어깨나 몸을 가로지르는 새 검정띠를 찾지 못했다.','230의 올라간 손목·총과 낮은 뒤팔은 구분된다. 새 종아리의 회색 그늘도 양쪽 사격짝에서 유지된다.','원추진15위상을 5판에서 실제 열람했다. 새 신발과 원래 점유면이 이어지고, 사격 전후 하체가 같은 위치에 남는다. 중립색 면은 불꽃의 실제 팔레트·블렌딩 표현이 아니다.','첫 탄환188픽셀 점유1판은 다섯 원점과 정본 총끝이 함께 보이는 정적 합성이다. 새 팔/총의 좌표 정합 근거이며 실제 발사 순간이나 양방향 게임 실행의 대용은 아니다.'],'new_art_requiring_change_found':False,'runtime_verified':False,'limits':['생성10셀의 원화 재양자화 검사는 제작자가 수행했다. 독립은 등록된 새 몸/팔의 재구성과 목표50층·비대상·효과·총손을 대조했다.','MIPS는 제작자 실행의 동일 decoded hash를 결속했다. 이번 독립 검수에서 새 원MIPS/게임 실행은 하지 않았다.']}
p=O/'visual_review.json';assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
code=[D/'verify_nana_ultimate_hover10_independent.py',D/'verify_shibuki_ultimate_hurt13_independent.py',Path(__file__)]
lock={'reader_sources':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in code],'input_hashes':r['inputs'],'additional_viewed_inputs':source_sheets,'outputs':{q.name:sha(q)for q in O.iterdir()if q.is_file()},'immutable_paths':True}
p=O/'READER_LOCK.json';assert not p.exists();p.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'report':sha(O/'report.json'),'visual':sha(O/'visual_review.json'),'lock':sha(p)}))
