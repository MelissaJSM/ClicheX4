"""원US 코드 정적 읽기: 파트 수와 공용 GPU 저장공간. 실행/자원 수정 없음."""
from pathlib import Path
import hashlib, json, struct, sys
N = Path(__file__).resolve().parent
ROOT = N.parents[2]
O = N / 'sprite_part_capacity_read01'
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN

sha = lambda b: hashlib.sha256(b).hexdigest()
def save(name, obj):
    path = O / name
    assert not path.exists(), path
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
exe = read_disc(ROOT / 'MegaMan X4.bin', ('SLUS_005.61',))[0]['SLUS_005.61']
load, size = struct.unpack_from('<II', exe, 24)
data = exe[2048:2048 + size]
cs = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
def dis(start, end):
    return [f'{q.address:08x} {q.bytes.hex()} {q.mnemonic:8} {q.op_str}'
            for q in cs.disasm(exe[2048 + start-load:2048 + end-load], start)]

# 전체 EXE 선형 디스어셈블은 중간 데이터/미정의 명령에서 멈출 수 있다.
# 따라서 LUI scratch 후보를 정렬된 원래 워드로 먼저 찾고 짧은 구간만 읽는다.
contexts = []
for off in range(0, len(data)-4, 4):
    word = struct.unpack_from('<I', data, off)[0]
    if word >> 26 == 15 and word & 0xffff == 0x1f80:
        lines = dis(load + off, min(load + len(data), load + off + 80))
        if any(s in line for line in lines for s in ('0x100(', '0x104(', '0x124(', ', 0x100', ', 0x104', ', 0x124')):
            contexts.append({'address': hex(load+off), 'disassembly': lines})
save('pool_pointer_contexts_v2.json', {
    'method': '정렬된 EXE 원시 word의 LUI 1f80 검색 후 80B 문맥. 실행경로 전수증명 아님.',
    'supersedes': 'pool_pointer_contexts.json의 빈 결과는 전체 선형 decode 조기종료로 부재 증거로 사용하지 않음.',
    'contexts': contexts,
})

segments = [
 ('frame_pool_initialization', 0x80023db8, 0x80023e68),
 ('player_dispatch_order', 0x80023e68, 0x80023ed0),
 ('base_entry_guard', 0x80024334, 0x80024384),
 ('base_count_and_loop_guard', 0x800243d8, 0x80024470),
 ('base_next_part_and_epilogue', 0x80024844, 0x80024920),
 ('armor_dispatch', 0x800257bc, 0x8002588c),
 ('armor_count_and_zero_branch', 0x80025948, 0x800259a0),
 ('armor_next_part', 0x80025bf0, 0x80025c34),
 ('other_shared_users_guard1', 0x80024920, 0x80024958),
 ('other_shared_users_guard2', 0x80024b9c, 0x80024bd4),
]
evidence = [{ 'name': name, 'start': hex(start), 'end_exclusive': hex(end),
             'sha256': sha(exe[2048 + start-load:2048 + end-load]),
             'disassembly': dis(start, end)} for name,start,end in segments]
