from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from PIL import Image
D=Path(__file__).parent/'rin_extension';O=D/'ride_head01';a=(D/'prepared_bank1_recovery128/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(a,9))
j=json.loads((O/'inputs.json').read_text('utf8'));j['scope']='다섯 각도의 작은 머리만 재작화한다. 단일16×16타일과 원래 얼굴 위치·빈80을 보존한다. 전신이나 탈것은 생성 입력에 넣지 않는다.';j['style_ref']=0
(O/'inputs.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
idle=render(a,0,0,0)[0];rgba(idle,pal).crop((136,128,168,160)).resize((1024,1024),Image.Resampling.NEAREST).save(O/'idle_head_style0.png')
rgba(idle,pal).crop((112,112,208,208)).resize((1536,1536),Image.Resampling.NEAREST).save(O/'idle_full_style0.png')
