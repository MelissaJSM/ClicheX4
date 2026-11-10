from pathlib import Path
import json,hashlib
from PIL import Image
D=Path(__file__).parent/'rin_extension';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
outputs={'ground_second01':'exec-51f0eb34-4f17-4e0d-8048-3e249f6aa47b.png','ground_recovery01':'exec-89a35a0f-ca0e-4afa-af58-aabd347246d2.png','movement_returns01':'exec-dd461100-0c99-4a4a-a29b-6dd9ec57d5b1.png'}
for name,f in outputs.items():
 p=D/name/'generated.png';original=Path('<LOCAL_PATH>')/f;assert p.read_bytes()==original.read_bytes()
 j={'tool':'builtin image_gen.imagegen','output_original':str(original),'output_copy':str(p),'output_sha256':sha(p),'size':list(Image.open(p).size),'prompt_sha256':sha(D/name/'prompt.txt'),'transparent_background_requested':True,'approved_replacement_sprite_inputs_only':True,'raw_game_assets_sent':False,'registered':False,'game_changed':False,'user_accepted':False}
 (D/name/'generation.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(j))
