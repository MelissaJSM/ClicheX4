"""내장 도구의 손/권총 국소 원화를 비파괴 보존."""
from pathlib import Path
import argparse,json,hashlib,shutil
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('group',choices=['a','b']);ap.add_argument('source');args=ap.parse_args();src=Path(args.source);out=D/f'pistol_hands_{args.group}_v1';out.mkdir(exist_ok=False);dest=out/'generated.png';shutil.copyfile(src,dest);im=Image.open(dest);inp=D/f'pistol_hands_{args.group}_inputs_v1'
 m={'tool':'builtin imagegen','source_output_path':str(src),'source_sha256':sha(src),'workspace_path':dest.relative_to(ROOT).as_posix(),'workspace_sha256':sha(dest),'size':list(im.size),'mode':im.mode,'prompt_path':(inp/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':sha(inp/'prompt.txt'),'input_manifest_sha256':sha(inp/'manifest.json'),'scope':'최초 등장 권총 방향을 새 손에 복원한 국소 원화. 고정16색/정본8px 총열/손 접점·공통층 등록 전.'};(out/'generation.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(dest),'size':m['size']}))
if __name__=='__main__':main()
