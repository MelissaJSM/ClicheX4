"""Keep per-reference art preparation separate from native/runtime evidence."""
from pathlib import Path
import json, hashlib

D = Path(__file__).parent
OUT = D / 'rin_extension'
groups = json.loads((D / 'group_map.json').read_text('utf8'))['rin']
done = set(f'b0_{n:03d}' for n in list(range(7,34)) + [35,39,40,44,46,47,48,49,50,51,52,95,97,99,101])
done |= {'b0_061','b0_174','b0_175','b0_176','b0_177','b1_005','b1_182','b1_183'}
done |= {'b1_184','b1_185'}
assert len(done) == 52
priority = {'dash':1,'run':1,'jump':1,'wall':1,'ground_saber':2,'wall_saber':2,'air_saber':2,'hyouretsuzan':2,'raijingeki_shared':2,'ladder':3,'ryuenjin':3,'shippuuga':3,'air_spin':3,'rakuhouha':4,'rakuhouha_static_body':4,'ride_chaser':4,'ride_armor_head':4,'victory_return_body':4,'arrival_body':4,'hurt':4,'low_hp':4}
rows, body, effect = [], set(), set()
for name, g in groups.items():
    refs = set(g['body_or_head_refs']); body |= refs; effect |= set(g['effect_or_blank_refs'])
    rows.append({'group':name,'priority':priority.get(name,5),'body_or_head_refs':sorted(refs),'new_art_prepared':sorted(refs & done),'remaining':sorted(refs - done),'effect_or_blank_or_partial':g['effect_or_blank_refs'],'action':g['action'],'runtime_new_art_verified':False,'normal_black_share_bitmap':True})
arc = OUT / 'prepared_burst_pair_final_v1/PL01_U.ARC'
data = {
    'scope':'린 일반/블랙은 같은 비트맵을 공유한다. 정적 미술/작업 ARC 준비와 실제 게임 검증·사용자 수용을 구분한다.',
    'current_arc':str(arc), 'current_sha256':hashlib.sha256(arc.read_bytes()).hexdigest(),
    'new_art_prepared_refs':sorted(done), 'body_or_head_unique_refs':len(body),
    'remaining_refs_in_original_audit':sorted(body-done), 'groups':rows,
    'next_authored_inputs':[{'directory':None,'bank':0,'refs':[34,36,37,38,41,45],'reason':'공중·벽·대시의 남은 고유 자세를 각 동작에 맞는 정밀 원화로 이어서 제작한다.41의 동일 표시42/43도 확인한다.'}],
    'limitations':[
        '대기 참조는 사용자 수용 기준이며 새 아트 교체 수에 포함하지 않는다.',
        '8개 부분 VRAM 참조는 독립 완성 PNG로 대체하거나 누락으로 단정하지 않는다.',
        '회전·탑승·후면을 같은 정면 머리로 일괄 덮지 않는다.',
        '단계별 UI 복제본과 정적 동작의 본체 동기화는 해당 본체 확정 후 별도 검사한다.',
        '52참조 전체의 실제 연속 플레이 및 사용자 수용은 아직 미확인이다. 신규185는 루트 미술 검토 대기다.',
        '정적23/24는 각각 새185/182 몸체와 동기화했고 전체 효과 알파·외부 배경은 보존했다.',
        '원래 전수 장부315개에는 중복·대기·일부 효과 오분류가 포함된다.남은263참조가263개 새 그림을 의미하지 않는다.'
    ]
}
(OUT / 'progress_ledger.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'body_or_head':len(body),'new':len(done),'remaining':len(body-done),'effects_or_partial':len(effect)}))
