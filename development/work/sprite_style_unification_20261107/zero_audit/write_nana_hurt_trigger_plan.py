"""Summarize read-only native trigger evidence for live-test preparation."""
from pathlib import Path
import hashlib
import html
import json

D = Path(__file__).parent
ROOT = D.parents[2]
O = D / 'nana_hurt_triggers01'
N = O / 'native_read.json'
j = json.loads(N.read_text('utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert j['hurt_animation_dispatch'] == [0, 33, 34, 36, 35]
def source(path, lines):
    p = ROOT / path
    return {'path': path, 'sha256': sha(p), 'lines': lines}
rows = [
    {'hurt_type': 1, 'animation': 33, 'refs': [106, 107, 108, 109],
     'trigger': '접촉원 type0·기본형/몸통아머 없음·원피해5미만, 또는 접촉원이 명시 type1.',
     'form_rule': '일반 type0는 몸통아머 bit2가 있으면 type4로 우선 전환. 명시 type1은 두 폼 공통.',
     'meaning': '작은 일반 피격/밀림. 번개처럼 보이는 추가 이펙트가 있어도 감전 전용 조건이 아니다.',
     'recovery': '무적타이머75에서60이 되는 지점에 착지/낙하 상태로 복귀.'},
    {'hurt_type': 2, 'animation': 34, 'refs': [106, 110, 111, 112, 113, 114],
     'trigger': '접촉원 type0·몸통아머 없음·원피해5이상, 또는 접촉원이 명시 type2.',
     'form_rule': '일반 type0 강타도 몸통아머는 type4로 우선 전환. 명시 type2는 아머 여부와 무관하게 이 경로.',
     'meaning': '위로 날리는 강한 피격. 전격 전용이 아니다.',
     'recovery': '무적타이머100에서60으로 내려갈 때 땅/공중 조건에 맞춰 복귀.'},
    {'hurt_type': 4, 'animation': 35, 'refs': [233, 234, 235, 236],
     'trigger': 'X 캐릭터가 몸통아머 bit2를 가진 상태에서 기본 type0 접촉 피해를 받음.',
     'form_rule': '포스 풀장착뿐 아니라 몸통파츠를 가진 모든 부분아머가 해당. 기본형 type0는 이 경로가 아니다.',
     'meaning': '몸통아머 일반 피격·오라. 감전 또는 특정 보스만의 전용 효과로 분류하면 안 된다.',
     'recovery': 'type1과 같은 밀림 처리. frame236에서 팔레트0x49를 선택하고 다른 프레임은 기본 팔레트 복귀.'},
    {'hurt_type': 3, 'animation': [36, 37], 'refs': [106, 107, 108, 109],
     'trigger': '접촉원 명시 type3으로 붙잡힘. stun_timer1 동안106 유지, 외부 player_damage 호출이 -1로 바꾸면37이 재생됨.',
     'form_rule': '몸통아머가 type3을 바꾸지 않으며 두 폼 공통. 피해 감소 계산은 별도.',
     'meaning': '붙잡힘/구속. 원코드에서 잠자리 들고 조이기, 달라붙는 적, Storm Owl 잡기, Web Spider 거미줄의 주기 피해 호출을 확인.',
     'recovery': '구속 적이 timer0으로 풀면복귀.37의 음수 상대스텝 시36으로 되돌고 timer1.'},
]
native_enemy = next(x for x in j['stage10_area0_records'] if x['object_type'] == 0 and x['id'] == 0x31)
report = {
    'scope': '나나 피격13의 실제 트리거와 우주항 일반 접촉피해 시험 준비. 게임 조작/실기 수행 없음.',
    'native_read': {'path': N.relative_to(ROOT).as_posix(), 'sha256': sha(N)},
    'original_US_and_RN17_hurt_code_identical': j['RN17_unchanged_from_original_US'],
    'trigger_groups': rows,
    'common_conditions': [
        '접촉 피해 진입은 충돌 검사 통과·hurt_phase0·이미 처리 중인 HP damage flag 없음·spike_immune0 등이 필요하다.',
        '차량 탑승 중은 별도 라이드아머 피해 경로이며 플레이어13참조 관측을 보장하지 않는다.',
        '이 분기는 X의 몸통아머 bit2를 검사하며 기본/포스별 다른 애니메이션 테이블을 사용하지 않는다. 표시 의상은 같은 PL00의 부분 레이어 선택으로 달라진다.',
        '가시·압사/HP0 사망 경로는 이 피격13의 일반 재현 수단과 구별한다.',
    ],
    'spaceport_minimum_candidate': {
        'stage': 10, 'area': 0,
        'entry_spawn': {'x': 360, 'y': 2048, 'source': 'stage_objects.c Checkpoint[66]'},
        'first_near_ground_enemy': {k: v for k, v in native_enemy.items() if k != 'initializer_head'},
        'contact_damage': 3, 'contact_type': 0,
        'native_evidence': ['0x800687C0 li v0,3; 0x800687D8 sb v0,0x60(enemy)',
                            '0x80068998 jal damage_player_on_contact',
                            'main object allocator clears +0x62; train soldier has no later +0x62 type override in scanned main code'],
        'suggested_route': '시작 낙하 후 같은 바닥대에서 오른쪽 첫 병사 쪽으로 접근하고 공격하지 않은 채 몸체 접촉을 관찰한다. 배치좌표672,2235는 움직이기 전 기록이며 실시간 위치가 아니다.',
        'expected_basic': '몸통아머0: animation33 /106..109',
        'expected_fourth': '몸통아머 bit2: animation35 /233..236',
        'heavy_reaction_limit': '이 병사 몸체의 원피해3으로는 type0 강한 날림110..114를 재현하지 못한다.',
        'route_runtime_verified_here': False,
        'uncertainties': ['적이 이미 소멸했는지, 실제 이동 시간·정확 접촉좌표·안전한 버튼 유지시간은 미확인.',
                          '근처 탄환의 공격타입/피해량은 이 첫병사 몸체 결과로 대신 판정하지 않는다.',
                          '우주항에서 가장 짧은 강한 날림 또는 구속 재현 경로는 아직 특정하지 않았다.'],
    },
    'explicit_special_examples': {
        'type2_native_writes': ['rocket_spiker_update 0x8005FE48', 'falling_rock_update 0x800A05B4', 'sigma_final_grab_release 0x8008E964'],
        'type3_native_writes': ['dragonfly_carry_grab 0x8004A13C', 'latcher_update 0x8005F644', 'storm_owl_grab_dive 0x80076334'],
        'local_stage_or_fast_route_verified': False,
    },
    'sources': [source('work/research/decomp/src/main/1E1BC.c', [172, 290]),
                source('work/research/decomp/src/main/player_check.c', [136, 146, 466, 563]),
                source('work/research/decomp/src/main/player.c', [824, 927]),
                source('work/research/decomp/src/main/player_common.c', [1052, 1093]),
                source('work/research/decomp/src/main/stage_object_records_10.c', [41, 104]),
                source('work/research/decomp/src/main/stage_objects.c', [180, 280, 405, 410]),
                source('work/research/decomp/src/main/objects.c', [204, 234]),
                source('work/sprite_style_unification_20261107/zero_audit/nana_hurt_relations01/report.json', None)],
    'limitations': ['로컬 원US 코드/EXE 읽기이며 CPU 실행·게임 테스트가 아니다.',
                    '원래33..37 프레임 시간표는 기존 관계보고를 연결하며 이번에 다시 전수 검사하지 않았다.',
                    '함수명은 로컬 디컴파일 심볼명이다. 실제 게임상 적의 공식 이름으로 단정하지 않는다.',
                    '동결978a9fc의 미술/패킹 통과와 실제 게임에서 해당모션을 관측했다는 주장은 별개이다.'],
    'source_or_game_modified': False,
}
(O / 'trigger_plan.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf8')
e = html.escape
page = ['<!doctype html><html lang="ko"><meta charset="utf-8"><title>나나 피격13 재현 조건</title>',
        '<style>body{font:16px system-ui;max-width:1200px;margin:30px auto;background:#192430;color:#eaf2fa}td,th{border:1px solid #728196;padding:12px;vertical-align:top}table{border-collapse:collapse}a{color:#9cd4ff}</style>',
        '<h1>나나 피격13 · 실제 트리거 읽기</h1><p>포스233..236은 몸통아머의 일반 접촉피격입니다. 감전 전용이 아닙니다. 원US와 RN17의 관련 코드·배치·분기표가 일치합니다.</p>',
        '<p><a href="trigger_plan.json">구조화 결과</a> · <a href="native_read.json">원명령·배치 근거</a></p>',
        '<table><tr><th>유형/애니</th><th>참조</th><th>재현 조건</th><th>폼 차이</th></tr>']
for row in rows:
    page.append('<tr>' + ''.join('<td>' + e(str(v)) + '</td>' for v in
                                (f"{row['hurt_type']} / {row['animation']}", row['refs'], row['trigger'], row['form_rule'])) + '</tr>')
page.extend(['</table><h2>우주항 일반 피격의 짧은 후보</h2>',
             '<p>시작 낙하 후 오른쪽 첫 병사(id0x31, 원배치672/2235)와 몸체 접촉. 원피해3·type0이므로 기본106..109와 몸통아머233..236을 각각 예상합니다. 버튼 유지시간·실시간 위치·접촉 성공은 아직 관측하지 않았습니다.</p>',
             '<p>첫병사 몸체만으로110..114 강한 날림은 나오지 않습니다. 원피해5이상(type0·몸통아머 없음) 또는 명시type2 공격이 필요합니다. 근처 탄환을 같은 공격값이라고 가정하지 않습니다.</p>',
             '<h2>한계</h2><ul>' + ''.join('<li>' + e(s) + '</li>' for s in report['limitations']) + '</ul></html>'])
(O / 'TRIGGERS.html').write_text('\n'.join(page), 'utf8')
print(json.dumps({'report_sha256': sha(O / 'trigger_plan.json'), 'native_sha256': sha(N)}))
