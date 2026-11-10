"""최신 BIN의 실제 애니메이션 표를 단독 스프라이트 앨범용으로 내보낸다.

게임 데이터와 저장 자료는 입력 전용이다. 출력은 프레임 순서 검토 자료이며
게임의 입력, 물리, 이벤트 핸들러, 무기 객체 또는 실제 플레이를 재현하지 않는다.
"""
from __future__ import annotations
import copy
import hashlib
import json
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader

OUT = ROOT / 'work/sprite_consistency_20261105/playback'
GALLERY = ROOT / 'out/sprite_consistency_20261105'
COVERAGE = ROOT / 'work/sprite_consistency_20261105/coverage'
EXE_SHA = '1789ef719487b3e49571ccc2f419d6eb36c16f03709a16cb74f856d433f699ab'
SOURCES = {
    'ver_buki_riko': ('shibuki_riko', '5a57b31c7a4410d697183a01b2246a28344c847cefb331d27aad56135e7a924d'),
    'ver_rin_nana': ('rin_nana', 'de818d585fe1a4455d9b07551f3161b24357e3a1a2343d84102628a1fde55679'),
}
CHARACTERS = {
    'shibuki': ('ver_buki_riko', 'x', '텐코 시부키'),
    'nana': ('ver_rin_nana', 'x', '하나코 나나'),
    'riko': ('ver_buki_riko', 'zero', '유즈하 리코'),
    'rin': ('ver_rin_nana', 'zero', '아오쿠모 린'),
}
TABLES = {'x': 0x80119DF0, 'zero': 0x8011AFF0, 'capsule': 0x8011BF40}
ZERO_SELECTOR = 0x8011AF60
COMMON_LABELS = {
    0: ('대기 참조 / 별칭', 'idle'), 1: ('등장 / 전송 빛', 'arrival'),
    2: ('등장 착지와 준비', 'arrival'), 3: ('귀환 자세', 'victory_return'),
    4: ('전송 빛 이동', 'victory_return'), 5: ('대기', 'idle'),
    6: ('체력 부족 대기', 'hurt'), 7: ('이동 시작', 'run'), 8: ('이동', 'run'),
    9: ('이동 종료', 'run'), 10: ('점프 상승', 'air'), 11: ('하강', 'air'),
    12: ('착지', 'air'), 13: ('벽에 붙기', 'wall'), 14: ('벽차기', 'wall'),
    15: ('벽 미끄러짐', 'wall'), 16: ('지상 대시', 'dash'), 17: ('지상 대시 종료', 'dash'),
    18: ('공중 대시', 'dash'), 19: ('공중 대시 종료', 'dash'),
    27: ('사다리 잡기', 'ladder'), 28: ('사다리 꼭대기에 올라서기', 'ladder'),
    29: ('위에서 사다리 내려잡기', 'ladder'), 30: ('사다리 바닥에서 내리기', 'ladder'),
    31: ('사다리 위로', 'ladder'), 32: ('사다리 아래로', 'ladder'),
    33: ('사망 직전 자세 / 별도 소멸 이펙트 제외', 'hurt'),
    34: ('피격 변형 34', 'hurt'), 35: ('피격 변형 35', 'hurt'),
    36: ('피격 변형 36', 'hurt'), 37: ('피격 변형 37', 'hurt'),
    38: ('스크립트 이동', 'run'), 39: ('승리', 'victory_return'),
    40: ('승리 후 퇴장', 'victory_return'),
}
ZERO_LABELS = {
    88: ('지상 베기 1', 'attack'), 89: ('지상 베기 2', 'attack'), 90: ('지상 베기 3', 'attack'),
    91: ('공중 베기 / 상승', 'attack'), 92: ('공중 베기 / 하강', 'attack'),
    93: ('사다리 베기', 'attack'), 94: ('벽 베기', 'attack'),
    95: ('뇌신격 시작', 'special'), 96: ('뇌신격 계속', 'special'),
    97: ('빙열참 낙하', 'special'), 98: ('빙열참 착지', 'special'),
    99: ('이단 점프', 'air'), 100: ('회전 베기', 'special'),
    101: ('용염인 상승', 'special'), 102: ('용염인 종료', 'special'),
    103: ('낙봉파', 'special'), 104: ('질풍아 / 지상 대시 베기', 'special'),
    118: ('벽 베기 효과 참조', 'effect'), 119: ('뇌신격 효과 1', 'effect'),
    120: ('뇌신격 효과 2', 'effect'), 121: ('빙열참 무기 객체 / 별도 VRAM 필요', 'effect'),
    122: ('회전 베기 효과', 'effect'), 123: ('용염인 효과 1', 'effect'),
    124: ('용염인 효과 2', 'effect'), 125: ('질풍아 효과', 'effect'),
}
X_LABELS = {
    88: ('정지 사격', 'attack'), 89: ('정지 사격 복귀 / 외부 유지시간', 'attack'),
    90: ('정지 사격 변형 90', 'attack'), 91: ('정지 사격 변형 91', 'attack'),
    92: ('사다리 사격', 'attack'), 93: ('사다리 사격 복귀 / 외부 유지시간', 'attack'),
    94: ('정지 사격 변형 94', 'attack'), 95: ('차지 프로스트 실드', 'special'),
    96: ('소울 보디 조종', 'special'), 99: ('라이징 파이어 / 지상', 'special'),
    100: ('라이징 파이어 / 공중', 'special'), 101: ('차지 라이징 파이어 / 지상', 'special'),
    102: ('차지 라이징 파이어 / 공중', 'special'),
    104: ('더블 사이클론', 'special'), 105: ('차지 더블 사이클론', 'special'),
    106: ('노바 스트라이크', 'special'), 132: ('사격 후 하강 진입', 'air'),
}
GROUP_LABELS = {'idle':'대기','run':'이동','air':'공중','dash':'대시','wall':'벽',
                'ladder':'사다리','hurt':'피격·체력 부족','attack':'공격','special':'특수 기술',
                'arrival':'등장','victory_return':'승리·귀환','vehicle':'탑승',
                'effect':'별도 효과 참조','capsule':'캡슐 잔상','unclassified':'표 참조 / 용도 미확정'}
