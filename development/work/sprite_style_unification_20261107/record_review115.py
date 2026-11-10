from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/ultimate_return_repaint';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[D/'packed_return_candidate_v1'/f'readback_{n}.png'for n in(1,2,3)]+[D/'native_cycle_v1'/f'timeline_{n}.png'for n in(39,40)]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in paths],'arc_sha256':sha(D/'packed_return_candidate_v1/PL02_U.ARC'),'findings':['최종 귀환 재추출3판과 승리/귀환 순서2판을 직접 열람했다. 새156은 머릿결·앞머리 음영·옷 경계를 대기/승리의 상세표현과 이어 보았으며 빈손을 가슴 앞에 모으는 원자세를 유지한다.','새 몸에 맞춘157 테두리와158 에너지 겹침에서 확정된 몸체 잘림·따로 뜨는 외곽은 찾지 못했다.159/160은 기존 에너지 형태를 유지한다.','새 후폼 의상의 잘못된 흰 반바지는 최종재추출에 남지 않았고 수용한 검정·분홍 허리 의상으로 보인다.'],'limits':['정적 재추출과 원표39/40 시뮬레이션 검토이다. 실제 게임 귀환 및 모든부분파츠의 사람이본실기를 주장하지 않는다.','몸체156과효과파생157/158을 구분한다. 전체 캐릭터/나나 모든 동작의 품질 완료나 사용자 최종 수용은 아니다.'],'runtime_verified':False,'final_user_accepted':False}
p=W/'root_review_checkpoint115.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
