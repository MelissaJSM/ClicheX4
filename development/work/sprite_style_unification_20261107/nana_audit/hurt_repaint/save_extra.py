"""추가 피격 원화를 변경 없이 보존한다."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
SRC=Path(r'<LOCAL_PATH>')
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=D/'extra_v1';out.mkdir(exist_ok=False);p=out/'generated.png';shutil.copyfile(SRC,p)
    assert digest(p)==digest(SRC)
    im=Image.open(p)
    j={'tool':'builtin image_gen.imagegen','source_path':str(SRC),'workspace_path':p.relative_to(ROOT).as_posix(),
       'workspace_sha256':digest(p),'actual_size':list(im.size),'mode':im.mode,'transparent_background':True,
       'inputs':[{'path':(D/'extra_inputs_v1'/n).relative_to(ROOT).as_posix(),'sha256':digest(D/'extra_inputs_v1'/n)}for n in('targets.png','style.png','prompt.txt','manifest.json')],
       'scope':'기본/포스 피격233/234 고유 몸체 네 원화. 기존 효과 제외.','native_packed':False,'runtime_verified':False}
    (out/'generation.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'sha256':digest(p),'size':im.size}))
if __name__=='__main__':main()
