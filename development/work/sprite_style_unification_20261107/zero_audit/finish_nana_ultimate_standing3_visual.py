from pathlib import Path
import hashlib,json
D=Path(__file__).parent;O=D/'nana_ultimate_standing3_independent01';ROOT=D.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'));rows=[]
for row in r['readback_sheets']:
 assert sha(ROOT/row['path'])==row['sha256'];rows.append({**row,'actually_viewed':True})
v={'technical_report_sha256':sha(O/'report.json'),'candidate_sha256':r['candidate_sha256'],'actually_viewed':rows,
 'scope':'후보 ARC에서 독립 재추출한 before/after 2판, 총 88/89/97 두 폼의 정적 비교.',
 'observations':['89의 머릿결·눈·재킷 여밈과 후폼 맨팔 손목의 경계가 구형보다 분명하다. 손과 위로 든 사선 권총의 연결에 추가 확정 단절을 찾지 못했다.',
 '97의 가슴 앞 두 손과 권총, 소매·어깨·허리 연결이 유지된다. 새 후폼 허리의 회색 면은 이 자세에서 별도의 큰 반바지 오류로 단정할 정도로 보이지 않는다.',
 '88의 머리 위 가로로 뻗은 밝은 모양은 보호한 원효과다. 이를 새 팔이나 원화 오류로 분류하지 않았다. 88과89의 새 몸체 연결 방향을 확인했다.',
 '새 종아리와 신발에서 추가 확정 절단이나 대기 대비 급격한 길이 변화는 찾지 못했다.'],
 'limits':['원표 연속 재생·실제 게임·총구 발사점은 이번 정적 열람에 포함하지 않았다.',
 '이 권총은 생성된 비사격 사선 모듈이며 정본85의20texel을 회전한 것으로 주장하지 않는다.',
 '최종 root 판단과 사용자 수용은 별도다.'],'runtime_verified':False,'user_accepted':False,'source_or_archive_modified':False}
p=O/'visual_review.json';p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
