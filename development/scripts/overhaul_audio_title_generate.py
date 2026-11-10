"""기존 로컬 Qwen 모델로 새 타이틀 콜 후보를 생성한다. 네트워크 사용 없음."""
import os,json,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'work/overhaul_20261105/audio/title'
os.environ.update(HF_HOME=str(ROOT/'work/tools/title_voice_cache'),HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',TRANSFORMERS_OFFLINE='1')
import torch,soundfile as sf
from qwen_tts import Qwen3TTSModel
def main():
    D.mkdir(parents=True,exist_ok=True)
    pin=json.loads((ROOT/'work/ver_buki_riko/title_voice_v1/model_revision.json').read_text('utf8'))
    torch.set_num_threads(8)
    model=Qwen3TTSModel.from_pretrained(pin['path'],device_map='cuda:0',dtype=torch.bfloat16,attn_implementation='sdpa')
    variants=[
      ('aiden_v2','Cliché X four!','English','Aiden','Speak a classic arcade game title announcement. Confident deep resonant voice, clear and natural. One compact energetic phrase, no long pause between the name and X four. Crisp enunciation, no singing or laughter.'),
      ('sohee_v2','클리셰 엑스 포!','Korean','Sohee','게임 제목을 또렷하고 힘 있게 한 호흡으로 외친다. 차분한 중저음의 당당한 게임 내레이터 목소리. 클리셰와 엑스 포 사이를 길게 끊지 않는다. 과장된 웃음이나 노래 없이 자연스럽고 선명하게.')]
    rows=[]
    for i,(name,text,lang,speaker,instruction) in enumerate(variants):
        p=D/(name+'.wav')
        if p.exists():raise FileExistsError(p)
        torch.manual_seed(11050+i);start=time.time()
        wavs,sr=model.generate_custom_voice(text=text,language=lang,speaker=speaker,instruct=instruction,max_new_tokens=100,do_sample=True,temperature=.65,top_p=.9)
        sf.write(p,wavs[0],sr,subtype='PCM_16')
        row=dict(name=name,text=text,language=lang,speaker=speaker,instruct=instruction,seed=11050+i,sample_rate=sr,duration=len(wavs[0])/sr,generation_seconds=time.time()-start)
        rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    (D/'generation.json').write_text(json.dumps({'model':pin,'variants':rows},ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
