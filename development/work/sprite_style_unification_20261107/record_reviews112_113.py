from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def record(n,paths,findings,limits,arc=None):
 p=W/f'root_review_checkpoint{n}.json';assert not p.exists()
 r={'root_actually_viewed':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)}for q in paths],'findings':findings,'limits':limits,'runtime_verified':False,'final_user_accepted':False}
 if arc:r['arc_sha256']=sha(arc)
 p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(n,sha(p))
D=W/'nana_audit/ultimate_victory_repaint'
record(112,[D/'packed_victory_candidate_v1'/f'readback_{i}.png'for i in(1,2)]+[D/'native_cycle_v1'/f'timeline_{i}.png'for i in(39,40)],['최종 재추출 두 판과 원표39/40 순서 두 판을 직접 열람했다. 새 승리204..207은 대기와 비교한 머릿결·의복·다리 윤곽을 유지하며 206/207은 같은 규격의 권총을 사용한다.','204 가슴 앞 손, 205 경례, 206 총을 들기, 207 머리 위로 올리기의 몸체 연결에서 추가 확정 결함을 찾지 못했다.'],['156..160 귀환은 이 후보에서 보존한 이전 그림이다. 특히156의 머리 명암과 의복은 별도 재제작 대상이며 이번 승리 검토 통과를 귀환 완료로 확대하지 않는다.','원표 정지판과 자동재생 검증이며 실제 스테이지 클리어·귀환의 실기 증거는 아니다.'],D/'packed_victory_candidate_v1/PL02_U.ARC')
D=W/'root_nana_special'
record(113,[D/'registered01'/f'comparison_{i}.png'for i in(1,2)],['95/98 기본·포스의 새 고정셀 그림을 대기·이전 동작과 비교했다. 머릿결과 검은 옷 주름은 이전보다 구별되지만 최종 등록 전 후보이다.','발끝이 이전 기준보다 1px 낮으며 총구·손 규격과 두 의상의 접점 정합은 추가 작업한다.'],['아직 파츠 분할·네이티브 재삽입 전이며 게임 적용/완료를 주장하지 않는다.'])
