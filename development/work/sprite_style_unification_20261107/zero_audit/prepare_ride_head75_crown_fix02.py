"""후면75 보닛 능선만 보완하는 단독 입력.77 및 다른 각도는 제외한다."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import rgba
D=Path(__file__).parent/'rin_extension';O=D/'ride_head75_crown_fix02';O.mkdir(exist_ok=False)
j=json.loads((D/'ride_head01/inputs.json').read_text('utf8'));pal=j['palette_words'];a=np.zeros((32,32),np.uint8);a[8:24,8:24]=np.array(Image.open(D/'ride_head_registered_v2/head_75_indices16.png'))
rgba(a,pal).save(O/'input_native.png');rgba(a,pal).resize((1024,1024),Image.Resampling.NEAREST).save(O/'input.png')
old=Image.open(D/'ride_head01/head_75_native.png');old.resize((1024,1024),Image.Resampling.NEAREST).save(O/'original_height_reference.png')
prompt='''Use case: precise-object-edit. Edit ONLY the TOP CROWN/BONNET of the FIRST transparent1024x1024 image. It is ONE rear-three-quarter head of the same Rin maid, native32x32 at32x enlargement. The head is intentionally very small within the canvas. Keep the entire canvas and native grid fixed. The second image is the old fuller head shape reference only; never restore its flat white blobs.
Current issue: the new head has a narrow tall point at its very top, making the bonnet look like a spike. Round and broaden ONLY that top crown, into a compact TWO-to-THREE-native-pixel-wide cool-white/light-gray ridge with supporting hair on both sides, at native rows10..13. The upper head should read like a full rounded human skull under a small maid bonnet, not a cone, animal ear or white antenna. Keep deliberate navy edge pixels and cool-gray layered strands; do not smear or simplify the new hair details. Preserve the LOWER TWO-THIRDS of the head EXACTLY: small cheek at the lower left, chin endpoint at native y23, dark lower outline, right-side blue ribbon, side hair edge, and angle. No new face or eyes. Do not shift the entire head, change the jaw, widen the entire head, lengthen the neck, or add a body. No interpolation or vertical stretch. Occupied native footprint must remain inside x9..22 or23, y10..23; first column of the central16x16 tile x8 remains empty. Existing lower white hair tips and all transparent padding stay unchanged. Return one transparent square image of this one head, with crisp native pixel clusters, no labels/background/glow.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8')
r={'ref':75,'aliases':[75,76],'fixed_native_canvas':[32,32],'scale':32,'semantic_edit_native_region':[9,10,22,15],'preserve_lower_rows_from':15,'source_registration':'ride_head_registered_v2','new_other_heads_unchanged':True,'why_new_art':'원화 상단의 실제 밝은 능선도 좁으며 넓은 보닛을 뒷받침할 충분한 새 표본이 없어 코드로 색을 채우지 않고75만 재생성합니다.','references':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in (O/'input.png',O/'original_height_reference.png')]}
(O/'inputs.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(O)
