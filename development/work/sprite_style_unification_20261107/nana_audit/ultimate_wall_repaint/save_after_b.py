"""builtin 생성 원본을 보존하고 작업 사본/출처를 기록한다."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image
D=Path(__file__).resolve().parent
G=Path('<LOCAL_PATH>')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for page,name in [('a','exec-137b0b77-ce8e-4120-9eb0-be56a7a65dd2.png'),('b','exec-5f61fc7f-f8f7-46f1-b26b-d1b9f184b62f.png')]:
 out=D/f'after_{page}_v1';out.mkdir(exist_ok=True);src=G/name;dst=out/'generated.png'
 if dst.exists():assert sha(src)==sha(dst)
 else:shutil.copy2(src,dst)
 inputs=[D/f'after_inputs_v1/{page}_fixed_bodies.png',D/'after_inputs_v1/after_style_master.png']
 rec={'tool':'builtin image_gen','source_path':str(src),'source_sha256':sha(src),'workspace_sha256':sha(dst),'dimensions':Image.open(dst).size,'prompt_path':str(D/f'prompt_after_{page}_v1.txt'),'prompt_sha256':sha(D/f'prompt_after_{page}_v1.txt'),'inputs':[{'path':str(p),'sha256':sha(p)}for p in inputs],'fourth_reference_cell_not_used':True,'scope':'새 전신의 의상만 후속 의미영역 등록. 아직 native ARC/게임 미적용.'}
 (out/'generation.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(page,sha(dst))
