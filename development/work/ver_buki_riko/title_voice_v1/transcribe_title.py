import os,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
os.environ['HF_HOME']=str(ROOT/'work/tools/voice_cache');os.environ['HF_HUB_OFFLINE']='1'
import torch,librosa
from transformers import WhisperProcessor,WhisperForConditionalGeneration
processor=WhisperProcessor.from_pretrained('openai/whisper-small',revision='973afd24965f72e36ca33b3055d56a652f456b4d')
model=WhisperForConditionalGeneration.from_pretrained('openai/whisper-small',revision='973afd24965f72e36ca33b3055d56a652f456b4d',torch_dtype=torch.float16).to('cuda').eval()
for name in sys.argv[1:] or ['original_title.wav']:
    x,sr=librosa.load(D/name,sr=16000)
    f=processor(x,sampling_rate=sr,return_tensors='pt',return_attention_mask=True).to('cuda',torch.float16)
    with torch.inference_mode():ids=model.generate(**f,language='ko' if 'korean' in name else 'en',task='transcribe',max_new_tokens=100,return_timestamps=True,return_token_timestamps=True)
    text=processor.batch_decode(ids['sequences'],decode_with_timestamps=True,skip_special_tokens=False)[0]
    tokens=[(processor.tokenizer.decode([int(t)]),float(st)) for t,st in zip(ids['sequences'][0],ids['token_timestamps'][0])]
    print(json.dumps({'file':name,'text':text,'tokens':tokens},ensure_ascii=True),flush=True)
