from pathlib import Path
import json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];R=D/'rin_extension';P=R/'prepared_burst_remaining02';O=R/'burst303_review_v2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
assert sha(P/'PL01_U.ARC')=='1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9'
files=[P/f'{form}_readback_{i:02}.png'for form in('normal','black')for i in range(3)]+[O/f'original_order_{form}_{i:02}.png'for form in('normal','black')for i in range(5)]
report={'candidate_sha256':sha(P/'PL01_U.ARC'),'actually_viewed_by_agent':[{'path':rel(p),'sha256':sha(p),'actually_viewed':True}for p in files],'observations':['일반/레드 최종재독출6판과 원표순서10판을 실제 열람했다.178..181의 신발이 대기와 같은 파란 가죽/레드 변형으로 돌아왔고 흰 부츠 명암과 외곽은 유지된다.','177→178→179의 들린 손과 원구체,180→181의 준비 전환에서 새로 확정할 구체-장갑 분리나 추가 팔을 발견하지 못했다.','181→기존 새182..185 반복→186..189 회복에서 새 머리·앞치마·부츠 질감이 이어진다. 몸체 높이 변화는 기존 낮은 무릎 동작을 따른다.','원래182..185 반복과 외부 정적효과는 새로 그리지 않았다. 회복188의 낮은 자루끝과189의 올라오는 몸체는 같은 원점을 유지한다.'],'runtime_verified':False,'user_accepted':False,'limits':['정적 원순서 연결판 열람이며 실제 재생 영상/게임플레이 관측으로 세지 않는다.','피부/장갑 일부는 원구체에 가려져 있으며 효과 아래 모든 픽셀의 미술 판단은 분리 원화 검토와 구분한다.']}
(O/'visual_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'images':len(files),'sha256':sha(O/'visual_review.json')}))
