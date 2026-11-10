"""보호된 X의 8보스 기록을 별도 Nana 캡슐 전 시험 카드로 복제한다."""
import json, sys
from functools import reduce
from hashlib import sha256
from operator import xor
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import digest
SOURCE = ROOT/'work/overhaul_20261105/baseline/user_backup/ver_buki_riko/memcards/epsxe001.mcr'
SOURCE_SHA = 'ab68aa740dd7a93b8b01b4b4b9cf1a57dab11c9900052879bfbc665499bf120f'
SLOT_HEX = '0030020fff06fff000200080001000408000100002004000200008000400000000000000000000000100'
OFFSET = 8192 + 512 + 2*42

def inspect_card(data):
    if len(data) != 131072 or data[:2] != b'MC':raise ValueError('Unexpected card format')
    directory = data[128:256]
    if (directory[0] != 0x51 or directory[10:30].split(b'\0')[0] != b'BASLUS-00561'
        or int.from_bytes(directory[4:8], 'little') != 8192 or directory[8:10] != b'\xff\xff'):
        raise ValueError('Expected one-block X4 save in block one')
    checks = [reduce(xor, data[i*128:i*128+127], 0) == data[i*128+127] for i in range(16)]
    if not all(checks):raise ValueError('Card header/directory XOR check failed')
    # This authenticated native X4 record uses lowercase sc, not an assumed SC.
    if data[8192:8196] != b'sc\x13\x01':raise ValueError('Unexpected game save header')
    return checks

def prepare(data):
    if sha256(data).hexdigest() != SOURCE_SHA:raise ValueError('Unexpected protected source card')
    inspect_card(data)
    if data[OFFSET:OFFSET+42].hex() != SLOT_HEX:raise ValueError('Unexpected original DATA3 record')
    target = bytearray(data)
    for field, value in ((2, 0), (3, 0), (41, 1)):target[OFFSET+field] = value
    changes = [i for i, (a, b) in enumerate(zip(data, target)) if a != b]
    if changes != [OFFSET+2, OFFSET+3, OFFSET+41]:raise ValueError('Unexpected save field change')
    inspect_card(target)
    return bytes(target), changes

def main():
    data = SOURCE.read_bytes();target, changes = prepare(data)
    out = ROOT/'work/ver_rin_nana/overhaul_runtime/preultimate_cards'
    if out.exists():raise ValueError('Fresh isolated test output required')
    negative = []
    for offset in (0, 128+127, OFFSET, OFFSET+4):
        corrupt = bytearray(data);corrupt[offset] ^= 1
        try:prepare(corrupt)
        except ValueError:negative.append(offset)
        else:raise ValueError('Corrupt card accepted')
    inventory = []
    paths = sorted((ROOT/'work/overhaul_20261105/baseline/user_backup').glob('*/memcards/*.mcr'))
    paths.append(ROOT/'work/ver_rin_nana/test_cards/nana_fourth_idle_v1/epsxe001.mcr')
    for path in paths:
        raw = path.read_bytes()
        inventory.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha256(raw).hexdigest(),
            data_records=[raw[8192+512+i*42:8192+512+(i+1)*42].hex() for i in range(3)]))
    proof = dict(source=SOURCE.relative_to(ROOT).as_posix(),source_sha256=SOURCE_SHA,
        target_sha256=sha256(target).hexdigest(),record='card2 DATA3',changed_offsets=changes,
        before=data[OFFSET:OFFSET+42].hex(),after=target[OFFSET:OFFSET+42].hex(),
        fields_before=dict(character=0,max_hp=48,arm_type=2,armor=15,boss_flags=255,ultimate=0),
        fields_after=dict(character=0,max_hp=48,arm_type=0,armor=0,boss_flags=255,ultimate=1),
        source_inventory=inventory,header_and_directory_checks_passed=inspect_card(target),
        directory_and_save_header_unchanged=data[:OFFSET]==target[:OFFSET],
        non_target_record_bytes_preserved=True,negative_corrupt_inputs_rejected=negative,
        native_layout_source='work/research/decomp/src/main/menu.c:1141 func_8001C210 / 1190 func_8001C3E8; record at game file +0x200, 42 bytes',
        scope='첫 모드 X의 8보스 DATA3에서 세 아머 필드만 바꾼 독립 Nana 시험 카드. 사용자 현재 Nana 진행·실제 커맨드·캡슐 획득 시험과 구분.',
        boss_progress_max_hp_weapons_preserved=True,user_cards_modified=False,runtime_loaded=False)
    out.mkdir(parents=True);path=out/'card2_preultimate.mcr';path.write_bytes(target)
    if path.read_bytes()!=target or digest(SOURCE)!=SOURCE_SHA:raise ValueError('Output/source preservation failed')
    (out/'preparation.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(output=str(path),sha256=proof['target_sha256'],changed_offsets=changes)))
if __name__=='__main__':main()
