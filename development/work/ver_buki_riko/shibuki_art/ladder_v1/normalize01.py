import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
d=Path(__file__).parent;out=d/'production01';out.mkdir(exist_ok=True)
src=Image.open(d/'generated.png').convert('RGBA');pal=json.loads((d.parent/'idle_chubby_v2/candidate09/candidate.json').read_text())['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32)
order=[143,144,146,149,151,153,154,183,150];foot={143:63,144:63,146:68,149:68,151:68,153:56,154:70,183:72,150:68};records=[]
sheet=Image.new('RGB',(5*288,2*264),'#28394b');dr=ImageDraw.Draw(sheet)
im=Image.open(d.parent/'standing_buster_v1/parent_000.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,(0,24),im);dr.text((8,5),'ACCEPTED IDLE',fill='white')
for i,n in enumerate(order):
 c=src.crop((i%3*src.width//3,[0,450,830][i//3],(i%3+1)*src.width//3,[450,830,1221][i//3]));yy,xx=np.nonzero(np.array(c)[:,:,3]>=160);box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));c=c.crop(box);size=tuple(round(v*.15) for v in c.size);arr=quantize(c,size,rgb,128)
 if n in (144,146,151,153,183):
  colors=np.array(c.resize(size,Image.Resampling.BOX))[:,:,:3].astype(np.int32);ids=[v for v in range(1,16) if v!=7];near=np.array(ids)[np.argmin(((colors[:,:,None,:]-rgb[None,None,ids,:])**2).sum(3),2)];arr[arr==7]=near[arr==7]
 yy,xx=np.nonzero(arr);left=round(48-(xx.min()+xx.max())/2);top=foot[n]-int(yy.max());canvas=np.zeros((80,96),np.uint8);canvas[top:top+size[1],left:left+size[0]]=arr
 im=save_image(canvas.tobytes(),(96,80),pal,out/f'frame_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);j=i+1;x=j%5*288;y=j//5*264;sheet.paste(im,(x,y+24),im);dr.text((x+8,y+5),str(n),fill='white')
 records.append({'frame':n,'image':f'frame_{n:03d}.png','source_box':box,'source_cell':i,'scale':.15,'size':size,'canvas_offset':[left,top],'opaque':int(np.count_nonzero(arr))})
sheet.save(out/'body_review.png');(out/'art.json').write_text(json.dumps({'palette_words':pal,'source_inventory':'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json','frames':records},indent=2));print(json.dumps(records))
