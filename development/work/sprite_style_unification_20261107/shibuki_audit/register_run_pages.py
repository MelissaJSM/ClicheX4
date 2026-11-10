"""새2x2생성페이지를고정1/8로양자화하여정합검토자료를만든다."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
import numpy as np
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_rin_run import quantize
from native_pose_pack import SOURCE,SOURCE_SHA
from src.psx_disc import file_hash
PAGES={2:[3,5,7,9],3:[15],4:[19,21,23,25],5:[27,29,31,85]}
def main():
 assert file_hash(SOURCE)==SOURCE_SHA
 arc=Archive(read_disc(SOURCE,('PL02_U.ARC',))[0]['PL02_U.ARC']);colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[1:16]],np.int32)
 out=H/'run_after_raw01';out.mkdir(exist_ok=False);report=[]
 for pg,refs in PAGES.items():
  src=ROOT/f'work/sprite_style_unification_20261107/shibuki/ultimate_run_detail{pg:02}';sheet=Image.open(src/'generated_after.png').convert('RGBA');info=json.loads((src/'inputs.json').read_text());assert sheet.size==(1536,1024);items=[]
  for t in info['frames']:
   n=t['ref']
   if n not in refs:continue
   x,y=t['cell'];a=np.zeros((384,384),np.uint8);a[128:192,112:208]=quantize(sheet.crop((x*768,y*512,x*768+768,y*512+512)),colors,.125)
   b=np.array(Image.open(src/'native'/f'{n:03}_indices.png'));Image.fromarray(a).save(out/f'{n:03}_indices.png');arc.rgba(a).save(out/f'{n:03}.png')
   items.extend([(f'{n} jacket source',arc.rgba(b,16)),(f'{n} raw swimsuit',arc.rgba(a))]);yy,xx=np.nonzero((a>0)&(b==0))
   report.append({'ref':n,'page':pg,'source':(src/'generated_after.png').relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256((src/'generated_after.png').read_bytes()).hexdigest(),'scale':.125,'after_outside_before_xy':list(map(list,zip(xx.tolist(),yy.tolist()))),'not_final_registered':True})
  page(items,arc.composite(0)[0],out/f'page{pg:02}.png',cols=2,scale=4)
 (out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
if __name__=='__main__':main()
