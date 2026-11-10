"""JP/US 보스 음향 차이의 로컬 전사 보조 증거. 효과음·감탄사 오인 가능."""
import json
import os
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work/boss_voice_restore_20261105'
os.environ.update(HF_HOME=str(ROOT / 'work/tools/voice_cache'), HF_HUB_OFFLINE='1',
                  TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
import librosa
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extra', action='store_true', help='US bank에 남아 있지만 재생 대상이 바뀐 JP 파형')
    parser.add_argument('--restored', action='store_true', help='최종 복구한 전투 음성 12개')
    args = parser.parse_args()
    if args.extra and args.restored:
        parser.error('Choose one source set')
    revision = '973afd24965f72e36ca33b3055d56a652f456b4d'
    processor = WhisperProcessor.from_pretrained('openai/whisper-small', revision=revision)
    model = WhisperForConditionalGeneration.from_pretrained(
        'openai/whisper-small', revision=revision, torch_dtype=torch.float16).to('cuda').eval()
    if args.restored:
        pairs = json.loads((WORK / 'assets/prepared_combat_v1/audition_manifest.json').read_text('utf8'))['pairs']
        data = {'rows': [{'source': 'restored', 'sha256': r['restored']['sha256'],
                           'native_variants': [r['restored']],
                           'occurrences': [{'path': f"/ARC/ST{r['stage']}_1_1.ARC;1"}]}
                          for r in pairs]}
    else:
        data = json.loads((WORK / ('assets/extra_native_manifest.json' if args.extra else
                                  'assets/asr_native_manifest.json')).read_text('utf8'))
    output = WORK / 'asr'
    output.mkdir(exist_ok=True)
    results = []
    for i, row in enumerate(data['rows']):
        variant = row['native_variants'][0]
        path = ROOT / variant['wav_path']
        x, sr = librosa.load(path, sr=16000)
        features = processor(x, sampling_rate=sr, return_tensors='pt',
                             return_attention_mask=True).to('cuda', torch.float16)
        # JP/US short combat samples are mostly Japanese even in the US edition.
        with torch.inference_mode():
            ids = model.generate(**features, language='ja', task='transcribe', max_new_tokens=100)
        result = {'source': row['source'], 'wave_sha256': row['sha256'],
                  'file': variant['wav_path'], 'seconds': variant['seconds'],
                  'text': processor.batch_decode(ids, skip_special_tokens=True)[0],
                  'occurrences': sorted({o['path'] for o in row['occurrences']})}
        results.append(result)
        print(json.dumps({'index': i + 1, 'total': len(data['rows']), **result}, ensure_ascii=True), flush=True)
        filename = ('restored_wave_transcripts.json' if args.restored else
                    'extra_wave_transcripts.json' if args.extra else 'native_wave_transcripts.json')
        (output / filename).write_text(json.dumps({
            'model': 'openai/whisper-small', 'revision': revision, 'offline': True,
            'native_rates_verified': True, 'listening_verified': False,
            'limitations': 'ASR is auxiliary only; sound effects and grunts may hallucinate text. No ADSR/mix simulation.',
            'completed': i + 1 == len(data['rows']), 'rows': results}, ensure_ascii=False, indent=2), 'utf8')


if __name__ == '__main__':
    main()
