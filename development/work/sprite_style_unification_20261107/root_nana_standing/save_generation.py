from pathlib import Path
from PIL import Image
import json,hashlib,shutil
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
src=Path('<LOCAL_PATH>');out=D/'art01';out.mkdir(exist_ok=False);shutil.copyfile(src,out/'generated.png');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();im=Image.open(out/'generated.png')
(out/'generation.json').write_text(json.dumps({'tool':'builtin image_gen.imagegen','source_result_file':str(src),'source_sha256':sha(src),'copied_sha256':sha(out/'generated.png'),'size':list(im.size),'mode':im.mode,'alpha_extrema':im.getchannel('A').getextrema(),'prompt_path':(D/'inputs01/prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':sha(D/'inputs01/prompt.txt'),'input_manifest_sha256':sha(D/'inputs01/manifest.json'),'target_refs':[89,97],'native_registered':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
code=(D.parent/'root_nana_special/register_art.py').read_text('utf8').replace('57d4627ed5a08b98f208cd8a27e40cee7979df1729940b6486f82504c15ebf3c',sha(out/'generated.png')).replace('special pose','standing pose');p=D/'register_art.py';assert not p.exists();p.write_text(code,'utf8');print(sha(out/'generated.png'))
