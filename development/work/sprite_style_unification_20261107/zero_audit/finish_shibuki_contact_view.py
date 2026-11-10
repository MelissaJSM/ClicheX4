from pathlib import Path
import json,hashlib
O=Path(__file__).parent/'shibuki_ultimate_return3_independent01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((O/'contact_constraints.json').read_text('utf8'))
v={'actual_view':True,'image':'contact_comparison.png','image_sha256':sha(O/'contact_comparison.png'),'constraints_sha256':sha(O/'contact_constraints.json'),'notes':['최종판은 accepted PL00 기본/포스와 parent PL02 전후, candidate PL02 전후를 모두 동일 원점·정수5배로 표시하며 발끝까지 자르지 않는다.','기존 PL02의 벌린 팔보다 새 손끝이 안쪽·위에 있으며, accepted PL00와도 정확 같은 외곽은 아니다. 이 판에서는 새로운 팔꿈치/손목 단절은 보이지 않는다.','발 모듈 정합 뒤 앞뒤 높이 차이와 종아리 연결을 확인했다. 코드 읽기로 확인한 정지 전송 단계의 물리 제약과 미술상의 자세 보존을 구별한다.'],'runtime_verified':False,'user_accepted':False}
(O/'contact_visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'visual_sha256':sha(O/'contact_visual_review.json'),'metrics':[{'source':r['source'],'form':r['form'],'body':r['body_bbox'],'regions':{k:q['bbox_world_exclusive']for k,q in r['semantic_roi_only'].items()}}for r in c['measurements']]}))
