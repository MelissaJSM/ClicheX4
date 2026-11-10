"""높은 팔 국소v2/공통v5의 실제 정적 열람만 별도 기록."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;ROOT=D.parents[2];U=D.parent/'nana_audit/ultimate_nova_repaint';O=D/'nana_ultimate_nova215_arm_visual02.json'
assert not O.exists()
rel=lambda p:p.relative_to(ROOT).as_posix();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
viewed=[U/'raise215_local_probe_v2/comparison.png',U/'common_probe_v5/comparison.png']
inputs={rel(p):sha(p)for p in viewed+[U/'raise215_local_probe_v2/manifest.json',U/'common_probe_v5/manifest.json',D/'nana_ultimate_nova215_arm_visual01.json']}
review={'scope':'Nova215 높은 팔 새국소와213/215 공통부 후보의 정적2판 실제열람','files':inputs,'actually_viewed':[rel(p)for p in viewed],'observations':['215 높은 주먹에서 굽힌 전완과 어깨까지 연결이 다시 읽힌다. 맨팔후폼에서는 머리 뒤 검정 경계와 피부팔이 분리되며 이 판에서 추가손/세번째팔은 보이지 않는다.','213의 가슴앞 손목과 반대팔도 이어져 보이며215 어깨 주변에 명확히 남은 밝은 분홍 소매띠는 찾지 못했다. 소매 의미 출처의 전체 픽셀검사나후속레이어검사를 수행한 결과는 아니다.','새215 높은 주먹은 옛 원화보다 높고 큰 윤곽으로 읽힌다. 새 원화 정합후보로 취급하며 원손좌표exact나 외부접점복원으로 단정하지 않는다.','초기낮춘팔 v1~3 미채택과 최신높은팔 v5 미동결을 분리한다. 새머리/다리/효과를 포함한전체Nova완료로세지 않는다.'],'runtime_verified':False,'new_MIPS_or_source_requantization_run':False,'art_or_ARC_modified':False,'producer_acceptance_not_claimed':True}
O.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(O))