save('instruction_evidence.json', evidence)
armor_text = '\n'.join(dis(0x8002588c, 0x80025cdc))
assert '0x124' not in armor_text
assert '0x3e8' not in armor_text
assert struct.unpack_from('<I', exe, 2048+0x80024400-load)[0] == 0x94420000
assert struct.unpack_from('<I', exe, 2048+0x8002445c-load)[0] == 0x286203e8
assert struct.unpack_from('<I', exe, 2048+0x80024868-load)[0] == 0x25ceffff
assert struct.unpack_from('<I', exe, 2048+0x80025960-load)[0] == 0x94420000
report = {
 'status': '정적 원코드 읽기 완료; 후보 통과 판정 아님',
 'original_exe_sha256': sha(exe),
 'source': 'MegaMan X4.bin / SLUS_005.61',
 'conclusion': '읽은 본체/아머 렌더러에는 개별 프레임 24파트 clamp가 없다. 본체 count는 unsigned16이며 31도 루프가 처리하는 범위이다. 이는 고정 32타일 용량이나 전체 장면 GPU 안전성 증명과는 별개다.',
 'base_renderer': {
   'function': '0x80024334..0x80024920',
   'count': '0x80024400 lhu; 0x80024868 count-1; 0x8002486c 남으면 0x8002444c로 반복; record stride4B',
   'global_counter': '0x1f800124; 0x80023ddc에서 화면 draw 시작시 0; 본체 entry 및 매 파트 직전 1000 미만인지 검사; 파트당 +1',
   'counter_guards': ['0x80024368', '0x8002445c'],
   'early_exit': '1000에 도달한 중간파트 분기는 0x800248ec로 가며 정상 pointer/OT commit(0x80024874..248e8)을 건너뛴다. 일부만 잘려도 정상 프레임이라는 가정 금지.',
 },
 'armor_renderer': {
   'function': '0x8002588c..0x80025cdc',
   'count': '0x80025960 lhu; count0은0x80025984→25c30; 나머지는 record4B/count-1 반복',
   'global_counter': '이 함수에는 scratch124/1000 비교가 없으나 같은 scratch100/104 패킷 포인터를 소비한다.',
 },
 'shared_pools': {
   'primitive_pointer': '0x1f800100', 'drawmode_pointer': '0x1f800104',
   'primitive_base': '0x801499c8 + display_index*0xa000',
   'drawmode_base': '0x80169d98 + display_index*0x2000',
   'primitive_per_part_bytes': 40, 'drawmode_per_part_bytes': 8,
   'stride_slots': [40960//40,8192//8],
   'capacity_scope': '1024는 실제 초기화 stride와 파트 증가량으로 계산한 해당 double-buffer 영역의 슬롯 수. 링버퍼/무제한 확장이라는 근거 없음.',
   'reserve_interpretation': '1000과1024의 차이24가 아머 등 미계수 사용량을 위한 여유처럼 보이나 의도는 추론이며, 개별 본체24 제한은 아니다.',
   'shared_counted_users': ['0x80024334 본체', '0x80024920', '0x80024b9c'],
   'scope': 'draw dispatcher 및0x80024000..25cdc와 원시scratch문맥을 읽음. 다른 오버레이/모든 게임 경로의 소비를 실행 검증하지 않음.',
 },
 'requested_candidate_arithmetic': {
   'source': 'HUD 전달 수치이며 후보 ARC 자체를 이번 보고에서 열지 않음.',
   'base_parts': 31, 'armor_parts': [1,3,1,2], 'total_parts': 38,
   'primitive_bytes': 38*40, 'drawmode_bytes': 38*8,
   'base_counter_increment': 31, 'uncounted_armor_slots': 7,
   'necessary_bounds': ['본체 시작 counter+31<=1000', '시작 primitive pool slot+38<=1024', '시작 drawmode pool slot+38<=1024', '뒤에 그려질 다른 공유 사용자 및 전체 아머 미계수 사용량까지 포함'],
   'normal_draw_observation': '23e88에서 플레이어 본체,23ea4에서아머 호출. 앞24e70의HUD는scratch108/10c/110 별도영역,241e8은OT초기화다. 일반 draw 경로에서 플레이어가 먼저 소비하지만 모든 runtime 조건을 실행한 것은 아니다.',
 },
 'required_followup': ['후보 실제 count31/아머7 및 원FX24의 순서·색인 보존 읽기', '원MIPS 렌더러로31파트 루프와38개 패킷, 마지막파트/guard영역 및양방향 확인', '목표 EXE의 관련 함수와 원US 차이 확인', '다른 객체 포함실기/전체frame pointer량은 별도'],
 'limits': ['MIPS 실행 없음','새 후보/패커/게임 코드 수정 없음','원화/ARC/EXE 쓰기 없음','후보 GPU 완료 또는 실기 통과 주장 없음','32타일/4096B는텍스처이고GPU파트수와다른제약'],
}
save('report.json', report)
save('READ_LOCK.json', {'files': {p.name:sha(p.read_bytes()) for p in sorted(O.iterdir()) if p.is_file()},
                         'scripts': {p.name:sha(p.read_bytes()) for p in [Path(__file__),N/'read_sprite_part_capacity01.py']}})
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'lock_sha256':sha((O/'READ_LOCK.json').read_bytes()),'scratch_contexts':len(contexts)},ensure_ascii=False))
