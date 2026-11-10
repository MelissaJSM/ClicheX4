"""승인된 나나·린 플레이 음원만 같은 길이의 무음으로 교체한다."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from scripts.inventory_riko_voice import parse_bank
from scripts.project import digest
from scripts.mute_shibuki_voice import require, save
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks
from src.psx_spu_audio import decode_spu, silence_fixed_oneshot, validate_oneshot_template, vag_container

PARENT = ROOT / 'out/ver_rin_nana/nana_life_face_20261030T050400807577Z'
PARENT_SHA = '5cf497173d6640e43cb785e31c9a031d663f976654a26b6dd6a0a665f01fd53a'
SOURCE = ROOT / 'MegaMan X4.bin'
SOURCE_SHA = '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
FFMPEG = ROOT / 'work/tools/voice_env/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
X_SPEC = (796672, 12, '22ebe296498468fe7a1e9de2b74f18bb185b391e0930ae530646c6e94037d2ed',
          '3aae0b66f594a8d09dac66c609701c5d0823c240522966c5bc0c57df073a16c2')
SPECS = {'PL00_U.ARC': X_SPEC, 'PL02_U.ARC': X_SPEC,
         'PL01_U.ARC': (741376, 13, '7f184dc4629c0012520d2a6a405cc26a63b658ef8206c85e33c36c117250e151',
                       'd01c61834cdaf791ff9cc1deccdbe437e8d1e225f1eb3b33629e50000eecf221')}


def entry_data(raw, entry):
    return raw[entry['offset']:entry['offset'] + entry['size']]


def mute_archive(current, original, name):
    size, waves, header_sha, body_sha = SPECS[name]
    require(len(current) == len(original) == size, 'Unsupported archive length')
    entries, native = psx_arc(current), psx_arc(original)
    head, body_entry = entries[12:14]
    require(head['type'] == '0x6' and body_entry['type'] == '0x20301', 'Unexpected voice entries')
    header, body = entry_data(current, head), entry_data(current, body_entry)
    require(sha256(header) == header_sha and sha256(body) == body_sha, 'Unsupported voice bank hashes')
    require(header == entry_data(original, native[12]) and body == entry_data(original, native[13]),
            'Voice differs from verified original')
    bank = parse_bank(header, body, True)
    require((bank['slot'], bank['wave_count'], bank['command_count'], bank['tone_count'], bank['program_count'])
            == (3, waves, 13, waves + 1, 1), 'Unsupported command/wave layout')
    require(bank['initial_padding_bytes'] == 0, 'Unexpected voice bank padding')
    require({t['wave_id'] for c in bank['commands'] for t in c['tones']} == set(range(1, waves + 1)),
            'Voice command coverage differs')
    require(all((int(c['command_hex'][:2], 16) & 63) == 3 for c in bank['commands']), 'Nonvoice command')
    muted, cursor, evidence = bytearray(body), 0, []
    for wave in bank['waves']:
        offset, length = wave['body_offset'], wave['bytes']
        require(offset == cursor and offset + length <= len(body), 'Wave overlap or incomplete coverage')
        raw = body[offset:offset + length]
        samples = validate_oneshot_template(raw)
        quiet = silence_fixed_oneshot(raw)
        decoded = decode_spu(quiet)
        require(len(decoded.pcm) == samples and not any(decoded.pcm), 'Silence or duration differs')
        require(raw[:16] == quiet[:16] and raw[-16:] == quiet[-16:] and raw[1::16] == quiet[1::16],
                'Reserved blocks/playback flags changed')
        muted[offset:offset + length] = quiet
        cursor += length
        evidence.append({**wave, 'original_peak': max(map(abs, decode_spu(raw).pcm)), 'muted_peak': 0,
                         'muted_sha256': sha256(quiet), 'pcm_samples': samples,
                         'flags_and_length_preserved': True})
    require(cursor == len(body), 'Unaccounted wave bytes')
    start, end = body_entry['offset'], body_entry['offset'] + len(body)
    result = current[:start] + bytes(muted) + current[end:]
    require(result[:start] == current[:start] and result[end:] == current[end:], 'Nonvoice bytes changed')
    shape = lambda raw: [{k: v for k, v in e.items() if k != 'sha256'} for e in psx_arc(raw)]
    require(shape(current) == shape(result), 'ARC layout changed')
    for e in entries:
        if e['index'] != 13:
            require(entry_data(current, e) == entry_data(result, e), 'Other resource changed')
    return result, {'header': head, 'body': body_entry, 'waves': evidence, 'commands': bank['commands'],
                    'muted_body_sha256': sha256(muted), 'unique_waves_muted': waves,
                    'changed_bytes': sum(a != b for a, b in zip(body, muted)),
                    'nonvoice_bytes_and_layout_identical': True}


def build(activate=False):
    game = PARENT / 'rin_nana.bin'
    require(digest(SOURCE) == SOURCE_SHA and digest(game) == PARENT_SHA, 'Unsupported input BIN hash')
    pointer_path = ROOT / 'projects/ver_rin_nana/current_build.json'
    pointer_bytes = pointer_path.read_bytes()
    pointer = json.loads(pointer_bytes)
    if activate:
        require(pointer['sha256'] == PARENT_SHA and ROOT / pointer['build'] == PARENT, 'Active parent differs')
    protection = json.loads((PARENT / 'preservation.json').read_text('utf8'))
    def protect():
        for q in protection['files']:
            require(digest(ROOT / q['path']) == q['expected_sha256'], 'Protected input changed: ' + q['path'])
    protect()
    archives, original, records = {}, {}, {}
    for path, values in ((game, archives), (SOURCE, original)):
        with path.open('rb') as f:
            reader = DiscReader(f, path.stat().st_size)
            iso = reader.inspect()
            for name in SPECS:
                hits = [r for r in iso['files'] if r['name'] == name + ';1']
                require(len(hits) == 1, 'Ambiguous ISO resource')
                rec = hits[0]
                values[name] = reader.read(rec['lba'], rec['size'])
                if path == game:
                    records[name] = {**rec, 'sha256': sha256(values[name])}
                else:
                    require(all(rec[k] == records[name][k] for k in ('lba', 'size', 'path')), 'ISO location changed')
    changes, checks, negative = {}, {}, []
    for name in SPECS:
        changes[name], checks[name] = mute_archive(archives[name], original[name], name)
        require(mute_archive(archives[name], original[name], name)[0] == changes[name], 'Reproduction differs')
        corrupt = bytearray(archives[name]); corrupt[checks[name]['body']['offset'] + 18] ^= 1
        for label, wrong in [('already_muted', changes[name]), ('modified_wave', bytes(corrupt)),
                             ('truncated', archives[name][:-1])]:
            try:
                mute_archive(wrong, original[name], name)
            except ValueError:
                negative.append(name + ':' + label)
            else:
                raise ValueError('Invalid source accepted: ' + label)
    ff_version = subprocess.run([str(FFMPEG), '-version'], capture_output=True, check=True).stdout.decode().splitlines()[0]
    # Independent decoder: zero-valued output including terminal dummy blocks.
    independent = []
    for name in ('PL00_U.ARC', 'PL01_U.ARC'):
        body = entry_data(changes[name], checks[name]['body'])
        for wave in checks[name]['waves']:
            raw = body[wave['body_offset']:wave['body_offset'] + wave['bytes']]
            pcm = subprocess.run([str(FFMPEG), '-v', 'error', '-f', 'vag', '-i', 'pipe:0',
                                  '-f', 's16le', '-acodec', 'pcm_s16le', 'pipe:1'],
                                 input=vag_container(raw, 22050), capture_output=True, check=True).stdout
            require(len(pcm) >= wave['pcm_samples'] * 2 and not any(pcm), 'Independent decode is not silence')
            independent.append({'archive': name, 'wave_id': wave['wave_id'], 'pcm_bytes': len(pcm), 'peak': 0})
    require(checks['PL00_U.ARC']['muted_body_sha256'] == checks['PL02_U.ARC']['muted_body_sha256'], 'X voice copies differ')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT / 'out/ver_rin_nana' / ('gameplay_voice_mute_' + stamp)
    out.mkdir(exist_ok=False)
    result = write_archive_copies(game, out / 'rin_nana.bin', [(records[n], v) for n, v in changes.items()], PARENT_SHA)
    actual = []
    with game.open('rb') as a, (out / 'rin_nana.bin').open('rb') as b:
        for lba in range(game.stat().st_size // 2352):
            old, new = a.read(2352), b.read(2352)
            require(len(old) == len(new) == 2352, 'Disc truncated')
            if old == new:
                continue
            require(old[:24] == new[:24], 'Sector header changed')
            validate_checks(new)
            hits = [n for n, r in records.items() if r['lba'] <= lba < r['lba'] + (r['size'] + 2047) // 2048]
            require(len(hits) == 1, 'Nonplayer sector changed')
            name = hits[0]; entry = checks[name]['body']; offset = (lba - records[name]['lba']) * 2048
            require(all(entry['offset'] <= offset + i < entry['offset'] + entry['size']
                        for i in range(2048) if old[24 + i] != new[24 + i]), 'Nonvoice payload changed')
            actual.append(lba)
        require(not b.read(1), 'Disc grew')
    require(set(actual) == {r['lba'] for r in result['changed_sectors']}, 'Sector set differs')
    with (out / 'rin_nana.bin').open('rb') as f:
        reader = DiscReader(f, result['size'])
        for name, rec in records.items():
            require(reader.read(rec['lba'], rec['size']) == changes[name], 'BIN readback differs')
    protect()
    require(digest(game) == PARENT_SHA, 'Parent changed')
    for name, data in changes.items():
        (out / ('modified.arc' if name == 'PL00_U.ARC' else name)).write_bytes(data)
    shutil.copyfile(PARENT / 'rin_nana.cue', out / 'rin_nana.cue')
    for folder in PARENT.iterdir():
        if folder.is_dir():
            shutil.copytree(folder, out / folder.name)
    verification = {'archives': checks, 'negative_cases_rejected': negative, 'reproduced_archives': 3,
                    'ffmpeg_version': ff_version, 'independent_decoded_waves': independent,
                    'all_disc_sectors_compared': game.stat().st_size // 2352, 'changed_sectors': len(actual),
                    'all_nonvoice_disc_payload_exact': True, 'edc_ecc_checked': True,
                    'protected_files': len(protection['files']), 'runtime_verified': False}
    manifest = json.loads((PARENT / 'manifest.json').read_text('utf8'))
    manifest.update(kind='rin_nana_gameplay_voice_muted', parent=PARENT.relative_to(ROOT).as_posix(),
                    parent_sha256=PARENT_SHA, modified_bin=result, modified_archive_sha256=digest(out / 'modified.arc'),
                    inherited_manifest=(PARENT / 'manifest.json').relative_to(ROOT).as_posix(),
                    inherited_verification=manifest['verification'], verification=verification,
                    gameplay_voice_muted=['nana', 'rin'], runtime_verified=False,
                    source_script_sha256=digest(Path(__file__)))
    save(out / 'manifest.json', manifest)
    save(out / 'verification.json', verification)
    save(out / 'preservation.json', protection)
    save(out / 'authorization.json', {'user_quote': '그렇게 부탁할게 보이스는  전부 못 구했어',
         'context': '나나와 린 모두 플레이 음성 무음, 기존 효과음·BGM·동영상 음성 보존 제안 수락',
         'source_sha256': SOURCE_SHA, 'parent_sha256': PARENT_SHA, 'scope': 'slot3 gameplay voice waveforms only'})
    if activate:
        require(pointer_path.read_bytes() == pointer_bytes, 'Active pointer changed during build')
        pointer.update(build=out.relative_to(ROOT).as_posix(), cue=(out / 'rin_nana.cue').relative_to(ROOT).as_posix(),
                       sha256=result['sha256'], gameplay_voice_muted=['nana', 'rin'], voice_user_accepted=False,
                       runtime_verified=False, current_session=None,
                       next_scope='Muted gameplay voice user test; Nana armor costumes deferred')
        pointer_path.write_text(json.dumps(pointer, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'build': out.relative_to(ROOT).as_posix(), 'sha256': result['sha256'],
                      'changed_sectors': len(actual), 'negative_cases': len(negative),
                      'independent_waves': len(independent), 'activated': activate}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activate', action='store_true')
    build(parser.parse_args().activate)
