"""새 CUE 부팅의 읽기 전용 RAM 사본과 준비한 음향 자원을 대조한다."""
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.build_hurt_capsule_fix import WORK, NAMES, proposal, require, write_json
from scripts.overhaul_audio_verify_cpu import banks
from scripts.overhaul_nana_progress_refresh import loaded_vab_header
from src.psx_disc import file_hash

inputs = {
    'ver_rin_nana': 'work/ver_rin_nana/korean_runtime/20261105T222104975805Z',
    'ver_buki_riko': 'work/ver_buki_riko/korean_runtime/20261105T222402056879Z',
}
out = {}
for mode, rel in inputs.items():
    path = ROOT / rel
    evidence = json.loads((path / 'evidence.json').read_text('utf8'))
    session = Path(evidence['session'])
    close = json.loads((session / 'close.local.json').read_text('utf8'))
    require(close['exited'] and len(evidence['ram_bases']) == 1, 'Missing closed unique runtime')
    ram_path = path / f"ram_{evidence['ram_bases'][0]}.bin"
    ram = ram_path.read_bytes()
    at = (struct.unpack_from('<I', ram, 0x141f50 + 12)[0] & 0x1fffffff) - 8
    start = struct.unpack_from('<I', ram, 0x141f30 + 12)[0]
    matches = []
    if at >= 0:
        for name, (_, resource) in proposal(mode, WORK / f'audio/prepared_v1/{mode}/proposal.json', NAMES).items():
            h, body, q = banks(resource)[3]
            if ram[at:at + len(h)] == loaded_vab_header(h, body, start):
                matches.append(name)
    out[mode] = {
        'bin_sha256': evidence['bin_sha256'], 'session': session.relative_to(ROOT).as_posix(),
        'RAM': ram_path.relative_to(ROOT).as_posix(), 'RAM_sha256': file_hash(ram_path),
        'resident_player_bank_matches': matches, 'hurt_tone_volume_104_verified': bool(matches),
        'header_address': hex(at) if at >= 0 else None, 'session_closed_normally': True,
        'actual_hurt_event_or_mixed_audio_verified': False, 'capsule_scene_verified': False,
        'F1_F3_used': False, 'process_memory_written': False,
    }
cards = json.loads((WORK / 'runtime/cards_before.json').read_text('utf8'))
for card in cards:
    require(file_hash(ROOT / card['path']) == card['sha256'], 'Isolated card changed')
write_json(WORK / 'runtime/boot_results.json', {
    'projects': out, 'isolated_cards_preserved': cards,
    'scope': '새 부팅과 상주한 경우 음향 헤더를 검사. 실제 피격 청취·캡슐 재현을 뜻하지 않음.'})
print(json.dumps(out))
