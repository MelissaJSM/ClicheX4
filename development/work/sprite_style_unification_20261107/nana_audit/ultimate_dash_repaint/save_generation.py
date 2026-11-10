"""Builtin 생성 출력과 입력 해시를 새 작업 디렉터리에 보존한다."""
from pathlib import Path
import sys, hashlib, json, shutil
from PIL import Image
D = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder, filename, prompt, *inputs = sys.argv[1:]
    src = Path('<LOCAL_PATH>') / filename
    out = D / folder
    assert D in out.resolve().parents and not out.exists()
    out.mkdir()
    dst = out / 'generated.png'
    shutil.copy2(src, dst)
    pp = D / prompt
    rec = {'tool':'builtin image_gen', 'source_path':str(src), 'source_sha256':sha(src), 'workspace_sha256':sha(dst), 'dimensions':Image.open(dst).size, 'prompt_path':str(pp), 'prompt_sha256':sha(pp), 'inputs':[{'path':str(D/p), 'sha256':sha(D/p)} for p in inputs], 'native_packed':False, 'runtime_verified':False}
    (out/'generation.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(sha(dst))
if __name__ == '__main__': main()
