from pathlib import Path
import hashlib,json,shutil
from PIL import Image
D=Path(__file__).parent/'rin_extension/bank1_special01';src=Path('<LOCAL_PATH>');out=D/'generated.png'
assert not out.exists();shutil.copyfile(src,out);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(src)==sha(out)
r={'tool':'builtin image_gen.imagegen','output_original':str(src),'output_copy':str(out),'output_sha256':sha(out),'size':list(Image.open(out).size),'prompt_sha256':sha(D/'prompt.txt'),'transparent_background_requested':True,'approved_replacement_sprite_inputs_only':True,'raw_game_assets_sent':False,'registered':False,'game_changed':False,'root_art_accepted':False,'user_accepted':False}
(D/'generation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(r))
