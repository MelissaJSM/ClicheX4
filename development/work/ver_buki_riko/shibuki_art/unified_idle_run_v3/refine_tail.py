from pathlib import Path
import sys,json,struct,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
work=Path(__file__).parent
out=work/'paired_body';out.mkdir(exist_ok=False)
for p in (work/'production').iterdir():
    if p.is_file():shutil.copyfile(p,out/p.name)
art=json.loads((out/'art.json').read_text());r=next(r for r in art['frames'] if r['frame']==13)
rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in art['palette_words']],np.int32)
im=Image.open(ROOT/'work/ver_buki_riko/shibuki_art/unified_idle_run_v2/passing13_tail_generated.png').convert('RGBA');im=im.crop(im.getbbox())
patch=quantize(im,tuple(r['native_size']),rgb)
base=np.array(Image.open(out/'run_013.png'));before=base.copy();left,top=r['world_position'];x,y=left+48,top+40
# Import only the generated tail rectangle. All head, torso and leg pixels stay exact.
region=(20,21,31,40);x0,y0,x1,y1=region
base[y+y0:y+y1,x+x0:x+x1]=patch[y0:y1,x0:x1]
save_image(base.tobytes(),(96,80),art['palette_words'],out/'run_013.png')
r['opaque_pixels']=int(np.count_nonzero(base));r['tail_patch']={'source':'../passing13_tail_generated.png','source_sha256':sha256((ROOT/'work/ver_buki_riko/shibuki_art/unified_idle_run_v2/passing13_tail_generated.png').read_bytes()),'local_rectangle':region,'changed_pixels':int(np.count_nonzero(before!=base))}
art['production_note']='13踰?瑗щ━留??앹꽦 ?섏젙蹂몄뿉???꾩엯. ?섎㉧吏 15?꾨젅?꾧낵 13踰?癒몃━/紐명넻/?ㅻ━ 蹂댁〈.'
(out/'art.json').write_text(json.dumps(art,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(r))
