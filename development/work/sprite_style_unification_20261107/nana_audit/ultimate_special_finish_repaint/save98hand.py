from pathlib import Path
import hashlib,json,shutil
from PIL import Image
D=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=Path('<LOCAL_PATH>');o=D/'hand98_v1';o.mkdir(exist_ok=False);p=o/'generated.png';shutil.copyfile(s,p);assert sha(s)==sha(p)
j={'method':'builtin_imagegen','source_image_path':str(s),'source_sha256':sha(s),'saved_sha256':sha(p),'size':list(Image.open(p).size),'input_manifest_sha256':sha(D/'hand98_inputs_v1/manifest.json'),'prompt_sha256':sha(D/'hand98_inputs_v1/prompt.txt'),'refs':[98],'forms':['before','after'],'status':'98 국소 생성 저장. 몸통/손/원총구 및 실제 알파 검증 전.','runtime_verified':False};(o/'generation.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(p),'size':j['size']}))
