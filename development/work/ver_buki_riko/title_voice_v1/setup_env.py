import json,urllib.request,zipfile,io,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
q=json.load(urllib.request.urlopen('https://pypi.org/pypi/qwen-tts/0.1.1/json'))
u=next(u for u in q['urls'] if u['filename'].endswith('.whl'))
raw=urllib.request.urlopen(u['url']).read()
(D/u['filename']).write_bytes(raw)
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    for n in z.namelist():
        if n.endswith('METADATA') or 'license' in n.lower():
            (D/Path(n).name).write_bytes(z.read(n))
    text=z.read('qwen_tts/inference/qwen3_tts_model.py').decode()
    (D/'qwen3_tts_model_review.py').write_text(text,'utf-8')
    print('wrapper',len(text),'exec calls',text.count('subprocess'),text.count('exec('))
# Share already installed CUDA/audio libraries read-only. New conflicting versions go in this isolated env first.
env=ROOT/'work/tools/title_voice_env'
(env/'Lib/site-packages/voice_shared.pth').write_text(str(ROOT/'work/tools/voice_env/Lib/site-packages')+'\n','utf-8')
subprocess.run([str(env/'Scripts/python.exe'),'-m','pip','install','--no-deps',str(D/u['filename']),'transformers==4.57.3','accelerate==1.12.0','tokenizers==0.22.1','sox==1.5.0'],check=True)
(D/'package_source.json').write_text(json.dumps({'package':'qwen-tts','version':'0.1.1','wheel':u,'license':'Apache-2.0','official_repo':'https://github.com/QwenLM/Qwen3-TTS'},indent=2),'utf-8')
