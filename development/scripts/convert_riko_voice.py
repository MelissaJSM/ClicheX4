"""고정된 Seed-VC v2로 Riko 보이스 후보를 로컬 생성한다. 게임에 쓰지 않는다."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from riko_voice_environment import configure, load_v2, ROOT, VOICE_ROOT


def main(args):
    configure()
    import torch
    import librosa
    import numpy as np
    import soundfile as sf
    import imageio_ffmpeg
    from pydub import AudioSegment
    AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
    output = (VOICE_ROOT / args.name).resolve()
    if output.parent != VOICE_ROOT.resolve() or output.exists():
        raise ValueError("Expected a fresh candidate directory")
    output.mkdir()
    reference_path = ROOT / "character/ver_buki_riko/riko(zero)_voice.wav"
    if hashlib.sha256(reference_path.read_bytes()).hexdigest() != "d0ba1fde6fddb1440fb021dd2bf2c504ee3d0f2039e12d0dece1dd0fef23da46":
        raise ValueError("Reference WAV changed")
    reference, sr = librosa.load(reference_path, sr=22050, mono=True)
    spans = {"a": (1.0, 12.0), "b": (23.0, 34.0), "c": (35.0, 47.0)}
    prompts = {}
    for label in args.references.split(","):
        start, end = spans[label]
        data = reference[round(start * sr):round(end * sr)]
        # Only remove DC and adjust uniform gain; no aggressive stem denoising.
        data = data - data.mean()
        gain = min(0.15 / max(np.sqrt(np.mean(data ** 2)), 1e-6), 0.94 / max(np.max(np.abs(data)), 1e-6))
        path = output / ("reference_" + label + ".wav")
        sf.write(path, data * gain, sr, subtype="PCM_16")
        prompts[label] = {"path": str(path), "original_span_seconds": [start, end], "gain": float(gain)}
    print("Loading pinned Seed-VC v2", flush=True)
    wrapper = load_v2()
    # Reduce log-mel amplitude before the vocoder's hard output clamp.
    # Uniform mel scaling avoids throwing away over-range waveform peaks.
    if not 0 < args.vocoder_gain <= 1:
        raise ValueError("Vocoder gain must be in (0, 1]")
    if args.vocoder_gain != 1:
        wrapper.vocoder.register_forward_pre_hook(
            lambda module, inputs: (inputs[0] + math.log(args.vocoder_gain),))
    manifest = json.loads((VOICE_ROOT / "original/manifest.local.json").read_text("utf-8"))
    records = []
    for voice_id in [int(x) for x in args.ids.split(",")]:
        info = next(x for x in manifest["commands"] if x["sound_id"] == voice_id)
        source, _ = librosa.load(VOICE_ROOT / "original" / (info["name"] + ".wav"), sr=sr)
        if args.source_shift:
            source = librosa.effects.pitch_shift(source, sr=sr, n_steps=args.source_shift)
        source = np.pad(source, (round(0.20 * sr), round(0.25 * sr)))
        source_path = output / (info["name"] + "_source_padded.wav")
        sf.write(source_path, source, sr, subtype="PCM_16")
        for label, prompt in prompts.items():
            seed = 20261026 + voice_id
            random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
            begin = time.monotonic()
            generator = wrapper.convert_voice_with_streaming(
                source_audio_path=str(source_path), target_audio_path=prompt["path"],
                diffusion_steps=args.steps, length_adjust=1.0,
                intelligebility_cfg_rate=args.intelligibility, similarity_cfg_rate=args.similarity,
                convert_style=False, device=torch.device("cuda"), dtype=torch.float16, stream_output=True)
            generated = None
            # The upstream streaming path yields final lossless PCM beside MP3 preview bytes.
            while True:
                try:
                    item = next(generator)
                    if item is not None and isinstance(item, tuple) and item[1] is not None:
                        generated = item[1]
                except StopIteration as end:
                    if end.value is not None:
                        generated = end.value
                    break
            if isinstance(generated, tuple):
                out_rate, generated = generated
            else:
                out_rate = sr
            if generated is None:
                raise ValueError("Model returned no waveform")
            generated = np.asarray(generated).reshape(-1)
            if not np.isfinite(generated).all() or np.max(np.abs(generated)) < 0.001:
                raise ValueError("Invalid model waveform")
            name = info["name"] + "_ref" + label + ".wav"
            sf.write(output / name, generated, out_rate, subtype="FLOAT")
            record = {"sound_id": voice_id, "reference": label, "file": name,
                      "seed": seed, "seconds": time.monotonic() - begin,
                      "model_samples": len(generated), "sample_rate": out_rate,
                      "source_padding_seconds": [0.20, 0.25], "source_pitch_shift": args.source_shift,
                      "peak": float(np.max(np.abs(generated))), "rms": float(np.sqrt(np.mean(generated ** 2)))}
            records.append(record)
            print(json.dumps(record), flush=True)
            (output / "manifest.local.json").write_text(json.dumps({"parameters": vars(args), "prompts": prompts,
                "records": records, "human_quality_accepted": False}, indent=2), encoding="utf-8")
    print("Candidate conversion complete", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--name", required=True)
    p.add_argument("--ids", default="3,11,12")
    p.add_argument("--references", default="a,b,c")
    p.add_argument("--steps", type=int, default=50)
    p.add_argument("--intelligibility", type=float, default=0.5)
    p.add_argument("--similarity", type=float, default=0.9)
    p.add_argument("--source-shift", type=float, default=0.0)
    p.add_argument("--vocoder-gain", type=float, default=0.5)
    main(p.parse_args())
