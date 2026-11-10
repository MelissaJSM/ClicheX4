"""승인된 그래픽 BIN 위에 길이/헤더가 동일한 플레이어 음성만 적용한다."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_riko_voice import SOURCE_HASH, BASE_HASH, REFERENCE_HASH
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from scripts.project import digest, write_json
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks
from src.psx_spu_audio import decode_spu, validate_oneshot_template


def replace_voice_body(arc, body, source):
    if sha256(arc) != source['parent_arc_sha256']:
        raise ValueError('Unsupported parent archive')
    entry = source['voice_body_entry']
    if len(body) != entry['size'] or sha256(body) == entry['sha256']:
        raise ValueError('Expected changed, same-size voice bank')
    layout = psx_arc(arc)
    if layout[13] != entry or layout[12] != source['voice_header_entry']:
        raise ValueError('Voice bank layout differs')
    occupied = set()
    for command in source['commands']:
        start, size = command['body_offset'], command['bytes']
        region = set(range(start, start+size))
        if occupied & region or start < 0 or start+size > len(body):
            raise ValueError('Overlapping/invalid voice slot')
        occupied.update(region)
        old = arc[entry['offset']+start:entry['offset']+start+size]
        new = body[start:start+size]
        validate_oneshot_template(new)
        if old[:16] != new[:16] or old[-16:] != new[-16:] or old[1::16] != new[1::16]:
            raise ValueError('Playback flags or reserved blocks changed')
    if occupied != set(range(len(body))):
        raise ValueError('Voice bank has unaccounted bytes')
    result = bytearray(arc)
    result[entry['offset']:entry['offset']+entry['size']] = body
    return bytes(result)


def build(packed):
    packed = packed.resolve()
    if not packed.is_relative_to(ROOT/'work/ver_buki_riko/voice_production'):
        raise ValueError('Expected local production package')
    source = json.loads((ROOT/'work/ver_buki_riko/voice_production/v1/original/manifest.local.json').read_text('utf-8'))
    package = json.loads((packed/'manifest.local.json').read_text('utf-8'))
    body = (packed/'voice_bank.adpcm').read_bytes()
    if len(package['commands']) != 13 or {r['sound_id'] for r in package['commands']} != set(range(13)) or sha256(body) != package['body_sha256']:
        raise ValueError('Incomplete or changed voice package')
    parent = ROOT/source['parent_build']
    game = parent/'riko_motion.bin'
    for path, expected in ((ROOT/'MegaMan X4.bin', SOURCE_HASH), (game, BASE_HASH),
                           (ROOT/'character/ver_buki_riko/riko(zero)_voice.wav', REFERENCE_HASH)):
        if digest(path) != expected:
            raise ValueError('Input hash mismatch')
    rec = dict(source['arc_record'], sha256=source['parent_arc_sha256'])
    with game.open('rb') as stream:
        original = DiscReader(stream, game.stat().st_size).read(rec['lba'], rec['size'])
    replacement = replace_voice_body(original, body, source)
    muted = package.get('kind') == 'riko_gameplay_voice_muted_v1'
    if muted:
        for command in source['commands']:
            start, size = command['body_offset'], command['bytes']
            if any(decode_spu(body[start:start+size]).pcm):
                raise ValueError('Mute package contains audible samples')
    out = ROOT/'out/ver_buki_riko'/('riko_voice_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir()
    result = write_archive_copy(game, out/'riko_motion.bin', rec, replacement, BASE_HASH)
    (out/'modified.arc').write_bytes(replacement)
    (out/'riko_motion.cue').write_bytes((parent/'riko_motion.cue').read_bytes())
    manifest = json.loads((parent/'manifest.json').read_text('utf-8'))
    manifest.update(kind='riko_gameplay_voice_muted_v1' if muted else 'riko_gameplay_voice_v1', modified_bin=result, modified_archive_sha256=sha256(replacement),
        modification_base_sha256=BASE_HASH,
        voice={'parent_build':str(parent), 'parent_sha256':BASE_HASH, 'package':str(packed),
            'package_sha256':digest(packed/'manifest.local.json'), 'body_sha256':sha256(body),
            'sound_ids':list(range(13)), 'vab_header_preserved':True, 'runtime_verified':False,
            'human_quality_accepted':False, 'fmv_xa_story_unchanged':True})
    if muted:
        manifest['voice'].update(mode='muted', all_13_decoded_samples_silent=True,
                                 user_playtest_pending=True)
    write_json(out/'manifest.json', manifest)
    # Compare every raw sector, and restrict every changed payload byte to the voice body.
    changed = []
    entry = source['voice_body_entry']
    with game.open('rb') as a, (out/'riko_motion.bin').open('rb') as b:
        lba = 0
        while True:
            old, new = a.read(2352*256), b.read(2352*256)
            if len(old) != len(new): raise ValueError('BIN length changed')
            if not old: break
            if old != new:
                for offset in range(0,len(old),2352):
                    x,y = old[offset:offset+2352], new[offset:offset+2352]
                    if x == y: continue
                    sector = lba+offset//2352
                    validate_checks(y)
                    if x[:24] != y[:24]: raise ValueError('Raw sector header changed')
                    for j in range(24,2072):
                        if x[j] != y[j]:
                            arc_offset = (sector-rec['lba'])*2048+j-24
                            if not entry['offset'] <= arc_offset < entry['offset']+entry['size']:
                                raise ValueError('Non-voice game byte changed')
                    changed.append(sector)
            lba += len(old)//2352
    if set(changed) != {s['lba'] for s in result['changed_sectors']}:
        raise ValueError('Unexpected changed sector set')
    with (out/'riko_motion.bin').open('rb') as stream:
        if DiscReader(stream, game.stat().st_size).read(rec['lba'],rec['size']) != replacement:
            raise ValueError('Archive readback mismatch')
    write_json(out/'voice_validation.local.json', {'all_raw_sectors_compared':lba, 'changed_sectors':changed,
        'only_voice_payload_and_edc_ecc_changed':True, 'header_timing_pitch_pan_preserved':True,
        'graphics_exe_xa_fmv_bgm_other_sfx_unchanged':True, 'input_sha256':BASE_HASH, 'output_sha256':result['sha256']})
    print(json.dumps({'output':str(out), 'sha256':result['sha256'], 'changed_sectors':len(changed)}))
    return out


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packed',type=Path,required=True)
    build(p.parse_args().packed)
