"""로컬 Whisper로 발화 식별의 보조 증거만 만든다. 청취/화자 확인을 대체하지 않는다."""
import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'work/overhaul_20261105/audio'
os.environ.update(HF_HOME=str(ROOT/'work/tools/voice_cache'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
import torch,librosa
from transformers import WhisperProcessor,WhisperForConditionalGeneration
def main():
    processor=WhisperProcessor.from_pretrained('openai/whisper-small',revision='973afd24965f72e36ca33b3055d56a652f456b4d')
    model=WhisperForConditionalGeneration.from_pretrained('openai/whisper-small',revision='973afd24965f72e36ca33b3055d56a652f456b4d',torch_dtype=torch.float16).to('cuda').eval()
    mode=sys.argv[1];rows=[]
    if mode=='title':pairs=[(D/'title/aiden_v2.wav','en'),(D/'title/sohee_v2.wav','ko')]
    elif mode=='npc':pairs=[(D/'npc_samples'/n,'ja') for n in ('jp_ST5_1_1_wave6.wav','jp_ST6_1_1_wave5.wav','jp_ST6_1_1_wave8.wav','jp_ST7_1_1_wave8.wav')]
    elif mode=='prepared':pairs=[(p,'ja') for p in sorted((D/'prepared/previews').glob('*.wav'))]
    else:pairs=[(p,'ja' if '/jp/' in p.as_posix() else 'en') for p in sorted((D/'xa_audition').glob('*/*BOS*.wav'))]
    for p,lang in pairs:
        x,sr=librosa.load(p,sr=16000)
        f=processor(x,sampling_rate=sr,return_tensors='pt',return_attention_mask=True).to('cuda',torch.float16)
        with torch.inference_mode():ids=model.generate(**f,language=lang,task='transcribe',max_new_tokens=150)
        row=dict(file=p.relative_to(ROOT).as_posix(),language=lang,text=processor.batch_decode(ids,skip_special_tokens=True)[0])
        rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    (D/(mode+'_asr.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
