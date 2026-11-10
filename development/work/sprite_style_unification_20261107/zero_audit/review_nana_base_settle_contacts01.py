from pathlib import Path
import hashlib,json
D=Path(__file__).parent;ROOT=D.parents[2];S=D.parent/'nana_audit/base_settle_repaint';O=D/'nana_base_settle_contacts_review01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['contacts_probe_v1/legs_comparison.png','joint_layers_probe_v2/partial.png']
r={'actually_viewed':[{'path':(S/n).relative_to(ROOT).as_posix(),'sha256':sha(S/n)}for n in names],
 'scope':'기본/포스138 하체 정합·138139 부분 소유 두 판의 정적 시각 의견만',
 'observations':[
 '포스 같은 행 국소정합 뒤에도 양 무릎·발목의 굴곡과 두 구두 구분이 유지된다. 이 판에서 종아리가 새 검정 기둥처럼 변하거나 원래 검정 부츠가 맨다리 밖에 남는 확정 결함은 찾지 못했다.',
 '화면 왼쪽 구두가 원포스보다 약간 넓어 보이지만 앞코와 발목이 이어져 읽힌다. 두 다리 전체 비율을 바꾼 인상은 없으며 실제 원순서에서의 발끝 안정성은 별도 검토 대상이다.',
 '부분판의 legs와 body+legs에서 베일 외곽이 뒤머리부터 이어지고 하체 옆에 단독 조각으로 떠 보이지 않는다. head/body/arms의 기본 부츠 및 나머지 머리도 함께 읽힌다.',
 '138과139의 부분표시에서 손을 들어 올린 자세와 몸의 연결에 새 확정 절단을 찾지 못했다.'
 ],'new_confirmed_visual_defects':[],
 'technical_assertions_not_repeated':['36개 표본 출처/최대2px','베일10셀 인덱스·소유 변경','권총 정본/원총구','후속 ARC 전체조립·GPU·원시간표'],
 'art_or_resources_modified':False,'runtime_verified':False,'native_packing_verified':False,'user_accepted':False}
O.mkdir(exist_ok=True);(O/'review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(O/'review.json'))
