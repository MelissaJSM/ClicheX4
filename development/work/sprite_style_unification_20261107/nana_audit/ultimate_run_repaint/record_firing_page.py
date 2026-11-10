"""builtin 사격팔 페이지를 새 작업 경로에 복사하고 입력 해시를 기록한다."""
from pathlib import Path
import json,argparse,shutil,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--page',choices=list('abcd'),required=True);p.add_argument('--form',choices=['before','after'],required=True);p.add_argument('--generated',required=True);p.add_argument('--version',default='v1');p.add_argument('--input-set',default='firing_inputs_v1');a=p.parse_args();src=Path(a.generated);assert src.is_file()and'generated_images'in src.parts
 out=D/f'firing_{a.page}_{a.form}_{a.version}';out.mkdir(exist_ok=False);dst=out/'generated.png';shutil.copy2(src,dst);assert sha(src)==sha(dst)
 inp=D/a.input_set;inputs=[inp/f'{a.page}_{a.form}_targets.png',inp/f'{a.page}_original_{a.form}_geometry.png',inp/f'{a.form}_accepted_style.png'];prompt=D/f'prompt_firing_{a.page}_{a.form}_{a.version}.txt'
 r={'mode':'builtin imagegen edit','source_generated_path':src.as_posix(),'workspace_path':dst.relative_to(ROOT).as_posix(),'workspace_sha256':sha(dst),'size':list(Image.open(dst).size),'input_images':{q.relative_to(ROOT).as_posix():sha(q)for q in inputs},'prompt_path':prompt.relative_to(ROOT).as_posix(),'prompt_sha256':sha(prompt),'original_unchanged':True}
 (out/'generation.json').write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps(r))
if __name__=='__main__':main()
