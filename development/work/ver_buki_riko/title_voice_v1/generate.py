import os,json,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
os.environ['HF_HOME']=str(ROOT/'work/tools/title_voice_cache')
os.environ['HF_HUB_OFFLINE']='1';os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import torch,soundfile as sf
from qwen_tts import Qwen3TTSModel
pin=json.loads((D/'model_revision.json').read_text('utf-8'))
torch.set_num_threads(8)
model=Qwen3TTSModel.from_pretrained(pin['path'],device_map='cuda:0',dtype=torch.bfloat16,attn_implementation='sdpa')
variants=[
('ryan_arcade','Cliché X four!','English','Ryan','A confident, powerful arcade game title announcement. Clear punchy pronunciation, compact and energetic. Say the game name with excitement. No laughter, no singing, no extra words.'),
('ryan_clean','Cliché! X four!','English','Ryan','Announce this game title in a strong, bright voice, with crisp consonants and a short pause before X four. Quick and emphatic, natural, no rasp or growling.'),
('sohee_korean','클리셰! 엑스 포!','Korean','Sohee','밝고 힘찬 게임 타이틀 콜. 짧고 또렷하게, 흥분된 목소리로 제목을 외친다. 노래하지 않고 자연스럽게 발음한다.')]
records=[]
for i,(name,text,language,speaker,instruct) in enumerate(variants):
    torch.manual_seed(840+i);start=time.time()
    wavs,sr=model.generate_custom_voice(text=text,language=language,speaker=speaker,instruct=instruct,max_new_tokens=150,do_sample=True,temperature=0.75,top_p=0.9)
    sf.write(str(D/(name+'.wav')),wavs[0],sr,subtype='PCM_16')
    record={'name':name,'text':text,'language':language,'speaker':speaker,'instruct':instruct,'seed':840+i,'seconds':len(wavs[0])/sr,'sample_rate':sr,'elapsed':time.time()-start}
    records.append(record);print(json.dumps(record,ensure_ascii=True),flush=True)
(D/'generation.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),'utf-8')
