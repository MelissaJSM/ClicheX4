import os,sys,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
os.environ['HF_HOME']=str(ROOT/'work/tools/voice_cache')
os.environ['HF_HUB_OFFLINE']='1'
import torch,librosa
from transformers import WhisperProcessor,WhisperForConditionalGeneration
D=Path(__file__).parent
model_id='openai/whisper-small';rev='973afd24965f72e36ca33b3055d56a652f456b4d'
processor=WhisperProcessor.from_pretrained(model_id,revision=rev)
model=WhisperForConditionalGeneration.from_pretrained(model_id,revision=rev,torch_dtype=torch.float16).to('cuda').eval()
ff=ROOT/'work/tools/voice_env/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
results=[]
for num,n in [(2,8),(3,8),(4,5),(5,3)]:
    src=D/f'BGM{num}{"_U" if num==5 else ""}.XA'
    for ch in range(n):
        p=D/f'bgm{num}_ch{ch}.wav'
        if not p.exists():subprocess.run([str(ff),'-hide_banner','-loglevel','error','-i',str(src),'-t','9','-map',f'0:a:{ch}',str(p)],check=True)
for p in sorted(D.glob('bgm[2345]*.wav')):
    x,sr=librosa.load(p,sr=16000)
    f=processor(x,sampling_rate=sr,return_tensors='pt').input_features.to('cuda',torch.float16)
    with torch.inference_mode():ids=model.generate(f,language='en',task='transcribe',max_new_tokens=64)
    text=processor.batch_decode(ids,skip_special_tokens=True)[0]
    row={'file':p.name,'text':text};results.append(row);print(json.dumps(row),flush=True)
(D/'probe_transcription.json').write_text(json.dumps(results,indent=2),'utf-8')
