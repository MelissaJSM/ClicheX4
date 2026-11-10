"""새Nova217 및218~220 효과 진단4판의 실제 정적 열람."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;ROOT=D.parents[2];U=D.parent/'nana_audit/ultimate_nova_repaint';O=D/'nana_ultimate_nova_dash_effects_visual01.json'
assert not O.exists()
rel=lambda p:p.relative_to(ROOT).as_posix();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
viewed=[U/'dash217_semantic_v1/comparison.png',*[U/f'effects_probe_v1/comparison_{n}.png'for n in(1,2,3)]]
files={rel(p):sha(p)for p in viewed+[U/'dash217_semantic_v1/manifest.json',U/'effects_probe_v1/manifest.json',D/'nana_ultimate_nova_relations01/report.json']}
result={'scope':'Nana 새Nova217 몸/홍채 및218~220 역사효과 재정합 진단4판 실제열람','files':files,'actually_viewed':[rel(p)for p in viewed],'findings':['새217 얼굴/녹색눈과 앞손, 접힌 두 신발이 기존 얇은 하체보다 분리되어 읽힌다. 새 하체는 기존보다 모인 덩어리로 보이므로215에서217로 넘어가는 원순서의 자세 전환은 최종 연속판에서 함께 판단할 필요가 있다.','218/220 등록효과판에서 머리끝과 앞팔의 새윤곽이 이어진다. 이 판에서 큰 사각빈틈이나 옛몸 잔상이라고 확정할 것은 발견하지 못했다.','219 새실루엣은 새 귀·뒤머리·접힌 다리 외곽을 따르며, 현몸과 달랐던 옛 실루엣을 그대로 유지한 진단과 구분된다.','218 위쪽의 작은 검정점은 기존효과의 검정3셀과 별도 대조해야 하며 이 정적판만으로 새로운 고립찌꺼기로 판정하여 제거하지 않는다.'],'source_limits':['217 눈은 원래x보다1px 오른쪽인 실제 새원화 녹색 표본이라는 manifest 설명을 읽었다. 이 열람에서 생성RGB 투표나 전체인덱스 재양자화를 실행한 것은 아니다.','218/220 원FX 외곽 exact·새몸가림0·219Manhattan2 재현은 제작자 진단이며 이보고는 기술독립검사를 새로 수행하지 않았다. 기존 역사효과 재구성 보고를 참조한다.'],'native_packed':False,'new_gameplay_verified':False,'new_source_requantization_performed':False,'art_or_ARC_modified':False,'overall_complete':False}
O.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(O))
