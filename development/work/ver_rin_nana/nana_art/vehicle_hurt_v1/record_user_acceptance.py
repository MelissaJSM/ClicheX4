"""탑승 둘의 사용자 수용만 기록한다. 게임 입력과 파일 패치 없음."""
import json,sys
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import write
B=ROOT/'out/ver_rin_nana/nana_vehicle_hurt_20261030T014147573781Z';rel=B.relative_to(ROOT).as_posix();quote='라이드 아머 라이드 체이서 둘다 테스트 다했어 이상없네'
acceptance={'date':'2026-10-30','user_quote':quote,'source':'user direct gameplay report','ride_armor_accepted':True,'ride_chaser_accepted':True,'visible_frames':[*range(162,175),*range(184,198),*range(199,204)],'blank_reference_preserved':198,'does_not_prove_special_damage233_236':True,'does_not_prove_all_directions_or_automated_full_capture':True,'build':rel}
write(B/'user_vehicle_acceptance.json',acceptance)
for name in('manifest.json','runtime_summary.local.json'):
 p=B/name;j=json.loads(p.read_text('utf8'));j.update(user_ride_test_pending=False,user_vehicle_accepted=True,user_vehicle_acceptance=rel+'/user_vehicle_acceptance.json',special_damage_user_accepted=False);write(p,j)
p=ROOT/'projects/ver_rin_nana/current_build.json';j=json.loads(p.read_text('utf8'));j.update(user_ride_test_pending=False,user_vehicle_accepted=True,next_group='nana_ui_or_unverified_special_damage');write(p,j)
p=ROOT/'projects/ver_rin_nana/project.json';j=json.loads(p.read_text('utf8'));j['active_substage']='NANA_VEHICLES_USER_ACCEPTED_EXTRA_HURT_APPLIED';j['nana_vehicle_hurt'].update(user_ride_test_pending=False,user_vehicle_accepted=True,user_vehicle_quote=quote,special_damage_user_accepted=False);write(p,j)
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8');s=s.replace('사용자가 아머 테스트를 맡겠다고 하여 조작을 넘겼으며 추가 입력은 하지 않는다.','사용자가 라이드 아머·라이드 체이서를 모두 테스트해 이상 없다고 보고하여 두 탑승 동작은 수용 완료다. 별도 피격233..236의 실기 확인은 남았다. 조작을 넘긴 뒤 추가 입력은 하지 않았다.').replace('이번 탑승·피격의 실제 발동은 미검증이다.','이번 탑승·피격의 자동 발동 검증은 미완료다.');p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 두 탑승 동작 사용자 수용\n\n사용자 “'+quote+'”로 라이드 아머 머리19개와 체이서13개를 수용 완료 처리한다. 빈198은 보존 상태다. 이 수용은 별도 피격233..236·아머 전용 동작·모든 방향의 자동 검증까지 포함하지 않는다. [상세](NANA_VEHICLE_HURT.md).\n\n'+p.read_text('utf8'),'utf8');print(json.dumps({'ride_armor_accepted':True,'ride_chaser_accepted':True,'special_damage_runtime_pending':True,'no_game_input':True}))