GENERAL_LIMITS = [
    '실제 플레이 영상이 아니라 최신 실행 파일의 애니메이션 표를 따라가는 프레임 검토 시뮬레이션입니다.',
    '384×384 캔버스의 원점 (160,160)을 고정합니다. 이동 거리·점프 궤적·충돌·카메라는 재현하지 않습니다.',
    '유지시간 단위는 animate_object 호출 횟수입니다. 화면의 초당 60호출은 검토용 가정이며 실측 프레임률이 아닙니다.',
    '이벤트 바이트는 표시만 합니다. 공격·소리·투사체 생성·입력·상태 전환·반투명 GPU 합성은 실행하지 않습니다.',
    '표의 position0에서 시작합니다. 게임이 중간 스텝으로 진입하거나 남은 사격 시간을 이어받는 조건은 재현하지 않습니다.',
    '마지막 relative_step=0 자세는 검토를 위해 유지합니다. 실제 게임에서는 호출자가 상태를 바꾸거나 일찍 종료할 수 있습니다.',
    '렌더링하지 못한 부분 VRAM 참조는 시간을 유지하는 빈 칸으로 표시합니다. 이전 그림을 추측해 채우거나 건너뛰지 않습니다.',
]

def need(ok, why):
    if not ok:
        raise ValueError(why)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def load(path):
    return json.loads(path.read_text('utf8'))

def rel(path):
    return path.relative_to(ROOT).as_posix()

def at(exe, address, size):
    offset = address - 0x80010000 + 2048
    need(2048 <= offset <= len(exe)-size, f'EXE 범위 밖: {address:#x}')
    return exe[offset:offset+size]

