from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pages=[W/'shibuki_audit/base_run_standing02_registered03'/f'{x}_comparison.png' for x in ('base','fourth')]
pages += [W/'nana_audit/rising_repaint/packed_base_candidate_v1'/f'readback_{i}.png' for i in (1,2,3)]
proof=W/'zero_audit/nana_rising7_independent01/report.json'
assert sha(proof)=='3b3c7cad3ec2ca8f2702271097e9d116731423fe9d4fc386eda7a7068f93633d'
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
   'findings':['시부키 정지 사격2 기본/포스는 옛 소매의 남은 부분 제거 후 대기와 옷 밀도·무릎 접속을 유지한다. 최종 압축 삽입 전 후보로 구분한다.',
               '나나 라이징7 패킹 재추출3판에서 새 머릿결·옷 명암·부츠 폭·사랑이 정본/손 접점의 유지가 보인다. 추가 확정 단절은 찾지 못했다.'],
   'independent_proof':{'path':proof.relative_to(ROOT).as_posix(),'sha256':sha(proof)},
   'limits':['라이징 최종 원래 순서 시뮬레이션·실기 검증은 별도이다.','네 캐릭터 전체 완료나 사용자 최종 수용을 뜻하지 않는다.'],
   'final_user_accepted':False}
p=W/'root_review_checkpoint65.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
