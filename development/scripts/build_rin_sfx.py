"""린에 첫 모드에서 수용한 낙봉파 발동음·원작 효과음 강조를 누적한다."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_riko_sfx import patch_sfx
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from scripts.inventory_riko_voice import parse_bank
from scripts.mute_shibuki_voice import require, save
from scripts.project import digest
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks
from src.psx_spu_audio import decode_spu

PARENT = ROOT / 'out/ver_rin_nana/gameplay_voice_mute_20261030T051924864312Z'
PARENT_SHA = 'f8b1172feb5e306b3d4beef26e1a82ca0b6adc71a9898750fe13c0916fcf8d30'
ARC_SHA = '766d4c2697a4276eec07f251d8f099a7267844db6b892aafc63b99ccfd444c32'
DONOR = ROOT / 'out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin'
DONOR_SHA = '8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a'
VOICE_SHA = '7ecf160ca2fe47090f2a6c2f612b814ac359865fb303a19c012e9a3a066726f4'


def data(raw, index):
    e = psx_arc(raw)[index]
    return raw[e['offset']:e['offset'] + e['size']]


def build(activate):
    game = PARENT / 'rin_nana.bin'
    pointer_path = ROOT / 'projects/ver_rin_nana/current_build.json'
    previous = pointer_path.read_bytes()
    pointer = json.loads(previous)
    if activate:
        require(pointer['sha256'] == PARENT_SHA and ROOT / pointer['build'] == PARENT, 'Active parent differs')
    require(digest(game) == PARENT_SHA and digest(DONOR) == DONOR_SHA, 'Unsupported input BIN')
    protection = json.loads((PARENT / 'preservation.json').read_text('utf8'))
    def protect():
        for q in protection['files']:
            require(digest(ROOT / q['path']) == q['expected_sha256'], 'Protected input changed: ' + q['path'])
    protect()
    with game.open('rb') as f:
        reader = DiscReader(f, game.stat().st_size)
        hits = [q for q in reader.inspect()['files'] if q['name'] == 'PL01_U.ARC;1']
        require(len(hits) == 1, 'Ambiguous player archive')
        record = hits[0]
        arc = reader.read(record['lba'], record['size'])
    require(sha256(arc) == ARC_SHA and (record['lba'], record['size']) == (1525, 741376), 'Unsupported Rin resource')
    record = {**record, 'sha256': ARC_SHA}
    replacement, edits, offsets = patch_sfx(arc, ARC_SHA)
    require(patch_sfx(arc, ARC_SHA)[0] == replacement, 'Reproduction differs')
    require(offsets == [565602, 565634, 565666, 565698, 661552, 661554], 'Change scope differs')
    negative = []
    for label, wrong, expected in [('wrong_hash', arc, '0' * 64), ('truncated', arc[:-1], ARC_SHA),
                                   ('already_patched', replacement, ARC_SHA),
                                   ('already_patched_with_matching_hash', replacement, sha256(replacement))]:
        try:
            patch_sfx(wrong, expected)
        except ValueError:
            negative.append(label)
        else:
            raise ValueError('Invalid input accepted: ' + label)
    with DONOR.open('rb') as f:
        donor = DiscReader(f, DONOR.stat().st_size).read(record['lba'], record['size'])
    for index in range(10, 14):
        require(data(replacement, index) == data(donor, index), 'Audio differs from accepted first mode')
    require(data(replacement, 11) == data(arc, 11) and data(replacement, 13) == data(arc, 13), 'Waveform bytes changed')
    require(sha256(data(replacement, 13)) == VOICE_SHA, 'Silent voice body changed')
    sfx = parse_bank(data(replacement, 10), data(replacement, 11), True)
    require(sfx['commands'][10]['command_hex'] == '8100b015', 'Impact source command differs')
    require(data(replacement, 12)[48:52].hex() == '8100b014', 'Rakuhouha target differs')
    require(sfx['commands'][10]['tones'][0]['volume'] == 114, 'Accepted impact volume differs')
    wave = next(q for q in sfx['waves'] if q['wave_id'] == 10)
    sound = data(replacement, 11)[wave['body_offset']:wave['body_offset'] + wave['bytes']]
    decoded = decode_spu(sound)
    require(max(map(abs, decoded.pcm)) > 0 and decoded.end_flag == 1, 'Impact is silent or looping')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT / 'out/ver_rin_nana' / ('rin_sfx_' + stamp)
    out.mkdir(exist_ok=False)
    result = write_archive_copy(game, out / 'rin_nana.bin', record, replacement, PARENT_SHA)
    changed, found = [], set()
    with game.open('rb') as a, (out / 'rin_nana.bin').open('rb') as b:
        for lba in range(game.stat().st_size // 2352):
            x, y = a.read(2352), b.read(2352)
            require(len(x) == len(y) == 2352, 'Disc truncated')
            if x == y:
                continue
            require(x[:24] == y[:24], 'Sector header changed')
            validate_checks(y)
            differences = {(lba - record['lba']) * 2048 + i for i in range(2048) if x[24+i] != y[24+i]}
            require(differences and differences <= set(offsets), 'Unapproved payload difference')
            found.update(differences); changed.append(lba)
        require(not b.read(1), 'Disc grew')
    require(found == set(offsets) and set(changed) == {q['lba'] for q in result['changed_sectors']}, 'Disc changes differ')
    with (out / 'rin_nana.bin').open('rb') as f:
        require(DiscReader(f, result['size']).read(record['lba'], record['size']) == replacement, 'ARC readback differs')
    protect()
    require(digest(game) == PARENT_SHA, 'Parent changed')
    for name in ('rin_nana.cue', 'modified.arc', 'PL02_U.ARC'):
        shutil.copyfile(PARENT / name, out / name)
    (out / 'PL01_U.ARC').write_bytes(replacement)
    for folder in PARENT.iterdir():
        if folder.is_dir():
            shutil.copytree(folder, out / folder.name)
    verification = {'all_disc_sectors_compared': game.stat().st_size // 2352, 'changed_sectors': changed,
                    'changed_resource_bytes': len(offsets), 'changed_offsets': offsets, 'edits': edits,
                    'reproduced_arc_identical': True, 'readback_arc_identical': True,
                    'negative_cases_rejected': negative, 'edc_ecc_checked': True,
                    'all_other_disc_payload_exact': True, 'all_waveform_bytes_identical': True,
                    'rin_voice_waves_still_silent': 13, 'all_four_audio_entries_match_accepted_first_mode': True,
                    'impact_wave': {**wave, 'decoded_peak': max(map(abs, decoded.pcm)), 'end_flag': decoded.end_flag},
                    'protected_files': len(protection['files']), 'runtime_verified': False,
                    'limitation': '원래 voice_timer 조건 때문에 일부 상황에서는 낙봉파 발동음이 생략될 수 있음'}
    manifest = json.loads((PARENT / 'manifest.json').read_text('utf8'))
    manifest.update(kind='rin_original_sfx_reinforced', subtask='zero_rin_audio',
                    parent=PARENT.relative_to(ROOT).as_posix(), parent_sha256=PARENT_SHA,
                    modified_bin=result, modified_archive_sha256=digest(out / 'modified.arc'),
                    inherited_manifest=(PARENT / 'manifest.json').relative_to(ROOT).as_posix(),
                    inherited_verification=manifest['verification'], verification=verification,
                    gameplay_voice_mode='muted_with_nonvocal_rakuhouha', runtime_verified=False,
                    source_script_sha256=digest(Path(__file__)), patch_function_script_sha256=digest(ROOT / 'scripts/build_riko_sfx.py'))
    save(out / 'manifest.json', manifest)
    save(out / 'verification.json', verification)
    save(out / 'preservation.json', protection)
    save(out / 'authorization.json', {'user_quote': '그 예전에 낙봉파 사운드가 너무심심해서 뭔 작업을했던걸로기억하거든? 그건 해야겠는데?',
         'interpretation': '첫 모드에서 수용한 원작 효과음 보완6바이트를 린에 재사용', 'parent_sha256': PARENT_SHA})
    if activate:
        require(pointer_path.read_bytes() == previous, 'Pointer changed during build')
        (out / 'previous_current_build.json').write_bytes(previous)
        pointer.update(build=out.relative_to(ROOT).as_posix(), cue=(out / 'rin_nana.cue').relative_to(ROOT).as_posix(),
                       sha256=result['sha256'], current_session=None, runtime_verified=False,
                       rin_sfx_applied=True, rin_sfx_user_accepted=False,
                       gameplay_voice_mode='muted_with_nonvocal_rakuhouha',
                       next_scope='Rin Rakuhouha and native SFX user listening; Nana armor costumes deferred')
        pointer_path.write_text(json.dumps(pointer, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'build': out.relative_to(ROOT).as_posix(), 'sha256': result['sha256'],
                      'changed_payload_bytes': len(offsets), 'changed_sectors': changed,
                      'negative_cases': len(negative), 'activated': activate}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activate', action='store_true')
    build(parser.parse_args().activate)
