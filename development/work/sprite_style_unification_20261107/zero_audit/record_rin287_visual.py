from pathlib import Path
import json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];R=D/'rin_extension';P=R/'prepared_chaser01';V=R/'chaser287_review';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
j=json.loads((V/'report.json').read_text('utf8'))
for r in j['sheets']:assert sha(ROOT/r['path'])==r['sha256'];r['actually_viewed']=True
(V/'report.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
paths=[P/f'{form}_readback_{i:02}.png'for form in('normal','black')for i in range(4)]+[ROOT/r['path']for r in j['sheets']]
report={'candidate_sha256':sha(P/'PL01_U.ARC'),'actually_viewed_by_agent':[{'path':rel(p),'sha256':sha(p)}for p in paths],'findings':['최종 패킹 일반/레드8판과 원순서 일반/레드12판, 총20판을 직접 열람했다. 머릿결/커프/치맛단/부츠의 내부 명암이 대기의 세부 수준에 가까워졌고 새 목·장갑·무릎 단절은 찾지 못했다.','65/67/69의 리본4위상 반복과66/68/70의 원래 상하진동에서 새몸이 같은원화로 이어진다.71..76의 네기울기 전환도 원눈/원발높이를 유지하여 새 과도한 크기 변화를 찾지 못했다.','22의 접힌 종아리/발끝이 원래보다 세밀하고 좁게 보이는 점은 조형 변화다. 정적 비교에서 지나치게 마른 확정 결함은 찾지 못했으나 실제 체이서 본체와 동작 접점은 추가 실기 범위다.','원리본 픽셀·타일은 그대로다. 새머리/등 접점에서 원리본을 같이 합성한28그림은 전부 연결되어 있다.'],'root_initial_contacts_review':'root가 chaser_contacts_probe_v1/normal_comparison.png 네각도 정합판을 실제열람하여 방향 수용. 최종 패킹8판은 아직 root 확인 대기.','root_final_review_pending':True,'runtime_verified':False,'user_accepted':False,'limitations':j['limitations']}
(V/'visual_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(len(paths))
