"""builtin 결과를 원본 보존 복사하고 실제 알파/크기를 기록한다."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
source=Path('<LOCAL_PATH>')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=D/'extra_v1';out.mkdir(exist_ok=False);dest=out/'generated.png';shutil.copy2(source,dest)
im=Image.open(dest).convert('RGBA');a=np.array(im);red=(a[:,:,0]>180)&(a[:,:,1]<60)&(a[:,:,2]<70);v,c=np.unique(a[:,:,3][red],return_counts=True)
j={'tool':'builtin image_gen','source_path':str(source),'source_sha256':sha(source),'workspace_path':dest.relative_to(ROOT).as_posix(),'workspace_sha256':sha(dest),'size':list(im.size),'mode':im.mode,'alpha_extrema':list(im.getchannel('A').getextrema()),'red_alpha_histogram':{str(int(x)):int(y)for x,y in zip(v,c)},'input_manifest_sha256':sha(D/'extra_inputs_v1/manifest.json'),'prompt_path':(D/'extra_inputs_v1/prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':sha(D/'extra_inputs_v1/prompt.txt'),'scope':'Ultimate233/234 전후4표시 첫 원화. 실제 게임 색인/관절 정합 전. 원화 원본 보존, 작업 복사만 수행.','runtime_verified':False}
(out/'generation.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(j))
