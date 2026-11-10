from pathlib import Path
import json,hashlib,shutil
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
source=Path('<LOCAL_PATH>')
out=D/'art01';out.mkdir(exist_ok=False);shutil.copyfile(source,out/'generated.png');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(out/'generation.json').write_text(json.dumps({'mode':'builtin_image_gen_edit','source_filename':source.name,'generated_sha256':sha(out/'generated.png'),'inputs_manifest_sha256':sha(D/'inputs01/manifest.json'),'prompt_sha256':sha(D/'inputs01/prompt.txt'),'native_packed':False,'runtime_verified':False},indent=2)+'\n','utf8');print(sha(out/'generated.png'))
