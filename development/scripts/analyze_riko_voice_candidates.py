"""음성 후보의 신호·참고 화자 유사도 보조 지표. 청취 품질 점수가 아니다."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from riko_voice_environment import configure, load_v2, VOICE_ROOT


def main(args):
    configure()
    import torch
    import librosa
    import numpy as np
    import soundfile as sf
    wrapper = load_v2()
    reference_dir = VOICE_ROOT / args.candidate
    reference_embeddings = []
    def embedding(data, rate):
        wave = librosa.resample(data.astype(np.float32), orig_sr=rate, target_sr=16000)
        with torch.inference_mode():
            value = wrapper.compute_style(torch.tensor(wave)[None].to("cuda")).float()
        return torch.nn.functional.normalize(value, dim=-1)
    def metrics(data, rate):
        rms = librosa.feature.rms(y=data, frame_length=512, hop_length=128)[0]
        f0 = librosa.yin(data, sr=rate, fmin=65, fmax=700, frame_length=2048, hop_length=128)
        active = rms > max(0.015, float(rms.max()) * 0.12)
        pitched = f0[:len(active)][active[:len(f0)]]
        return {"rms": float(np.sqrt(np.mean(data ** 2))), "peak": float(np.max(np.abs(data))),
                "full_scale_fraction": float(np.mean(np.abs(data) >= 0.9999)),
                "yin_median_hz_active_frames": float(np.median(pitched)) if len(pitched) else None,
                "yin_is_not_voicing_or_identity_verification": True}
    reference_metrics = {}
    for path in sorted(reference_dir.glob("reference_*.wav")):
        data, rate = sf.read(path, dtype="float32")
        reference_embeddings.append(embedding(data, rate))
        reference_metrics[path.name] = metrics(data, rate)
    ref_embedding = torch.nn.functional.normalize(torch.stack(reference_embeddings).mean(dim=0), dim=-1)
    original = json.loads((VOICE_ROOT / "original/manifest.local.json").read_text("utf-8"))
    rows = []
    for folder_name in args.folders.split(","):
        folder = VOICE_ROOT / folder_name
        manifest = json.loads((folder / "manifest.local.json").read_text("utf-8"))
        for record in manifest["records"]:
            data, rate = sf.read(folder / record["file"], dtype="float32")
            info = next(x for x in original["commands"] if x["sound_id"] == record["sound_id"])
            start, end = round(0.2 * rate), round((0.2 + info["duration_seconds"]) * rate)
            cropped = data[start:end]
            emb = embedding(cropped, rate)
            row = {"candidate": folder_name, "file": record["file"], "sound_id": record["sound_id"],
                   "reference_cosine_diagnostic": float((emb * ref_embedding).sum()), **metrics(cropped, rate)}
            rows.append(row)
            print(json.dumps(row), flush=True)
    for info in original["commands"]:
        if info["sound_id"] not in [3, 11, 12]:
            continue
        data, rate = sf.read(VOICE_ROOT / "original" / (info["name"] + ".wav"), dtype="float32")
        row = {"candidate": "original", "sound_id": info["sound_id"],
               "reference_cosine_diagnostic": float((embedding(data, rate) * ref_embedding).sum()), **metrics(data, rate)}
        rows.append(row)
        print(json.dumps(row), flush=True)
    output = {"reference_metrics": reference_metrics, "rows": rows,
              "limitations": "Embedding and YIN are diagnostics, not human judgement or an acceptance score."}
    target = VOICE_ROOT / args.output
    if target.exists():
        raise ValueError("Analysis output already exists")
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", default="pilot_v2b")
    p.add_argument("--folders", default="pilot_v2b")
    p.add_argument("--output", default="pilot_diagnostics.local.json")
    main(p.parse_args())
