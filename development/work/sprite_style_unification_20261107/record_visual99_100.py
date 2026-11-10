from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,paths,findings,limits):
 p=W/f'root_review_checkpoint{n}.json';assert not p.exists();p.write_text(json.dumps({'root_actually_viewed':[{'path':(W/q).relative_to(ROOT).as_posix(),'sha256':sha(W/q)} for q in paths],'findings':findings,'limits':limits,'final_user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(p.name,sha(p))
write(99,[f'nana_audit/ultimate_hurt_repaint/native_cycle_v1/timeline_{i}.png' for i in range(33,38)],['나나 Ultimate 피격 원표33..37의 순서도5판을 직접 열람했다. 피격 몸체와 번개/단색 실루엣이 같은 기준점을 따라 연결되며 추가 확정 스케일 변화·몸체 분리를 찾지 못했다.'],['정지 순서도 열람이며 실제 게임의 전속도 반복 관찰을 대신하지 않는다. 별도 브라우저 검사84캔버스/6재생은 기계 검사이고 사용자 수용은 아직 없다.'])
write(100,['root_nana_ladder/registered_page02/comparison_1.png','root_nana_ladder/registered_page02/comparison_2.png'],['나나 기본/포스144/149 새4표시를 직접 열람. 넓은 분홍 단색 머리가 나뉜 머릿결로 바뀌고 베일/옷 주름이 살아났다.','기존보다 발끝2~3픽셀 아래인 차이와 올라간 손의1픽셀 오차를 확인했다. 후보를 그대로 패킹하지 않고 접점을 먼저 정합한다.'],['현재는 새 원화 후보이며 총구/사격/부분아머 공통층/실기는 미완료.'])
