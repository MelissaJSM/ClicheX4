"""13개 플레이 음성을 무음화한 별도 BIN을 제작한다. 효과음·BGM·영상은 보존한다."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_riko_voice import build, replace_voice_body
from scripts.discover_inputs import DiscReader, sha256
from scripts.prepare_riko_voice import BASE_HASH, SOURCE_HASH, REFERENCE_HASH, save_wav
from scripts.project import digest, write_json
from src.psx_spu_audio import decode_spu, silence_fixed_oneshot, vag_container


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activate', action='store_true', help='검증 후 현재 빌드 포인터 갱신')
    args = parser.parse_args()
    production = ROOT / 'work/ver_buki_riko/voice_production'
    original = production / 'v1/original'
    source = json.loads((original / 'manifest.local.json').read_text('utf-8'))
    parent = ROOT / source['parent_build']
    game = parent / 'riko_motion.bin'
    protected = ((ROOT / 'MegaMan X4.bin', SOURCE_HASH), (game, BASE_HASH),
                 (ROOT / 'character/ver_buki_riko/riko(zero)_voice.wav', REFERENCE_HASH))
    for path, expected in protected:
        if digest(path) != expected:
            raise ValueError('Protected input hash mismatch')
    source_body = (original / 'source_bank.adpcm').read_bytes()
    if sha256(source_body) != source['voice_body_entry']['sha256']:
        raise ValueError('Original voice bank hash mismatch')
    if len(source['commands']) != 13 or {r['sound_id'] for r in source['commands']} != set(range(13)):
        raise ValueError('Expected all thirteen original voice slots')
    rec = source['arc_record']
    with game.open('rb') as stream:
        arc = DiscReader(stream, game.stat().st_size).read(rec['lba'], rec['size'])
    body = bytearray(source_body)
    records, samples = [], []
    for command in source['commands']:
        offset, size = command['body_offset'], command['bytes']
        raw = source_body[offset:offset + size]
        if sha256(raw) != command['raw_sha256']:
            raise ValueError('Original sample hash mismatch')
        muted = silence_fixed_oneshot(raw)
        decoded = decode_spu(muted)
        body[offset:offset + size] = muted
        records.append({**command, 'raw_sha256': sha256(muted),
                        'original_raw_sha256': sha256(raw), 'mode': 'muted',
                        'decoded_peak_lsb': max(abs(x) for x in decoded.pcm),
                        'pcm_samples': len(decoded.pcm), 'flags_preserved': True,
                        'reserved_blocks_preserved': True})
        samples.append((command['name'], command['wav_sample_rate'], muted, decoded.pcm))
    # Validate the complete replacement before writing any package or game output.
    replace_voice_body(arc, bytes(body), source)
    output = production / ('muted_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    if not output.resolve().is_relative_to(production.resolve()):
        raise ValueError('Output must stay in the local production directory')
    output.mkdir(exist_ok=False)
    for name, rate, muted, pcm in samples:
        (output / (name + '.adpcm')).write_bytes(muted)
        (output / (name + '.vag')).write_bytes(vag_container(muted, rate, name))
        save_wav(output / (name + '.wav'), pcm, rate)
    (output / 'voice_bank.adpcm').write_bytes(body)
    write_json(output / 'manifest.local.json', {
        'kind': 'riko_gameplay_voice_muted_v1', 'commands': records,
        'body_sha256': sha256(body), 'original_body_sha256': sha256(source_body),
        'parent_sha256': BASE_HASH, 'only_gameplay_player_voice_muted': True,
        'runtime_verified': False, 'user_playtest_pending': True})
    built = build(output)
    manifest = json.loads((built / 'manifest.json').read_text('utf-8'))
    for path, expected in protected:
        if digest(path) != expected:
            raise ValueError('Protected input changed during build')
    if args.activate:
        pointer = ROOT / 'projects/ver_buki_riko/current_build.json'
        before = pointer.read_bytes()
        previous = json.loads(before)
        snapshot = output / 'previous_current_build.json'
        snapshot.write_bytes(before)
        updated = dict(previous)
        updated.update(kind=manifest['kind'], build=built.relative_to(ROOT).as_posix(),
            cue=(built / 'riko_motion.cue').relative_to(ROOT).as_posix(),
            bin_sha256=manifest['modified_bin']['sha256'], source_sha256=SOURCE_HASH,
            previous_build=previous['build'], previous_bin_sha256=previous['bin_sha256'],
            previous_pointer_snapshot=snapshot.relative_to(ROOT).as_posix(),
            voice_package=output.relative_to(ROOT).as_posix(), voice_mode='muted',
            voice_quality_user_review_pending=False, voice_mute_user_playtest_pending=True,
            voice_runtime_verified=False, voice_manual_tuning_active=False,
            session=None, session_closed=True, agent_loaded_save_state=False,
            session_state_at_last_observation=None, session_state_evidence=None,
            report='docs/RIKO_VOICE_MUTE.md',
            next_task='플레이 음성 무음·효과음 유지 사용자 확인')
        if pointer.read_bytes() != before:
            raise ValueError('Current build pointer changed; refusing activation')
        temporary = pointer.with_suffix('.mute.tmp')
        with temporary.open('x', encoding='utf-8') as stream:
            json.dump(updated, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        temporary.replace(pointer)
    print(json.dumps({'package': str(output.relative_to(ROOT)),
                      'build': str(built.relative_to(ROOT)), 'activated': args.activate}))


if __name__ == '__main__':
    main()
