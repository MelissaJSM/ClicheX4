"""로컬 변환 PCM을 원래 길이의 PS1 음성 슬롯에 맞추고 독립 디코더로 검사한다."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.psx_spu_audio import decode_spu, encode_fixed_oneshot, vag_container


def main(args):
    import numpy as np
    import soundfile as sf
    import librosa
    import imageio_ffmpeg
    from scipy.ndimage import uniform_filter1d
    from scipy.signal import butter, sosfiltfilt
    root = ROOT / 'work/ver_buki_riko/voice_production/v1'
    candidate = (root / args.candidate).resolve()
    output = (root / args.output).resolve()
    if candidate.parent != root.resolve() or output.parent != root.resolve() or output.exists():
        raise ValueError('Expected a local candidate and fresh output')
    source = json.loads((root / 'original/manifest.local.json').read_text('utf-8'))
    generated = json.loads((candidate / 'manifest.local.json').read_text('utf-8'))
    output.mkdir()
    bank = bytearray((root / 'original/source_bank.adpcm').read_bytes())
    rows = []
    for info in source['commands']:
        if args.ids and info['sound_id'] not in set(map(int,args.ids.split(','))):
            continue
        record = next(x for x in generated['records'] if x['sound_id'] == info['sound_id'] and x['reference'] == args.reference)
        data, rate = sf.read(candidate / record['file'], dtype='float32')
        if rate not in (22050,44100) or not np.isfinite(data).all() or np.any(np.abs(data) >= 0.9999):
            raise ValueError('Invalid or clipped synthesis: ' + record['file'])
        late_artifact_energy = 0.0
        if info['sound_id'] == 9 and candidate.name == 'full_v1':
            # Inspected v1 model output has a separate burst at ~0.85 s in
            # appended input silence, after the cry has ended near 0.60 s.
            # Require the intervening quiet gap; do not shorten a continuous cry.
            if np.sqrt(np.mean(data[round(.65*rate):round(.75*rate)]**2)) > .003:
                raise ValueError('Expected quiet gap before generated boundary artifact')
            tail = round(.75*rate)
            late_artifact_energy = float(np.sum(data[tail:]**2)/np.sum(data**2))
            data = data.copy()
            data[tail:] = 0
        original, native_rate = sf.read(root / 'original' / (info['name'] + '.wav'), dtype='float32')
        guide = librosa.resample(original, orig_sr=native_rate, target_sr=rate)
        # Align broad energy envelopes within 80 ms; never correlate voice waveform phase.
        width = round(rate * .012)
        a = np.sqrt(uniform_filter1d(guide ** 2, width))
        b = np.sqrt(uniform_filter1d(data ** 2, width))
        count = len(guide)
        options = []
        for offset in range(round(.12 * rate), round(.28 * rate) + 1, 22):
            part = np.pad(b[offset:offset+count], (0, max(0, offset+count-len(b))))
            score = float(np.dot(a, part) / max(np.linalg.norm(a)*np.linalg.norm(part), 1e-9))
            energy = float(np.sum(data[offset:offset+count]**2) / max(np.sum(data**2), 1e-9))
            if energy >= .97:
                options.append((score, offset))
        if not options:
            raise ValueError('Generated voice exceeds original slot: ' + info['name'])
        correlation, start = max(options)
        cropped = data[start:start+count]
        retained = float(np.sum(cropped ** 2) / max(np.sum(data ** 2), 1e-9))
        if retained < .97 or correlation < .45:
            raise ValueError(f'Alignment requires review: {info["name"]}, energy={retained}, correlation={correlation}')
        cropped = np.pad(cropped, (0, count-len(cropped)))
        pcm = librosa.resample(cropped, orig_sr=rate, target_sr=native_rate)
        pcm = np.pad(pcm[:len(original)], (0, max(0, len(original)-len(pcm))))
        # The fixed ~11 kHz bank has a 5.5 kHz Nyquist limit. Leave room for
        # 4-bit ADPCM by suppressing the vocoder's highest-frequency noise.
        resampled = pcm.copy()
        pcm = sosfiltfilt(butter(4, 4000, fs=native_rate, output='sos'), resampled)
        pcm -= pcm.mean()
        pcm[:28] = 0
        fade = max(8, round(.004*native_rate))
        pcm[28:28+fade] *= np.linspace(0, 1, fade)
        pcm[-fade:] *= np.linspace(1, 0, fade)
        gain = min(float(np.sqrt(np.mean(original**2))/max(np.sqrt(np.mean(pcm**2)), 1e-9))*10**(args.gain_db/20), .90/max(float(np.max(np.abs(pcm))), 1e-9))
        pcm *= gain
        quantized = np.rint(pcm*32767).astype(np.int16)
        template = (root / 'original' / (info['name'] + '.adpcm')).read_bytes()
        encoded, quality = encode_fixed_oneshot(quantized, template)
        cutoff = 4000
        if quality['snr_db'] < 19:
            cutoff = 3500
            pcm = sosfiltfilt(butter(4, cutoff, fs=native_rate, output='sos'), resampled)
            pcm -= pcm.mean(); pcm[:28] = 0
            pcm[28:28+fade] *= np.linspace(0, 1, fade)
            pcm[-fade:] *= np.linspace(1, 0, fade)
            gain = min(float(np.sqrt(np.mean(original**2))/max(np.sqrt(np.mean(pcm**2)), 1e-9))*10**(args.gain_db/20), .90/max(float(np.max(np.abs(pcm))), 1e-9))
            pcm *= gain
            quantized = np.rint(pcm*32767).astype(np.int16)
            encoded, quality = encode_fixed_oneshot(quantized, template)
        decoded = np.asarray(decode_spu(encoded).pcm, dtype=np.int16)
        # Engineering rejection floor, not a perceptual quality approval.
        if quality['snr_db'] < 19 or np.max(np.abs(decoded.astype(np.int32))) >= 32767:
            raise ValueError(f'ADPCM requires review: {info["name"]}, {quality}, peak={np.max(np.abs(decoded.astype(np.int32)))}')
        stem = output / info['name']
        sf.write(str(stem)+ '_pcm.wav', quantized, native_rate, subtype='PCM_16')
        sf.write(str(stem)+ '.wav', decoded, native_rate, subtype='PCM_16')
        Path(str(stem)+'.adpcm').write_bytes(encoded)
        Path(str(stem)+'.vag').write_bytes(vag_container(encoded, native_rate, info['name']))
        independent = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v','error','-i',str(stem)+'.vag',
            '-f','s16le','-acodec','pcm_s16le','-'], capture_output=True, check=True)
        other = np.frombuffer(independent.stdout, dtype='<i2')
        if len(other) != len(decoded)+28:
            raise ValueError('Unexpected independent decoder length')
        error = other[:len(decoded)].astype(np.float64)-decoded
        if np.max(np.abs(error)) > 128:
            raise ValueError('Independent decoder disagreement')
        offset = info['body_offset']
        bank[offset:offset+info['bytes']] = encoded
        row = {**quality, 'sound_id': info['sound_id'], 'wave_id': info['wave_id'], 'name':info['name'],
            'sha256':hashlib.sha256(encoded).hexdigest(), 'sample_rate':native_rate,
            'candidate':record['file'], 'crop_start_seconds':start/rate, 'envelope_correlation':correlation,
            'retained_energy':retained, 'gain':gain, 'peak':float(np.max(np.abs(decoded.astype(np.float64)))/32768),
            'discarded_late_padding_artifact_energy':late_artifact_energy,
            'lowpass_hz':cutoff, 'gain_db_requested':args.gain_db,
            'ffmpeg_max_abs_error_lsb':float(np.max(np.abs(error))), 'ffmpeg_rms_error_lsb':float(np.sqrt(np.mean(error**2))),
            'runtime_trigger_verified':False, 'human_quality_accepted':False}
        rows.append(row)
        print(json.dumps(row), flush=True)
    body = bytes(bank)
    (output / 'voice_bank.adpcm').write_bytes(body)
    manifest = {'candidate':str(candidate), 'candidate_manifest_sha256':hashlib.sha256((candidate/'manifest.local.json').read_bytes()).hexdigest(),
        'source_manifest':str(root/'original/manifest.local.json'), 'body_sha256':hashlib.sha256(body).hexdigest(),
        'body_bytes':len(body), 'reference':args.reference, 'commands':rows, 'alignment': 'energy envelope lag only; no time stretching',
        'lowpass_choices_hz':[4000,3500], 'ffmpeg_version':'7.1', 'decoder_note':'Different predictor rounding; terminal dummy block is not audible after end+mute.'}
    (output/'manifest.local.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', default='full_v1')
    p.add_argument('--reference', default='b')
    p.add_argument('--output', default='packed_v1')
    p.add_argument('--ids',default='')
    p.add_argument('--gain-db',type=float,default=0.0)
    main(p.parse_args())
