"""builtin 생성 원본을 덮어쓰지 않고 프로젝트에 복사한다."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    src=Path('<LOCAL_PATH>')
    out=D/'first_v1';out.mkdir(exist_ok=False);dest=out/'generated.png';shutil.copyfile(src,dest)
    m={'tool':'builtin imagegen','source_output_path':str(src),'source_sha256':sha(src),'workspace_path':dest.relative_to(ROOT).as_posix(),'workspace_sha256':sha(dest),'size':list(Image.open(dest).size),'mode':Image.open(dest).mode,'prompt_path':(D/'first_inputs_v1/prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':sha(D/'first_inputs_v1/prompt.txt'),'input_manifest_sha256':sha(D/'first_inputs_v1/manifest.json'),'scope':'133/135 전후4표시 원화. 네이티브 정합/팔레트/패킹/게임 검증 전.'}
    (out/'generation.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(dest),'size':m['size']}))
if __name__=='__main__':main()
