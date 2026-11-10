"""생성 키포즈 전체를 고정 배율과 실제 CLUT로 변환한다. 옛 머리/옷으로 덮지 않는다."""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive, page
from scripts.prepare_rin_run import quantize

HERE = Path(__file__).parent
info = json.loads((HERE/'inputs.json').read_text('utf8'))
arc = Archive(read_disc(ROOT/info['source']['bin'], ('PL02_U.ARC',))[0]['PL02_U.ARC'])
colors = np.array([[(int(w)>>s&31)*255//31 for s in (0,5,10)] for w in arc.words[17:32]], np.int32)
sheet = Image.open(HERE/'generated.png').convert('RGBA')
assert sheet.size == (1536,1024)
out = HERE/'native_preview'
out.mkdir(exist_ok=True)
items, records = [], []
for item in info['targets']:
    col,row = item['cell']
    crop = sheet.crop((col*512,row*512,col*512+512,row*512+512))
    # Fixed 1/8 native registration; original sprite and whole pose remain separate.
    indexed = quantize(crop, colors, .125)
    target = np.zeros((384,384),np.uint8)
    target[128:192,128:192] = indexed
    Image.fromarray(target).save(out/f'{item["ref"]:03}_indices.png')
    revised = arc.rgba(target,16)
    revised.save(out/f'{item["ref"]:03}.png')
    old = arc.composite(item['ref'],15,2)[0]
    items.extend([(f'{item["ref"]:03} before',old),(f'{item["ref"]:03} detailed',revised)])
    records.append({'ref':item['ref'],'native_scale':.125,'before_bounds':old.getchannel('A').getbbox(),
                    'new_bounds':revised.getchannel('A').getbbox(),'opaque_pixels':int((target>0).sum()),
                    'palette_row':16,'old_detail_overwrite':False})
page(items,arc.composite(0,15,2)[0],out/'comparison.png',cols=2,scale=4)
(out/'registration.json').write_text(json.dumps(records,indent=2)+'\n','utf8')
print(json.dumps({'output':str(out),'records':records}))
