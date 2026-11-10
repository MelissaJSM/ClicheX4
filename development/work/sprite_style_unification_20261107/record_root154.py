from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
def record(p):
    p=ROOT/p
    return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actually_viewed':True}
h='work/sprite_style_unification_20261107/shibuki_audit/'
n='work/sprite_style_unification_20261107/nana_audit/base_nova_repaint/dash_layers_probe_v1/'
out=W/'root_review_checkpoint154.json'
assert not out.exists()
data={'checkpoint':154,'actually_viewed_files':[record(h+'nova_strike_ultimate_native01/comparison.png'),*[record(h+f'nova_strike_ultimate_effects02/comparison_{r}.png')for r in(218,219,220)],*[record(n+f'{s}.png')for s in('body_comparison','effects_comparison','partial')]],'observations':['시부키 Ultimate217 새 머릿결·안경·맨팔·종아리/신발은 수용한 획득 후 대기 의상과 일치하는 개선 방향이다. 종전 흰 재킷은 제거되었다.','시부키219 새 몸의 실루엣과220 머리 가림 보정 후보에서 추가 확정 절단은 찾지 못했다. 218 원효과 세 점 보존은 제작 기록에 따른 것이며 별도 raw 검증은 이 시각 검토에 포함하지 않는다.','나나217 기본 곱슬 머릿결과 접힌 두 신발, 포스 베일 음영·치맛단·맨다리의 세부 개선을 확인했다. 부분 조합에서 추가 확정 몸체 분리는 찾지 못했다.','나나220 원효과 속 새 몸에서도 추가 머리/신발 절단은 보이지 않았다.'],'limits':['일곱 판은 실제 열람한 정적 중간 후보이며 최종 ARC readback·원순서 재생이나 실제 게임 검증이 아니다.','시부키220 효과의 몸 가림 영역 변경은 원효과 전체 바이트 불변으로 표현하지 않는다.','최종 packed 후보와 대기/앞뒤 연결은 후속 검토한다.'],'runtime_verified':False,'whole_project_complete':False}
out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'path':out.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'viewed':len(data['actually_viewed_files'])}))
