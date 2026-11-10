import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
d=Path(__file__).parent;a=d/'production01';a.mkdir(exist_ok=True);src=Image.open(d/'generated.png').convert('RGBA');pal=json.loads((d.parent/'idle_chubby_v2/candidate09/candidate.json').read_text())['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32);records=[];sheet=Image.new('RGB',(4*288,264),'#28394b');dr=ImageDraw.Draw(sheet)
for i,n in enumerate((120,122,124)):
 c=src.crop(([0,850,1390][i],0,[850,1390,src.width][i],src.height));mask=np.array(c)[:,:,3]>=160;ys,xs=np.nonzero(mask);bb=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));c=c.crop(bb);size=tuple(round(v*.085) for v in c.size);arr=quantize(c,size,rgb,128);yy,xx=np.nonzero(arr);fy,fx=np.nonzero(arr[-4:]);left=round(48-(fx.min()+fx.max())/2);top=62-int(yy.max());canvas=np.zeros((80,96),np.uint8);canvas[top:top+size[1],left:left+size[0]]=arr
 save_image(canvas.tobytes(),(96,80),pal,a/f'frame_{n:03d}.png');records.append({'frame':n,'image':f'frame_{n:03d}.png','scale':.085,'source_box':bb,'size':size,'offset':[left,top]});im=Image.open(a/f'frame_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,((i+1)*288,24),im);dr.text(((i+1)*288+8,5),str(n),fill='white')
im=Image.open(d.parent/'standing_buster_v1/parent_000.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,(0,24),im);dr.text((8,5),'ACCEPTED IDLE',fill='white');sheet.save(a/'body_review.png');(a/'art.json').write_text(json.dumps({'frames':records,'palette_words':pal,'source_inventory':'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json'},indent=2));print(records)