def read_disc(path, names):
    with path.open('rb') as handle:
        reader = DiscReader(handle, path.stat().st_size)
        records = {x['name'].split(';')[0]: x for x in reader.inspect()['files']}
        return {n: reader.read(records[n]['lba'], records[n]['size']) for n in names}

def parse_sequence(exe, table, aid):
    pointer = at(exe, table+4*aid, 4)
    address, = struct.unpack('<I', pointer)
    position, seen, steps = 0, set(), []
    while position not in seen:
        need(position >= 0 and len(seen) < 512, '잘못된 상대 스텝')
        seen.add(position)
        raw = at(exe, address+position*4, 4)
        duration, event, relative_step, frame = struct.unpack('<bbbB', raw)
        steps.append({'position': position, 'address': hex(address+position*4), 'bytes': raw.hex(),
                      'duration_signed': duration, 'duration_calls': (duration & 255) or 256,
                      'event': event, 'event_bits': event & 255,
                      'relative_step': relative_step, 'frame_ref': frame})
        position += relative_step
    index = next(i for i, s in enumerate(steps) if s['position'] == position)
    terminal = steps[-1]['relative_step'] == 0
    return {'id': aid, 'native_animation_id': aid, 'table_address': hex(table),
            'address': hex(address), 'pointer_bytes': pointer.hex(), 'steps': steps,
            'loop_to_position': position, 'loop_start_index': index,
            'terminal_position': position if terminal else None,
            'terminal_policy': 'hold_for_review_external_game_state_not_simulated' if terminal else None,
            'prefix_calls': sum(x['duration_calls'] for x in steps[:index]),
            'loop_calls': sum(x['duration_calls'] for x in steps[index:]),
            'sequence_calls': sum(x['duration_calls'] for x in steps),
            'exact_table_loop': not terminal, 'uninterrupted_table_timing_exact': True,
            'simulation_only': True, 'runtime_verified': False}

def semantic(family, aid):
    labels = dict(COMMON_LABELS)
    labels.update(ZERO_LABELS if family == 'zero' else X_LABELS)
    if family == 'x' and 119 <= aid <= 131:
        source = aid-112
        if source in COMMON_LABELS:
            labels[aid] = (COMMON_LABELS[source][0]+' / 사격 연결', COMMON_LABELS[source][1])
    if family == 'x' and 139 <= aid <= 143:
        labels[aid] = (COMMON_LABELS[aid-112][0]+' / 사격 연결', 'ladder')
    if aid in labels:
        return (*labels[aid], '호출 함수 및 기존 기술별 조사에 근거')
    if 41 <= aid <= 64:
        return (f'라이드 아머 참조 {aid} / 차량 제외', 'vehicle', '플레이어 탑승 호출 구간; 세부 자세 명칭 미확정')
    if 65 <= aid <= 76:
        return (f'라이드 체이서 참조 {aid} / 차량 제외', 'vehicle', '플레이어 탑승 호출 구간; 세부 자세 명칭 미확정')
    return (f'표 참조 {aid} / 용도 미확정', 'unclassified', '표 존재 확인; 이름 및 실제 진입 경로 미확정')

def get_frames(char, family, manifest, revisions):
    frames = {}
    if family == 'x':
        for frame in manifest['frames']:
            path = revisions.get(frame['id'], frame.get('path'))
            frames[frame['id']] = {'path': path, 'render_status': frame['status'],
                                   'reason': frame.get('reason'), 'group': frame.get('group'),
                                   'display_mask': frame.get('display_mask'), 'arm_type': frame.get('arm_type')}
    else:
        for frame in manifest['frames']:
            for form in ('normal','black'):
                key = form+':'+frame['id']
                path = frame.get('images',{}).get(form)
                path = rel(GALLERY/char/path) if path else None
                frames[key] = {'path':revisions.get(key,path), 'render_status':frame['render_status'],
                               'reason':frame.get('reason'), 'group':frame.get('group')}
    for key, item in frames.items():
        if item['path']:
            path = ROOT/item['path']
            need(path.is_file(), f'존재하지 않는 프레임 {char}/{key}: {path}')
            item['png_sha256'] = digest(path)
            item['revised_in_current_build'] = key in revisions
    return frames

