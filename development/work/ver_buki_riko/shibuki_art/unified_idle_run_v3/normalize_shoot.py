from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import ranges,quantize
from scripts.extract_zero import save_image
work=Path(__file__).parent;art=json.loads((work/'production/art.json').read_text());words=art['palette_words']
rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
im=Image.open(work/'shoot_generated.png').convert('RGBA');mask=np.array(im)[:,:,3]>=128;boxes=[]
for top,bottom in ranges(mask.any(1)):
 for left,right in ranges(mask[top:bottom].any(0)):
  yy,xx=np.nonzero(mask[top:bottom,left:right]);boxes.append((left,top+int(yy.min()),right,top+int(yy.max()+1)))
if len(boxes)!=16:raise ValueError('Expected sixteen shots')
out=work/'shoot_normalized';out.mkdir(exist_ok=False);records=[]
sheet=Image.new('RGB',(8*224,2*256),'#28394b');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16)
src=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z';inv=json.loads((src/'inventory.json').read_text())
for i,(r,bb) in enumerate(zip(art['frames'],boxes)):
 n=r['frame'];crop=im.crop(bb);scale=art['common_scale'];lab=quantize(crop,(round(crop.width*scale),round(crop.height*scale)),rgb,edge_threshold=48)
 run=np.array(Image.open(work/'production'/r['image']));ry,rx=np.nonzero(run==7);sy,sx=np.nonzero(lab==7)
 wx=round(float(np.median(rx)-np.median(sx)))-48;wy=round(float(np.median(ry)-np.median(sy)))-40
 canvas=np.zeros((80,96),np.uint8);canvas[wy+40:wy+40+lab.shape[0],wx+48:wx+48+lab.shape[1]]=lab
 pic=save_image(canvas.tobytes(),(96,80),words,out/f'shoot_{n+1:03d}.png').convert('RGBA');big=pic.resize((288,240),Image.Resampling.NEAREST);bx,by=(i%8)*224,(i//8)*256;sheet.paste(big,(bx-32,by+20),big);d.text((bx+6,by+5),f'Shoot {n+1:03d}',font=font,fill='white')
 orig=np.array(Image.open(src/f'base_{n+1:03d}.png'));ob=inv['base_frames'][n+1]['bounds'];oy,ox=np.nonzero(orig);minx=int(ox.min());muzzley=float(np.median(oy[ox<=minx+2]))+ob[1]
 yy,xx=np.nonzero(canvas);xmin=int(xx.min());my=float(np.median(yy[xx<=xmin+2]))-40
 record={'frame':n+1,'run':n,'world_position':[wx,wy],'image':f'shoot_{n+1:03d}.png','original_muzzle':[minx+ob[0],muzzley],'generated_muzzle':[xmin-48,my]};records.append(record);print(json.dumps(record),flush=True)
sheet.save(out/'shoot_master_3x.png');(out/'art.json').write_text(json.dumps({'frames':records,'scale':art['common_scale'],'palette_words':words},indent=2)+'\n')
