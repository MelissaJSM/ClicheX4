"""138 위로 든 권총팔 국소 교정 원화를 프로젝트에 보존한다."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    src=Path('<LOCAL_PATH>');out=D/'raised138_v1';out.mkdir(exist_ok=False);dest=out/'generated.png';shutil.copyfile(src,dest);im=Image.open(dest)
    m={'tool':'builtin imagegen','source_output_path':str(src),'source_sha256':sha(src),'workspace_path':dest.relative_to(ROOT).as_posix(),'workspace_sha256':sha(dest),'size':list(im.size),'mode':im.mode,'prompt_path':(D/'raised138_inputs_v1/prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':sha(D/'raised138_inputs_v1/prompt.txt'),'input_manifest_sha256':sha(D/'raised138_inputs_v1/manifest.json'),'scope':'138 위로 든 권총팔/오해한 가짜귀 국소교정.원손접점·정본총/보호부위 등록 전.'}
    (out/'generation.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(dest),'size':m['size']}))
if __name__=='__main__':main()
