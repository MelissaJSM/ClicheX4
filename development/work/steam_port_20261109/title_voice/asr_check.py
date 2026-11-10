from pathlib import Path
import os,json
R=Path(__file__).resolve().parents[3]
os.environ.update(HF_HOME=str(R/'work/tools/voice_cache'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
import numpy as np,torch
from scipy.signal import resample_poly
from transformers import WhisperProcessor,WhisperForConditionalGeneration
D=Path(__file__).parent
rev='973afd24965f72e36ca33b3055d56a652f456b4d'
p=WhisperProcessor.from_pretrained('openai/whisper-small',revision=rev)
m=WhisperForConditionalGeneration.from_pretrained('openai/whisper-small',revision=rev,torch_dtype=torch.float16).to('cuda').eval()
rows=[]
for name,lo,hi,lang in [('jp',0,12.53,'en'),('jp',6,9.6,'en'),('jp',7,8.2,'en'),('jp',8.2,9.95,'en'),('jp',9.95,12.53,'en')]:
 x=np.fromfile(D/(name+'.f32'),dtype='<f4').reshape(-1,2).mean(axis=1)
 x=resample_poly(x[round(lo*48000):round(hi*48000)],1,3)
 features=p(x,sampling_rate=16000,return_tensors='pt',return_attention_mask=True).to('cuda',torch.float16)
 with torch.inference_mode(): ids=m.generate(**features,language=lang,task='transcribe',max_new_tokens=50)
 row={'name':name,'range':[lo,hi],'text':p.batch_decode(ids,skip_special_tokens=True)[0]}
 rows.append(row);print(json.dumps(row),flush=True)
(D/'asr_jp_boundary.json').write_text(json.dumps({'offline':True,'auxiliary_only':True,'rows':rows},ensure_ascii=False,indent=2),'utf8')
