"""builtin 결과를 프로젝트의 새 경로에 복사하고 실제 입력/프롬프트를 묶는다."""
from pathlib import Path
import sys,json,argparse,shutil,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--page',choices=list('abcd'),required=True);p.add_argument('--generated',required=True);args=p.parse_args();src=Path(args.generated);assert src.is_file()and'generated_images'in src.parts
 out=D/f'after_{args.page}_v1';out.mkdir(exist_ok=False);dst=out/'generated.png';shutil.copy2(src,dst);assert sha(src)==sha(dst)
 inputs=[D/f'after_inputs_v1/{args.page}_fixed_bodies.png',D/'after_inputs_v1/after_style_master.png'];prompt=D/f'prompt_after_{args.page}_v1.txt'
 r={'mode':'builtin imagegen edit','source_generated_path':src.as_posix(),'workspace_path':dst.relative_to(ROOT).as_posix(),'workspace_sha256':sha(dst),'size':list(Image.open(dst).size),'input_images':{p.relative_to(ROOT).as_posix():sha(p)for p in inputs},'prompt_path':prompt.relative_to(ROOT).as_posix(),'prompt_sha256':sha(prompt),'original_unchanged':True}
 (out/'generation.json').write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps(r))
if __name__=='__main__':main()
