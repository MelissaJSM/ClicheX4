import json,sys,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];d=Path(__file__).parent;a=d/'production04';art=json.loads((a/'art.json').read_text());pairs=json.loads((a/'pairs.json').read_text());normalization=json.loads((d/'normalized02/art.json').read_text());metrics=[]
sheet=Image.new('RGB',(7*288,4*264),'#28394b');draw=ImageDraw.Draw(sheet)
for i,n in enumerate(range(33,55,2)):
 b=np.array(Image.open(a/f'run_{n:03d}.png'));s=np.array(Image.open(a/f'shoot_{n:03d}.png'));yy,xx=np.nonzero(b);ey,ex=np.nonzero(b==7);cx,cy=round(np.median(ex)),round(np.median(ey))
 face=np.array_equal(b[cy-2:cy+3,cx-1:cx+5],s[cy-2:cy+3,cx-1:cx+5]);boots=np.array_equal(b[54:],s[54:]);assert face and boots
 if n>=49:assert yy.max()==62
 metrics.append({'frame':n,'width':int(xx.max()-xx.min()+1),'height':int(yy.max()-yy.min()+1),'eye':[cx,cy],'foot_row':int(yy.max()),'paired_face_region_identical':face,'paired_boot_region_identical':boots})
 r=next(r for r in pairs['frames'] if r['run']==n);r['body_scale']=next(r for r in normalization['frames'] if r['frame']==n)['scale']
 for row,name in enumerate(('run','shoot')):
  im=Image.open(a/f'{name}_{n:03d}.png').convert('RGBA');pic=im.resize((288,240),Image.Resampling.NEAREST);x=((i%6)+1)*288;y=((i//6)*2+row)*264;sheet.paste(pic,(x,y+24),pic);draw.text((x+8,y+5),str(n+row),fill='white')
for row in range(4):
 im=Image.open(d.parent/'standing_buster_v1/parent_000.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,(0,row*264+24),im);draw.text((8,row*264+5),'ACCEPTED IDLE',fill='white')
sheet.save(a/'final_review_3x.png');sheet.resize((sheet.width//3,sheet.height//3),Image.Resampling.NEAREST).save(a/'final_review_1x.png')
# pairs metadata changed only: the production recipe records the final file hash.
(a/'pairs.json').write_text(json.dumps(pairs,indent=2));(a/'body_metrics.json').write_text(json.dumps(metrics,indent=2))
sources=['generated_with_backdrop.png','prompt.txt','landing_generated.png','landing_prompt.txt','normalize.py','normalize_landing.py','assemble.py','layout04.json']
(d/'source_manifest.json').write_text(json.dumps({'method':'builtin_imagegen_then_indexed_palette_registration','sources':{f:hashlib.sha256((d/f).read_bytes()).hexdigest() for f in sources},'arm_source':'work/ver_buki_riko/shibuki_art/standing_buster_v1/production03/registered_arm_085.png','source_sheet_firing_rows_not_used':True,'final_art':str(a.relative_to(ROOT)),'runtime_verified':False},indent=2));print(metrics)
