"""실제로 본 최종 판과 동일 픽셀인 재생성 판만 열람 근거에 기록한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];R=D/'rin_extension';P=R/'prepared_arrival01';O=R/'arrival294_review_v2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
read=lambda p:json.loads(p.read_text('utf8'))
q=read(P/'proposal.json');q['scope']=q['scope'].replace('타일창 두곳만','하단 타일창 각3곳(총6곳)만');(P/'proposal.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf8')
images=[]
for form in ('normal','black'):
 for page in range(2):
  p=P/f'{form}_readback_{page:02}.png';images.append({'path':rel(p),'sha256':sha(p),'actually_viewed':True})
 for page in range(3):
  p=O/f'original_order_{form}_{page:02}.png'
  if page<2:
   previous=R/'arrival294_review'/p.name;assert p.read_bytes()==previous.read_bytes()
  images.append({'path':rel(p),'sha256':sha(p),'actually_viewed':True,'viewing_evidence':'이전 판과 바이트 동일하며 이전 실제 열람'if page<2 else '실제 view_image 열람'})
out={'candidate_sha256':sha(P/'PL01_U.ARC'),'actually_viewed_by_agent':images,'findings':['새 다섯 자세에서 앞치마 안쪽 주름·커프 음영·머릿결이 기준 대기의 세부 밀도에 가까워졌다.','249/250의 다리를 무릎 아래만 옮긴 v2는 꺾임으로 배제했다. v3는 같은 새 원화의 허벅지부터 다리 전체를 옮겨 무릎 연결을 유지한다.','253에서 첫 대기0으로 넘어가는 양팔레트 비교를 실제 열람했다. 새 보닛/얼굴 높이와 접힌 무릎이 이어지며 추가 확정 절단은 발견하지 못했다.','섬광247/248은 새249의 실제 alpha에서 부모와 동일한 원규칙으로 파생됐다.'], 'runtime_verified':False,'user_accepted':False,'limitations':['시트 육안 검토는 모든 실제 60Hz 프레임과 게임 배경의 가림 검사를 대신하지 않는다.','새250/253 눈높이는 부모 대비1px 낮지만 새 얼굴 안쪽 비율을 유지했고 그 수치만 맞추기 위한 얼굴 변형을 하지 않았다.']}
(O/'visual_review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'viewed':len(images),'scope':q['scope']},ensure_ascii=False))
