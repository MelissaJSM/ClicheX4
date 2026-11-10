from pathlib import Path
import hashlib,json,shutil
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=Path('<LOCAL_PATH>');o=D/'geometry_v1';o.mkdir(exist_ok=False);p=o/'generated.png';shutil.copyfile(s,p);assert sha(s)==sha(p)
j={'method':'builtin_imagegen','source_image_path':str(s),'source_sha256':sha(s),'saved_sha256':sha(p),'size':list(Image.open(p).size),'input_manifest_sha256':sha(D/'geometry_inputs_v1/manifest.json'),'prompt_sha256':sha(D/'geometry_inputs_v1/prompt.txt'),'refs':[95,98],'forms':['before','after'],'status':'생성 원화 저장, 네이티브 등록 전. 출력의 저알파 배경은 실제 알파 분포와 함께 검사 예정.','runtime_verified':False}
(o/'generation.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(p),'size':j['size']}))
