from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'shibuki_audit/base_run_complete_pack06'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'PL00_U.ARC')=='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce'
paths=[D/f'{form}_readback_{i:02}.png' for form in ('base','fourth') for i in range(6)]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths],
   'packed_asset_sha256':sha(D/'PL00_U.ARC'),
   'findings':['시부키 기본/포스32참조의 최종 재추출12판을 대기 옆에서 직접 열람했다. 새 머릿결·옷깃·소매·부츠 묘사가 압축 뒤에도 남고 일반/사격의 같은 보행 자세가 이어진다.',
               '포스 서서사격2의 이전 큰 흰 가슴과 아래쪽 잔여 소매가 정리된 모습을 확인했다. 이 판에서 새 확정 절단이나 원화가 거친 옛 도트로 되돌아간 현상은 찾지 못했다.'],
   'limits':['공간 정리와 내부은행 이동은 미술 열람만으로 안전성을 확인하지 않는다. 독립 전체디렉터리/원코드/새 부팅 검사가 별도다.',
             '정적 전신64표시이며 부분1024조합 전부를 사람이 보았거나 전체실기를 마친 것은 아니다.'],
   'final_user_accepted':False}
p=W/'root_review_checkpoint75.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
