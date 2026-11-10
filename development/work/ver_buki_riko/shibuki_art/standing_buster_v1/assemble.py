import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
d=Path(__file__).parent;out=d/'production01';out.mkdir(exist_ok=True)
words=json.loads((ROOT/'work/ver_buki_riko/shibuki_art/idle_chubby_v2/candidate09/candidate.json').read_text())['palette_words']
base=np.array(Image.open(d/'parent_000.png'));common=base.copy();common[36:53,:42]=0;common[53:55,:39]=0
sheet=Image.new('RGB',(5*288,288),'#28394b');draw=ImageDraw.Draw(sheet);records=[]
# Generated arm/sleeve isolation polygons, not synthesized character pixels.
polys={85:[(20,33),(34,32),(40,36),(44,37),(44,40),(40,43),(35,47),(35,54),(29,54),(27,46),(27,41),(20,41)],
87:[(26,29),(31,28),(40,34),(44,37),(44,40),(40,45),(36,48),(36,54),(30,54),(29,45),(26,37)],
92:[(29,26),(34,25),(40,31),(42,36),(44,37),(44,40),(40,45),(36,48),(36,54),(31,54),(30,43)]}
shifts={85:(7,-5),86:(8,-5),87:(5,-5),92:(3,1)}
for i,n in enumerate((0,85,86,87,92)):
 if n==0:canvas=base.copy()
 else:
  src=85 if n==86 else n;a=np.array(Image.open(d/f'normalized_{src:03d}.png'))
  mask=Image.new('1',(96,80));ImageDraw.Draw(mask).polygon(polys[src],fill=1);arm=np.where(np.array(mask),a,0).astype(np.uint8)
  yy,xx=np.nonzero(arm);dx,dy=shifts[n];shifted=np.zeros_like(arm);shifted[yy+dy,xx+dx]=arm[yy,xx]
  canvas=common.copy();canvas[shifted!=0]=shifted[shifted!=0]
  # Preserve the approved head and face exactly, plus the entire lower body.
  canvas[:20]=base[:20];canvas[20:36,42:]=base[20:36,42:];canvas[55:]=base[55:]
  save_image(arm.tobytes(),(96,80),words,out/f'isolated_arm_{n:03d}.png')
  save_image(shifted.tobytes(),(96,80),words,out/f'registered_arm_{n:03d}.png')
  assert np.array_equal(canvas[:20],base[:20]) and np.array_equal(canvas[20:36,42:],base[20:36,42:]) and np.array_equal(canvas[55:],base[55:])
  records.append({'frame':n,'image':f'standing_{n:03d}.png','source_frame':src,'arm_shift':shifts[n],'face_and_foot_preserved':True,'forward_hair_may_be_occluded_by_weapon':True})
 pic=save_image(canvas.tobytes(),(96,80),words,out/f'standing_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST)
 sheet.paste(pic,(i*288,32),pic);draw.text((i*288+20,12),f'Shibuki {n:03d}',fill='white')
sheet.save(out/'review_3x.png');(out/'art.json').write_text(json.dumps({'palette_words':words,'frames':records,'source_inventory':'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json'},indent=2))
