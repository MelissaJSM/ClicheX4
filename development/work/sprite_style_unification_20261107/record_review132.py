from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_nana_vehicle'
paths=[D/f'registered_{group}01/comparison_{i}.png'for group in ('a','b')for i in (1,2)]
paths += [D/f'joint_targets03/comparison_{n}.png'for n in (162,166,174)]
paths += [D/f'joint_targets03/partial_{n}.png'for n in (162,166,170,174)]
paths += [D/f'native_sequence01/{form}_id{aid}_ordered.png'for aid in (66,68,70,75)for form in ('base','fourth')]
p=W/'root_review_checkpoint132.json';assert not p.exists()
rows=[{'path':str(q.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'actually_viewed':True}for q in paths]
j={'reviewer':'root','actually_viewed_files':rows,'scope':'Nana base/Fourth ride chaser13, eight newly authored images and nine exact native Y aliases','findings':['대기 기준 머릿결·모자/베일 명암·옷 주름을 보완한 방향을 수용한다.','초기 부분조합166에서 떨어졌던 베일 상부를 머리층으로 귀속해 이어졌다.','174 얼굴은 새 포스 원화로 공통화해 눈의 기존 y−19를 유지했다.','다리 국소등록은 새 포스 원화의 같은행/인접1행에서만 대응했으며 최대가로3셀이다. 전체몸 스케일변환/이전 몸체 덮기는 없다.','원표66/68/70/75의 실제순서 판에서 추가 확정 형태 급변·분리·세부손실을 찾지 못했다.'],'candidate_sha256':'29f7b9a054ede30562bc4c3a88da96f70a909ad05262b3fd184c566e980454db','independent_audit_pending':True,'runtime_verified':False,'continuous_animation_actually_watched_by_model':False,'whole_project_complete':False}
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(len(rows),hashlib.sha256(p.read_bytes()).hexdigest())
