"""실제 열람한 현215 직접 생성출처의 팔 의미를 별도 기록한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
O=D/'nana_ultimate_nova215_arm_visual01.json'
assert not O.exists()
paths=['work/ver_rin_nana/nana_ultimate_armor/nova_art_v1/generated.png','work/ver_rin_nana/nana_ultimate_armor/nova_art_v1/prompt.txt','work/sprite_style_unification_20261107/nana_audit/ultimate_nova_repaint/a_registered_v1/comparison_1.png','work/sprite_style_unification_20261107/zero_audit/nana_ultimate_nova_relations01/report.json']
files={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in paths}
assert files[paths[0]]=='0c1731b767721ac7338e469b888891f6ac389099686d8c0e82da6c97b5df81b0'
prompt=(ROOT/paths[1]).read_text('utf8');quote='one bent arm near the head, other forearm close to torso';assert quote in prompt
result={'scope':'나나 현행 Ultimate Nova215의 머리 뒤 피부면/팔 의미에 대한 정적 직접 열람','files':files,'actually_viewed':[paths[0],paths[2]],'read_prompt':paths[1],'prompt_cell2_quote':quote,'findings':['직접 출처 nova_art_v1/generated.png 가운데 둘째 셀에는 머리 뒤 피부 주먹, 검정 커프, 아래로 굽힌 분홍 소매가 함께 보인다. 이 직접 원화의 해당 피부면은 토끼 귀 내부로 해석하지 않는다.','a_registered_v1/comparison_1.png 하단 중간 현215에도 높은 주먹/커프가 남아 있다. 하단 오른쪽 새215에서는 그 반대팔이 허리 쪽으로 내려가 자세 의미가 달라졌다.','해당 새 팔 국소 재작화 시 현재 새 얼굴·몸·다리는 보존하면서 높은 굽힌 팔을 정합하는 근거로 쓸 수 있다. 정확한 손끝 픽셀 고정이나 외부 접촉점 존재를 이 판으로 증명하지 않는다.'],'limits':['더 이른 stage_vehicle_01 원화는 이번 보고에서 실제 열람하지 않았으며 현재215 직접 원화와 동일하다고 간주하지 않는다.','역사 Nana 제작 자세 확인이며 원US 로봇 자세의 완전 복원/게임 실기/새 팔 생성 완료를 뜻하지 않는다.'],'new_art_called':False,'assets_modified':False,'runtime_verified':False}
O.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(hashlib.sha256(O.read_bytes()).hexdigest())
