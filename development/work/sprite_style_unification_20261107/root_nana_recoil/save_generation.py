from pathlib import Path
import shutil,json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=Path('<LOCAL_PATH>')
out=D/'art01';out.mkdir(exist_ok=False);shutil.copyfile(src,out/'generated.png')
(out/'metadata.json').write_text(json.dumps({'tool':'builtin imagegen','intent':'style-transfer edit','source_path':str(src),'sha256':sha(src),'prompt_path':'inputs01/prompt.txt','prompt_sha256':sha(D/'inputs01/prompt.txt'),'review':'Generated original displayed and inspected. Native palette/registration review remains.'},ensure_ascii=False,indent=2)+'\n','utf8')
s=(W/'root_nana_standing/register_art.py').read_text('utf8').replace('26765dc823179faae9a24b9102fbccb9aa8d511434e784931b0245a77d3a4711',sha(src)).replace('standing pose','recoil pose')
p=D/'register_art.py';assert not p.exists();p.write_text(s,'utf8');print(sha(src))
