import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
d=Path(__file__).parent;a=d/'production16';original=d/'production05'
art=json.loads((a/'art.json').read_text());changes=[];metrics=[]
sheet=Image.new('RGB',(672,184),'#28394b');draw=ImageDraw.Draw(sheet)
for i,r in enumerate(art['frames']):
 n=r['frame'];normal=np.array(Image.open(a/f'run_{n:03d}.png'));shot=np.array(Image.open(a/f'shoot_{n:03d}.png'))
 before=np.array(Image.open(original/f'run_{n:03d}.png'));yy,xx=np.nonzero(normal!=before)
 assert np.array_equal(normal!=0,before!=0) and np.array_equal(normal==15,before==15)
 assert np.array_equal(normal==7,before==7)
 edits=[[int(x),int(y),int(before[y,x]),int(normal[y,x])] for x,y in zip(xx,yy)]
 if edits:
  assert n==59 and len(edits)==10
  for x,y,old,new in edits:assert shot[y,x]==new
  changes.append({'frame':n,'pixels':edits,'alpha_outline_eyes_unchanged':True})
 eyes=lambda v:np.argwhere(v==7).tolist()
 assert eyes(normal)==eyes(shot)
 metrics.append({'frame':n,'scale':r['scale'],'source_size':r['size'],'offset':r['canvas_offset'],'eye_canvas':r['eye_canvas'],'normal_shoot_eyes_equal':True,'bbox':Image.open(a/f'run_{n:03d}.png').getbbox()})
 for row,mode in enumerate(('run','shoot')):
  im=Image.open(a/f'{mode}_{n:03d}.png').convert('RGBA');sheet.paste(im,((i+1)*96,row*92+12),im);draw.text(((i+1)*96+5,row*92+1),str(n+row),fill='white')
for row in range(2):
 im=Image.open(d.parent/'standing_buster_v1/parent_000.png').convert('RGBA');sheet.paste(im,(0,row*92+12),im);draw.text((3,row*92+1),'IDLE',fill='white')
sheet.save(a/'final_review_1x.png');sheet.resize((2016,552),Image.Resampling.NEAREST).save(a/'final_review_3x.png')
art['final_internal_quantization_refinement']=changes
for path,value in [(a/'art.json',art),(a/'quantization_changes.json',changes),(a/'body_metrics.json',metrics)]:path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
names=['generated.png','compact_generated.png','contact_generated.png','prompt.txt','compact_prompt.txt','contact_prompt.txt','normalize06.py','assemble05.py','plan.json']
(d/'source_manifest.json').write_text(json.dumps({'method':'builtin_imagegen_then_indexed_palette_registration','files':{n:digest(d/n) for n in names},'final_art':'production16','shade_refinement_pixels':10},indent=2),encoding='utf-8')
print(json.dumps({'final_art':str(a),'changes':changes,'frames':len(metrics)}))
