from pathlib import Path
import hashlib,json
D=Path(__file__).parent;O=D/'shibuki_ultimate_special3_independent01';ROOT=D.parents[2];H=D.parent/'shibuki_audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
r=json.loads((O/'report.json').read_text('utf8'));rows=[]
for row in r['readback_sheets']:
 p=ROOT/row['path'];assert sha(p)==row['sha256'];rows.append({**row,'actually_viewed':True})
for n in(95,97):
 p=H/f'prepared_standing_special_ultimate01/partial_{n:03}.png';rows.append({'path':rel(p),'sha256':sha(p),'actually_viewed':True})
v={'technical_report_sha256':sha(O/'report.json'),'candidate_sha256':r['candidate_sha256'],'actually_viewed':rows,
 'scope':'독립 실제 ARC 재추출 before/after 2판 및 고정된 제작자 부분16마스크 2판의 정적 검토.',
 'observations':['95/96의 새 안경·머릿결·재킷 여밈과 후폼 맨팔의 경계가 구형보다 분명하다. 접힌 다리·손목에서 새로 확정할 단절은 찾지 못했다.',
 '97의 두 팔을 들어 올린 자세에서 새 커프·주먹과 어깨, 머리 끝의 연결을 확인했다. 신발과 무릎의 명암도 유지된다.',
 'Ultimate 후폼은 짧게 퍼지는 옷단이 있는 별도 디자인이다. 95의 옷단 너비만으로 원화 오류라고 판단하지 않았다.',
 '부분판은 layer5를 켜는 조합에서 재킷, 끄는 조합에서 후폼으로 일관되게 전환된다. 이전 Ultimate의 단순 모양을 새 머리 위에 덧씌운 잔재는 찾지 못했다.'],
 'limits':['원표 연결·실제 게임에서의 모션이나 외부 효과 접점은 이번 정적 열람에 포함하지 않았다.',
 '새96=x+1은 제작정책이다. 서로 달랐던 부모95/96이 원래 같은 그림이었다는 수용이 아니다.',
 'root 최종 미술 판단 및 사용자 수용은 별도다.'],'runtime_verified':False,'user_accepted':False,'source_or_archive_modified':False}
p=O/'visual_review.json';p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
