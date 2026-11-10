from pathlib import Path
import json,hashlib,shutil
D=Path(__file__).resolve().parent;ROOT=D.parents[2];source=Path('<LOCAL_PATH>');out=D/'art01';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copyfile(source,out/'generated.png');(out/'generation.json').write_text(json.dumps({'tool':'builtin image_gen','exec_image_file':source.name,'source_sha256':sha(source),'saved_sha256':sha(out/'generated.png'),'prompt_path':(D/'inputs01/prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':sha(D/'inputs01/prompt.txt'),'transparent_background':True,'target_manifest_sha256':sha(D/'inputs01/manifest.json')},ensure_ascii=False,indent=2)+'\n','utf8')
t=(D.parent/'root_nana_lowhp/register_art.py').read_text('utf8').replace("m['source_arc']","m['parent_arc']").replace("m['source_arc_sha256']","m['parent_sha256']").replace('b10a077778b2ae3fb9b0390ac34eaf884bd5a12209c9413d96739f6ccb6627b8',sha(source)).replace('low HP','special pose')
(D/'register_art.py').write_text(t,'utf8');print(sha(source))
