"""첫 피격 원화를 변경 없이 보존하고 입력 출처를 기록한다."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image

D = Path(__file__).resolve().parent
ROOT = D.parents[3]
SOURCE = Path(r'<LOCAL_PATH>')
OUT = D / 'first_v1'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    dest = OUT / 'generated.png'
    shutil.copyfile(SOURCE, dest)
    assert digest(dest) == digest(SOURCE)
    im = Image.open(dest)
    rec = {'tool': 'builtin image_gen.imagegen', 'source_path': str(SOURCE),
           'workspace_path': dest.relative_to(ROOT).as_posix(),
           'workspace_sha256': digest(dest), 'actual_size': list(im.size),
           'mode': im.mode, 'transparent_background': True,
           'inputs': [{'path': (D/'first_inputs_v1'/n).relative_to(ROOT).as_posix(),
                       'sha256': digest(D/'first_inputs_v1'/n)}
                      for n in ('targets.png', 'style.png', 'prompt.txt', 'manifest.json')],
           'scope': '기본/포스 피격 106/110의 네 전신 원화. 효과는 입력·출력 대상 아님.',
           'native_packed': False, 'runtime_verified': False}
    (OUT/'generation.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps(rec, ensure_ascii=True))

if __name__ == '__main__':
    main()
