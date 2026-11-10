"""생성 의상 시안의 팔레트/축척만 정규화한다. 손으로 새 그림을 그리지 않는다."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
d=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('--source',default='idle_generated.png');p.add_argument('--candidate',default='candidate01');args=p.parse_args()
out=d/args.candidate;out.mkdir(exist_ok=False)
colors=[(37,27,55),(63,45,85),(88,68,112),(126,96,165),(169,140,205),(211,190,237),(255,249,255),(198,220,242),(255,226,191),(242,195,102),(157,111,61),(211,75,96),(129,48,71),(72,65,76),(125,115,128)]
words=[0]+[0x8000|round(r*31/255)|(round(g*31/255)<<5)|(round(b*31/255)<<10) for r,g,b in colors]
rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
source=Image.open(d/args.source).convert('RGBA');rgba=np.array(source);ys,xs=np.nonzero(rgba[:,:,3]>=128);bb=[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1];crop=source.crop(bb);height=47;width=round(crop.width*height/crop.height)
data=np.array(crop);labels=np.zeros(data.shape[:2],np.uint8)
for y in range(crop.height):
 delta=data[y,:,:3].astype(np.int32)[:,None,:]-rgb[1:][None,:,:];labels[y]=np.argmin((delta*delta).sum(2),axis=1)+1
votes=[np.array(Image.fromarray(np.where(labels==i,data[:,:,3],0).astype(np.uint8)).resize((width,height),Image.Resampling.BOX)) for i in range(1,16)]
native=(np.argmax(np.stack(votes),axis=0)+1).astype(np.uint8);alpha=np.array(crop.getchannel('A').resize((width,height),Image.Resampling.BOX));native[alpha<128]=0
base=np.array(Image.open(d/'analysis/accepted_base_with_original_armor_bank0.png').convert('RGBA'));by,bx=np.nonzero(base[:,:,3]);bottom=int(by.max());feet=np.nonzero(base[bottom-2:bottom+1,:,3])[1];footcenter=(feet.min()+feet.max())/2
nf=np.nonzero(native[-3:])[1];left=round(footcenter-(nf.min()+nf.max())/2);top=bottom-height+1
canvas=np.zeros((160,160),np.uint8);canvas[top:top+height,left:left+width]=native
pic=save_image(canvas.tobytes(),(160,160),words,out/'full_outfit_indexed.png').convert('RGBA')
sheet=Image.new('RGB',(800,560),'#253546');draw=ImageDraw.Draw(sheet)
for i,(im,label) in enumerate([(Image.fromarray(base),'accepted base'),(pic,'new full outfit / normalization only')]):
 im=im.crop((55,50,105,110)).resize((400,480),Image.Resampling.NEAREST);sheet.paste(im,(i*400,35),im);draw.text((i*400+12,12),label,fill='white')
sheet.save(out/'comparison.png')
pic.crop((55,50,105,110)).resize((600,720),Image.Resampling.NEAREST).save(out/'outfit_12x.png')
(out/'normalization.json').write_text(json.dumps({'palette_words':words,'crop':bb,'native_size':[width,height],'position':[left,top],'base_bbox':[int(bx.min()),int(by.min()),int(bx.max()+1),int(by.max()+1)],'foot_center':float(footcenter),'quantization':'palette-area, RGB555, no dithering','game_applied':False},indent=2));print((out/'normalization.json').read_text())
