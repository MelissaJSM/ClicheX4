from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=W/'zero_audit/x_endpoint_supplement01'
pages=[d/name/f'{leaf}.png' for name in ('shibuki','nana') for leaf in ('endpoints','hq_all12','dialogue_all8','life_all20')]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
   'findings':['두 X 캐릭터의 별도 HQ12·대화8·잔기20 및 주요 끝점8판을 직접 검토했다. 각각의 내부 윤곽/머릿결/색감은 유지되고 추가 확정 절단은 찾지 못했다.',
               'HQ의 큰 전신, 대화/메뉴 일러스트, 작은 잔기 아이콘을 플레이어 45~47픽셀 도트와 같은 그림으로 바꾸지 않는다. 원래 용도별 수용 디자인을 보존한다.'],
   'independent_proof':{'path':(d/'report.json').relative_to(ROOT).as_posix(),'sha256':sha(d/'report.json')},
   'limits':['BR14/RN15의 추출판 열람이며 해당 UI 전 장면의 새로운 실시간 애니메이션 검증이 아니다.','RN16은 라이징 파이어 몸체만 추가 변경되어 이 별도 사본에는 추가 변경이 없다.'],
   'final_user_accepted':False}
p=W/'root_review_checkpoint69.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
