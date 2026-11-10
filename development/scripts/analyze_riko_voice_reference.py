"""제공 음성을 로컬 Whisper로 전사해 참고 구간 선택을 돕는다. 청취 판정이 아니다."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from riko_voice_environment import configure, model_revisions, ROOT, VOICE_ROOT


def main():
    configure()
    import torch
    import librosa
    import numpy as np
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    revision = model_revisions()["openai/whisper-small"]["revision"]
    processor = WhisperProcessor.from_pretrained("openai/whisper-small", revision=revision)
    model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small", revision=revision,
                                                            torch_dtype=torch.float16).to("cuda")
    signal, rate = librosa.load(ROOT / "character/ver_buki_riko/riko(zero)_voice.wav", sr=16000)
    records = []
    for start in range(0, len(signal), 16000 * 8):
        piece = signal[start:start + 16000 * 8]
        inputs = processor(piece, sampling_rate=16000, return_tensors="pt").input_features.to("cuda", dtype=torch.float16)
        with torch.inference_mode():
            result = model.generate(inputs, language="ko", task="transcribe", max_new_tokens=150)
        text = processor.batch_decode(result, skip_special_tokens=True)[0]
        item = {"start_seconds": start / 16000, "end_seconds": (start + len(piece)) / 16000,
                "automatic_transcript_unverified": text,
                "rms": float(np.sqrt(np.mean(piece ** 2)))}
        records.append(item)
        print(json.dumps(item, ensure_ascii=True), flush=True)
    report = {"reference": "character/ver_buki_riko/riko(zero)_voice.wav", "model_revision": revision,
              "records": records, "listening_completed": False, "human_transcript_verified": False}
    (VOICE_ROOT / "reference_asr.local.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