def mapped_animation(native, family, form, frames, selector=0):
    anim = copy.deepcopy(native)
    aid = anim['id']
    label, group, confidence = semantic(family, aid)
    anim.update(label=f'{aid:03d} · {label}', group=group, group_label=GROUP_LABELS[group],
                label_evidence=confidence, recommended=(aid in COMMON_LABELS and aid != 0) or
                aid in (ZERO_LABELS if family=='zero' else X_LABELS), graphics_bank=selector,
                composition_bank=5 if selector else 0, external_event_bytes=[s['event_bits'] for s in anim['steps'] if s['event_bits']])
    limits = []
    if group == 'vehicle':
        limits.append('플레이어 파츠만 재생합니다. 차량 본체와 핸들·좌석 이동은 포함하지 않습니다.')
    if group == 'ladder':
        limits.append('사다리 동작은 실제 게임에서 입력 중에만 갱신될 수 있습니다. 연속 호출을 가정한 검토입니다.')
    if group in ('hurt','effect'):
        limits.append('실시간 팔레트 섬광과 외부 무기 VRAM·효과 객체는 이 재생만으로 재현하지 않습니다.')
    if family == 'x':
        limits.append('선택한 폼의 고정 레이어 합성입니다. 실제 장면의 임시 아머 마스크·소울 보디·발사체는 별도입니다.')
        if aid in (89,93):
            limits.append('호출자가 attack_pose_timer로 유지시간을 덮어씁니다. 여기서는 표 원래 시간만 보여줍니다.')
        if aid == 106 and form in ('base','ultimate_before'):
            anim['gameplay_reachable_in_form'] = False
            limits.append('이 폼은 실제 노바 사용 조건을 갖추지 않습니다. 공유 표의 그림 검토만 제공합니다.')
        else:
            anim['gameplay_reachable_in_form'] = None
    else:
        limits.append('일반/블랙 몸체 팔레트는 별도입니다. 다른 CLUT의 효과색은 추출 당시 참조이며 현재 실기색 검증이 아닙니다.')
    for step in anim['steps']:
        ref = step['frame_ref']
        key = f'{form}:b{selector}_{ref:03d}' if family=='zero' else f'{form}_{ref:03d}'
        frame = frames.get(key)
        reason = None
        if family == 'zero' and aid == 121:
            reason = '빙열참 무기 객체가 조립 bank6과 별도 무기 VRAM을 사용하므로 플레이어 bank 그림으로 대체할 수 없음'
        elif not frame:
            reason = '스프라이트 모음집에 해당 실제 bank/ref가 없음'
        elif not frame['path'] or frame['render_status'] in ('unreconstructed','partial_vram_requires_previous_texture'):
            reason = frame.get('reason') or '부분 VRAM 로딩 이력 또는 별도 자원 필요; 임의 복원하지 않음'
        step.update(frame_id=None if reason else key, expected_frame_id=key, reason=reason,
                    origin=[160,160], render_status=frame['render_status'] if frame else 'missing')
        if frame:
            step['display_mask'] = frame.get('display_mask')
    anim['limitations'] = limits
    return anim

