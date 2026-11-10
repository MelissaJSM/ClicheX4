from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,paths,findings,limits):
 out=W/f'root_review_checkpoint{n}.json';assert not out.exists()
 data={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths],'findings':findings,'limits':limits,'final_user_accepted':False}
 out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');print(n,sha(out))
D=W/'nana_audit/rising_repaint'
write(61,[D/'common_legs_probe_v2'/f'comparison_{i}.png' for i in (1,2,3)]+[D/'common_legs_probe_v3/comparison.png'],
 ['v2의101 발끝과104 긴 부츠가 지나치게 뾰족/가늘어 보여 보류했다.','v3는 같은 새 원화의 발끝3행/부츠13행 폭과 명암을 복구해 인상이 개선됐다. 포스 대응 구두도 과대해지지 않아 국소 방향을 수용한다.'],
 ['머리·부분층·최종패킹/재추출 검증 전 후보이며 현재BIN 반영이 아니다.'])
D=W/'zero_audit/final_endpoint_audit01'
write(62,[D/form/(name+'.png') for form in ('riko','rin') for name in ('endpoints','hq_all14','life_all9','dialogue_all3')],
 ['두 캐릭터의 저장 정상/블랙, 별도 헌터베이스14, 잔기9, 대사3과 메뉴 초상화를8판에서 직접 검토했다.','HQ/대사는 별도 해상도에서 머리결·옷 명암을 유지한다. 작은 잔기는 사용자가 수용한 독립 디자인이며 조종석 머리의 낡은 사본으로 판단하지 않았다.'],
 ['모음집4510표시와 별도 보충판이다.','정적 재추출 검토로 이번 게임에서 모든HQ 눈/입 프레임을 재생한 것은 아니다.'])
D=W/'shibuki_audit'
write(63,[D/f'base_run_shot_page{page:02}_registered02'/(form+'_comparison.png') for page in range(2,6) for form in ('base','fourth')],
 ['기본/포스 이동사격10..32의8비교판을 직접 검토했다. 머리 가닥·소매/옷 명암 방향을 수용하며 새 확정 팔 연결 절단은 찾지 못했다.'],
 ['원화 등록 후보이며 서서2·부분 조합·패킹·재추출 검토가 남아 있다.','현재BIN에 적용됐다는 증거가 아니다.'])
