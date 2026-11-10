"""builtin 출력 원본 보존, 새 경로만 저장하는 짧은 provenance 도구."""
from pathlib import Path
import sys,hashlib,json,shutil
from PIL import Image
D=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 folder,filename,prompt,*inputs=sys.argv[1:];src=Path('<LOCAL_PATH>')/filename;out=D/folder;out.mkdir(exist_ok=False);dst=out/'generated.png';shutil.copy2(src,dst);pp=D/prompt
 rec={'tool':'builtin image_gen','source_path':str(src),'source_sha256':sha(src),'workspace_sha256':sha(dst),'dimensions':Image.open(dst).size,'prompt_path':str(pp),'prompt_sha256':sha(pp),'inputs':[{'path':str(D/p),'sha256':sha(D/p)}for p in inputs],'fourth_reference_cell_not_used':True,'native_packed':False,'runtime_verified':False};(out/'generation.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(sha(dst))
if __name__=='__main__':main()