def capsule_animation(native, form, bank, frames):
    anim = copy.deepcopy(native)
    anim.update(id=f'{form}_{bank}_{native["id"]}',
                label=f'캡슐 잔상 bank{bank} · 원래 ID {native["id"]}', group='capsule',
                group_label=GROUP_LABELS['capsule'], graphics_bank=bank, composition_bank=bank+8,
                recommended=True,
                limitations=['캡슐 잔상의 원래 프레임 표입니다. 캡슐 이동·반투명·팔레트 순환·본체와의 합성은 재현하지 않습니다.'])
    for step in anim['steps']:
        key = f'{form}_{bank}_{step["frame_ref"]}'
        frame = frames.get(key)
        valid = frame and frame['path'] and frame['render_status'] != 'unreconstructed'
        step.update(frame_id=key if valid else None,expected_frame_id=key,origin=[160,160],
                    reason=None if valid else '캡슐 참조를 독립 렌더링하지 못함',
                    render_status=frame['render_status'] if frame else 'missing')
    return anim

def main():
    gallery = load(GALLERY/'gallery_manifest.json')
    revisions = {x['id']:x['revisions'] for x in gallery['characters']}
    original_path = ROOT/'MegaMan X4.bin'
    need(digest(original_path)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b','원본 US 입력 해시 불일치')
    original = read_disc(original_path,['SLUS_005.61'])['SLUS_005.61']
    native, inputs, checks = {}, {}, []
    for project,(stem,expected) in SOURCES.items():
        path=ROOT/f'out/{project}/sprite_consistency_20261105_v1/{stem}.bin'
        need(digest(path)==expected, '최신 BIN 해시 불일치')
        pointer = load(ROOT/f'projects/{project}/current_build.json')
        need(pointer['sha256']==expected,'현재 빌드 포인터와 입력 불일치')
        assets = read_disc(path,['SLUS_005.61','PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'])
        exe=assets['SLUS_005.61']; need(sha(exe)==EXE_SHA,'실행 파일 해시 불일치')
        inputs[project]={'bin':rel(path),'bin_sha256':expected,'assets':{n:sha(v) for n,v in assets.items()}}
        native[project]={}
        for family,count in (('x',144),('zero',144),('capsule',54)):
            native[project][family]=[parse_sequence(exe,TABLES[family],a) for a in range(count)]
            need(native[project][family]==[parse_sequence(original,TABLES[family],a) for a in range(count)],'원본과 애니메이션 표가 다름')
        selector=list(at(exe,ZERO_SELECTOR,144))
        need(bytes(selector)==at(original,ZERO_SELECTOR,144),'원본과 Zero bank selector 다름')
        need(set(selector)<= {0,1},'예상하지 못한 selector')
        native[project]['selectors']=selector
        checks.append({'project':project,'x_ids':144,'zero_ids':144,'effect_table_ids':54,
                       'reachable_step_and_pointer_bytes_identical_to_original':True,
                       'selector_identical_to_original':True,'selector_sha256':sha(bytes(selector))})
    timer=load(COVERAGE/'native_animation_timer.json');need(timer['passed'],'실제 MIPS 타이머 검사 실패')
    chars={}
    for char,(project,family,label) in CHARACTERS.items():
        manifest=load(GALLERY/char/'manifest.json'); revision=revisions[char]
        revision_sha=revision.get('source_sha256',revision.get('built_bin_sha256'))
        if revision['frames']:
            need(revision_sha==inputs[project]['bin_sha256'],'수정 이미지가 최신 BIN 소스와 다름')
        elif family=='zero':
            need(manifest['source']['arc_sha256']==inputs[project]['assets']['PL01_U.ARC'],'미수정 Zero ARC가 달라짐')
        frames=get_frames(char,family,manifest,revision['frames'])
        forms={}
        definitions=manifest['forms'] if family=='x' else [dict(id=x,label='일반' if x=='normal' else '블랙') for x in ('normal','black')]
        for formdef in definitions:
            form=formdef['id']
            animations=[mapped_animation(a,family,form,frames,native[project]['selectors'][a['id']] if family=='zero' else 0) for a in native[project][family]]
            forms[form]={'label':formdef['label'],'animations':animations,
                         'idle_frame_id': f'{form}_000' if family=='x' else f'{form}:b0_147',
                         'idle_animation_id':5,'native_animation_count':144}
        if family=='x':
            for form,aid in (('capsule_fourth',37),('capsule_ultimate',38)):
                forms[form]={'label':'포스 캡슐 잔상' if aid==37 else '얼티밋 캡슐 잔상',
                             'animations':[capsule_animation(native[project]['capsule'][aid],form,b,frames) for b in range(10,14)]}
        chars[char]={'label':label,'project':project,'family':family,'source':inputs[project],
                     'forms':forms,'image_sources':frames,
                     'latest_revision_frame_count':len(revision['frames']),
                     'runtime_verified_by_this_export':False}
    all_anims=[a for c in chars.values() for f in c['forms'].values() for a in f['animations']]
    all_steps=[s for a in all_anims for s in a['steps']]
    unresolved=Counter(s['reason'] for s in all_steps if not s['frame_id'])
    result={'schema_version':1,'kind':'native_table_frame_review_not_gameplay','characters':chars,
            'groups':GROUP_LABELS,'limitations':GENERAL_LIMITS,'sources':inputs,
            'timer_proof':{'path':rel(COVERAGE/'native_animation_timer.json'),'sha256':digest(COVERAGE/'native_animation_timer.json'),
                           'exe_sha256':EXE_SHA,'passed':True,'raw_signed_zero_calls':256,'raw_signed_minus_one_calls':255},
            'playback_contract':{'default_calls_per_second':60,'calls_per_second_is_assumption':True,
                'duration_unit':'uninterrupted animate_object calls','start_position':0,
                'step_transition':'position += relative_step; match position, not array offset',
                'terminal_handling':'hold current terminal frame indefinitely for review; external state not executed',
                'missing_step_handling':'show blank with reason for full duration; never skip',
                'dynamic_partial_fourth':'use fourth animation sequence and remap fourth_NNN to selected live-composite ref'},
            'source_code_evidence':[
                {'file':'work/research/decomp/src/main/player_common.c','lines':[360,400],'scope':'X graphics0/parts0, Zero bank selector0/1→parts0/5'},
                {'file':'work/research/decomp/src/main/player_weapon.c','lines':[1230,1260],'scope':'X moving shooting variant +112 and frame/duration continuation'},
                {'file':'work/research/decomp/src/main/player.c','lines':[125,157],'scope':'beam-in caller processes event and terminal to change state'},
                {'file':'work/research/decomp/src/main/player.c','lines':[769,820],'scope':'ladder input-gated animation calls'},
                {'file':'work/research/decomp/src/main/item_26_light_capsule.c','lines':[442,457],'scope':'capsule graphics10..13/parts18..21 and shared animation IDs37/38'},
                {'file':'scripts/prepare_zero_specials.py','scope':'Zero121 weapon override is separate composition6 and weapon VRAM, not bodybank1'},
            ],
            'coverage':{'characters':4,'forms':sum(len(c['forms']) for c in chars.values()),
                        'animation_form_sequences':len(all_anims),'steps':len(all_steps),
                        'timed_unrendered_steps':sum(unresolved.values()),'unrendered_reasons':dict(unresolved),
                        'all_sequences_simulation_only':True,'native_tables_compared':checks}}
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'manifest.json';target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    verification={'passed':True,'manifest':rel(target),'manifest_sha256':digest(target),
                  'coverage':result['coverage'],'native_timer':timer,'source_before_after_hashes':{}}
    for project,source in inputs.items():
        after=digest(ROOT/source['bin']);need(after==source['bin_sha256'],'입력 변경 감지')
        verification['source_before_after_hashes'][project]={'before':source['bin_sha256'],'after':after,'unchanged':True}
    (OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'manifest':rel(target),'sha256':digest(target),'coverage':result['coverage']},ensure_ascii=False))

if __name__=='__main__':
    main()
