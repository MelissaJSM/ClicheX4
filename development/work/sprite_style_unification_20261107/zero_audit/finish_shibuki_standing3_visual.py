from pathlib import Path
import hashlib,json
D=Path(__file__).parent;O=D/'shibuki_standing3_independent01';ROOT=D.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'))
rows=[]
for row in r['readback_sheets']:
 p=ROOT/row['path'];assert sha(p)==row['sha256'];rows.append({**row,'actually_viewed':True})
v={'technical_report_sha256':sha(O/'report.json'),'candidate_sha256':r['candidate_sha256'],
 'actually_viewed':rows,'scope':'실제 후보 ARC에서 독립 재추출한 비교 1판 및 95/97 부분 아머 각 16마스크 2판의 정적 열람.',
 'observations':['95/96의 새 머릿결, 목·옷깃, 양손과 접힌 다리의 명암이 기존 단색 면보다 대기 상세와 이어진다. 96은 같은 자세의 x+1 이동으로 보인다.',
 '97의 새 머리와 팔·소매, 허리와 신발 연결에서 새로 확정할 수 있는 절단은 찾지 못했다.',
 '머리 부분 전환에서 기본 빨간 꽃이 포스 장식으로 바뀌며, 상의·앞팔·다리 조합 32표시에서 옛 꽃의 별도 잔재나 떠 있는 새 소매 조각을 찾지 못했다.',
 '부위별 획득 상태에는 두 의상의 재질이 함께 보인다. 전신 포스와 동일한 의상이라는 주장은 하지 않으며, 현재 소유 기준에 따른 표현으로 검토했다.'],
 'limits':['실제 게임, 무기 생성 좌표, 원 애니메이션 연속 재생은 이번 열람에 포함하지 않았다.',
 '부분 마스크의 두 번째 arm CLUT는 기술 검사에 포함했지만 이 세 판은 기본 arm CLUT 시각 비교다.',
 'root 또는 사용자 최종 수용을 대신하지 않는다.'],
 'runtime_verified':False,'user_accepted':False,'source_or_archive_modified':False}
p=O/'visual_review.json';p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
