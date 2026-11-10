from pathlib import Path
import json, hashlib
W=Path(__file__).resolve().parent; ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
review=W/'root_review_checkpoint104.json'
paths=[W/'shibuki_audit/hurt_base_sequence01'/f'{form}_id{n}_ordered.png' for form in ('base','fourth') for n in (33,34,35)]
assert not review.exists()
review.write_text(json.dumps({'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths],
 'findings':['시부키 기본/포스 피격의 원순서 비교판 여섯 장을 직접 열람했다. 머리와 의상 경계의 세부 묘사를 대기와 비교했고, 새 몸체와 그 몸체에서 파생한 섬광/흑화/전기 효과의 실루엣이 이어진다.', '몸을 웅크리는110/234의 낮아진 높이는 포즈에 따른 것이다. 235/236은 같은234 몸체에 원 백색/청색 외곽 효과가 이어지며 별도 옛 의상 조각은 보이지 않는다.'],
 'limits':['원순서 정지판 열람과 자동 canvas 재생 검사는 실제 게임 피격 검증과 구분한다.','모든 순간의 미술적 무결점이나 사용자 최종수용을 주장하지 않는다.'],
 'arc_sha256':'87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b','final_user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8')
plan=read(W/'staging_br_v16.json');D=W/'shibuki_audit/prepared_hurt_base01'; f=read(D/'FROZEN.json')
assert sha(D/'FROZEN.json')=='4d40a9904c6fb4f2f56d0d4c73c2998c752a246f2c10d727bd0f717886859d84'
for name,h in f['files'].items():assert sha(D/name)==h,(name,h)
assert f['parent_arc_sha256']==plan['resources']['PL00_U.ARC']['after']
plan['resources']['PL00_U.ARC'].update(path=(D/'PL00_U.ARC').relative_to(ROOT).as_posix(),after=f['candidate_sha256'])
plan['candidate_freeze_bindings']['PL00_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
for n in (103,104):
 p=W/f'root_review_checkpoint{n}.json';plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
plan['output']='out/ver_buki_riko/sprite_style_unification_20261107_v17';assert not (ROOT/plan['output']).exists()
plan['checkpoint_label']='four_character_style_checkpoint_17_shibuki_base_fourth_hurt'
out=W/'staging_br_v17.json';assert not out.exists();out.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
print(out.name,sha(out)); print(review.name,sha(review))
