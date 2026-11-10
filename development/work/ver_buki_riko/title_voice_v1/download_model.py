import os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
os.environ['HF_HOME']=str(ROOT/'work/tools/title_voice_cache')
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
from huggingface_hub import HfApi,snapshot_download
repo='Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice'
info=HfApi().model_info(repo)
record={'repo':repo,'revision':info.sha,'license':info.card_data.get('license'),'path':None}
print(json.dumps(record),flush=True)
assert record['license']=='apache-2.0'
record['path']=snapshot_download(repo,revision=info.sha,ignore_patterns=['*.bin','*.pt','*.pth'],max_workers=4)
(D/'model_revision.json').write_text(json.dumps(record,indent=2),'utf-8')
print('downloaded',flush=True)
