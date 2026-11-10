"""수용된 무음 빌드에서 원작 세이버/적중음을 강조하고 낙봉파에 비음성 발동음을 연결한다."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from scripts.inventory_riko_voice import parse_bank
from scripts.prepare_riko_voice import SOURCE_HASH
from scripts.project import digest, write_json
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks
from src.psx_spu_audio import decode_spu

BASE = ROOT / 'out/ver_buki_riko/riko_voice_20261026T020845493327Z'
BASE_HASH = 'b536cfa9b31a07c9816ee884d3e21f1d5cfa3607850aeaad4411fe2f5ddf862b'
SFX_HEADER_HASH = 'eedd528abf5f201cc3ff825f8d88e4784058b24189722beb4bb9e45673c7f842'
VOICE_HEADER_HASH = '7f184dc4629c0012520d2a6a405cc26a63b658ef8206c85e33c36c117250e151'


def patch_sfx(arc, expected_hash):
    if sha256(arc) != expected_hash:
        raise ValueError('Unsupported parent archive')
    entries = psx_arc(arc)
    sfx_header, sfx_body, voice_header, voice_body = entries[10:14]
    if sfx_header['sha256'] != SFX_HEADER_HASH or voice_header['sha256'] != VOICE_HEADER_HASH:
        raise ValueError('Unexpected sound command/header revision')
    def payload(entry):
        return arc[entry['offset']:entry['offset'] + entry['size']]
    sfx = parse_bank(payload(sfx_header), payload(sfx_body), True)
    voice = parse_bank(payload(voice_header), payload(voice_body), True)
    if (sfx['slot'], voice['slot'], sfx['command_count'], voice['command_count']) != (1, 3, 14, 13):
        raise ValueError('Unexpected sound bank slots')
    for wave in voice['waves']:
        start = wave['body_offset']
        if any(decode_spu(payload(voice_body)[start:start + wave['bytes']]).pcm):
            raise ValueError('Parent player voice is not silent')
    result = bytearray(arc)
    edits = []
    for sound_id, tone_id, wave_id, old_volume, new_volume in (
        (7, 8, 9, 105, 120), (8, 9, 9, 105, 120),
        (9, 10, 11, 100, 114), (10, 11, 10, 100, 114)):
        command = sfx['commands'][sound_id]
        if len(command['tones']) != 1:
            raise ValueError('Expected one tone for selected SFX')
        tone = command['tones'][0]
        if (tone['tone'], tone['wave_id'], tone['volume']) != (tone_id, wave_id, old_volume):
            raise ValueError('Selected SFX tone mapping differs')
        sharing = [c['sound_id'] for c in sfx['commands'] if any(t['tone'] == tone_id for t in c['tones'])]
        if sharing != [sound_id]:
            raise ValueError('Unexpected shared tone')
        offset = sfx_header['offset'] + sfx['vab_offset'] + 32 + 128 * 16 + tone_id * 32 + 2
        if result[offset] != old_volume:
            raise ValueError('Tone volume address differs')
        result[offset] = new_volume
        edits.append({'kind': 'tone_volume', 'slot': 1, 'sound_id': sound_id,
                      'tone': tone_id, 'wave_id': wave_id, 'offset': offset,
                      'before': old_volume, 'after': new_volume})
    # US sound_key_on uses command byte 0's low 6 bits as the VAB ID.
    # Reuse the existing non-vocal impact, retaining the original voice channel 20.
    old = bytes.fromhex(voice['commands'][10]['command_hex'])
    source = bytes.fromhex(sfx['commands'][10]['command_hex'])
    if old != bytes.fromhex('8300a014') or source != bytes.fromhex('8100b015'):
        raise ValueError('Unexpected Rakuhouha or impact command')
    new = source[:3] + old[3:]
    offset = voice_header['offset'] + 8 + 10 * 4
    result[offset:offset + 4] = new
    edits.append({'kind': 'nonvocal_command', 'slot': 3, 'sound_id': 10,
                  'offset': offset, 'before_hex': old.hex(), 'after_hex': new.hex(),
                  'source_slot': 1, 'source_sound_id': 10, 'spu_channel': 20})
    changed = [i for i, (a, b) in enumerate(zip(arc, result)) if a != b]
    allowed = [e['offset'] for e in edits[:-1]] + [offset, offset + 2]
    if changed != sorted(allowed):
        raise ValueError('Unexpected resource byte changes')
    return bytes(result), edits, changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activate', action='store_true')
    args = parser.parse_args()
    game = BASE / 'riko_motion.bin'
    if digest(ROOT / 'MegaMan X4.bin') != SOURCE_HASH or digest(game) != BASE_HASH:
        raise ValueError('Protected source or mute build hash differs')
    source = json.loads((ROOT / 'work/ver_buki_riko/voice_production/v1/original/manifest.local.json').read_text('utf-8'))
    record = source['arc_record'].copy()
    with game.open('rb') as stream:
        arc = DiscReader(stream, game.stat().st_size).read(record['lba'], record['size'])
    record['sha256'] = sha256(arc)
    replacement, edits, changed_offsets = patch_sfx(arc, record['sha256'])
    # Reproducibility and refusal checks operate on the actual supported input.
    assert patch_sfx(arc, record['sha256'])[0] == replacement
    for invalid, expected in ((arc, '0' * 64), (arc[:-1], record['sha256']), (replacement, record['sha256'])):
        try:
            patch_sfx(invalid, expected)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid or already-patched archive accepted')
    out = ROOT / 'out/ver_buki_riko' / ('riko_sfx_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(exist_ok=False)
    written = write_archive_copy(game, out / 'riko_motion.bin', record, replacement, BASE_HASH)
    (out / 'modified.arc').write_bytes(replacement)
    (out / 'riko_motion.cue').write_bytes((BASE / 'riko_motion.cue').read_bytes())
    changed_sectors, found_offsets, lba = [], set(), 0
    with game.open('rb') as a, (out / 'riko_motion.bin').open('rb') as b:
        while True:
            old, new = a.read(2352 * 256), b.read(2352 * 256)
            if len(old) != len(new):
                raise ValueError('BIN length changed')
            if not old:
                break
            if old != new:
                for offset in range(0, len(old), 2352):
                    x, y = old[offset:offset + 2352], new[offset:offset + 2352]
                    if x == y:
                        continue
                    sector = lba + offset // 2352
                    validate_checks(y)
                    if x[:24] != y[:24]:
                        raise ValueError('Sector header changed')
                    for j in range(24, 2072):
                        if x[j] != y[j]:
                            address = (sector - record['lba']) * 2048 + j - 24
                            if address not in changed_offsets:
                                raise ValueError('Unexpected game payload change')
                            found_offsets.add(address)
                    changed_sectors.append(sector)
            lba += len(old) // 2352
    if found_offsets != set(changed_offsets) or set(changed_sectors) != {s['lba'] for s in written['changed_sectors']}:
        raise ValueError('Readback edit set differs')
    validation = {'all_raw_sectors_compared': lba, 'changed_sectors': changed_sectors,
                  'changed_archive_offsets': changed_offsets, 'payload_changed_bytes': len(changed_offsets),
                  'edits': edits, 'source_sha256': SOURCE_HASH, 'parent_sha256': BASE_HASH,
                  'output_sha256': written['sha256'], 'all_waveform_bytes_unchanged': True,
                  'all_13_original_voice_waveforms_still_silent': True,
                  'graphics_exe_xa_fmv_bgm_other_banks_unchanged': True,
                  'repeat_archive_identical': True, 'invalid_inputs_rejected': 3,
                  'runtime_verified': False, 'user_playtest_pending': True,
                  'limitation': '낙봉파 발동음은 원래 기합 호출 조건을 유지하므로 voice_timer > 0이면 생략될 수 있음'}
    write_json(out / 'sfx_validation.local.json', validation)
    manifest = json.loads((BASE / 'manifest.json').read_text('utf-8'))
    manifest.update(kind='riko_original_sfx_reinforced_v1', modified_bin=written,
                    modified_archive_sha256=sha256(replacement), modification_base_sha256=BASE_HASH,
                    sfx=validation)
    manifest['voice'].update(mode='muted_with_nonvocal_rakuhouha',
                             nonvocal_command_override={'sound_id': 10, 'vab_slot': 1, 'tone': 11},
                             user_mute_accepted=True)
    write_json(out / 'manifest.json', manifest)
    if digest(game) != BASE_HASH or digest(ROOT / 'MegaMan X4.bin') != SOURCE_HASH:
        raise ValueError('Protected input changed')
    if args.activate:
        path = ROOT / 'projects/ver_buki_riko/current_build.json'
        previous_bytes = path.read_bytes()
        p = json.loads(previous_bytes)
        if p['bin_sha256'] != BASE_HASH:
            raise ValueError('Current build changed; refusing pointer update')
        (out / 'previous_current_build.local.json').write_bytes(previous_bytes)
        p.update(kind=manifest['kind'], build=out.relative_to(ROOT).as_posix(),
                 cue=(out / 'riko_motion.cue').relative_to(ROOT).as_posix(),
                 bin_sha256=written['sha256'], previous_build=BASE.relative_to(ROOT).as_posix(),
                 previous_bin_sha256=BASE_HASH,
                 previous_pointer_snapshot=(out / 'previous_current_build.local.json').relative_to(ROOT).as_posix(),
                 voice_mode='muted_with_nonvocal_rakuhouha', sfx_user_review_pending=True,
                 sfx_runtime_verified=False, sfx_validation=(out / 'sfx_validation.local.json').relative_to(ROOT).as_posix(),
                 session=None, session_closed=True, previous_session=p.get('session'),
                 report='docs/RIKO_SFX.md', next_task='세이버·적중음 강조 및 낙봉파 발동음 사용자 청취 확인')
        temp = path.with_suffix('.sfx.tmp')
        with temp.open('x', encoding='utf-8') as stream:
            json.dump(p, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        if path.read_bytes() != previous_bytes:
            raise ValueError('Pointer changed during activation')
        temp.replace(path)
    print(json.dumps({'output': str(out), 'sha256': written['sha256'],
                      'changed_payload_bytes': len(changed_offsets), 'changed_sectors': len(changed_sectors),
                      'activated': args.activate}))


if __name__ == '__main__':
    main()
