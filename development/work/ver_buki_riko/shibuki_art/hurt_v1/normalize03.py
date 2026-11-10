import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
d=Path(__file__).parent;out=d/'production03';out.mkdir(exist_ok=False)
src=Image.open(d/'compact_generated.png').convert('RGBA');pal=json.loads((d.parent/'idle_chubby_v2/candidate09/candidate.json').read_text())['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32)
scale=.066;records=[];sheet=Image.new('RGB',(3*288,264),'#28394b');draw=ImageDraw.Draw(sheet)
for i,n in enumerate((106,110)):
 chosen=Image.open(d/'tucked_generated.png').convert('RGBA') if n==110 else src
 c=chosen.crop((i*src.width//2,0,(i+1)*src.width//2,src.height));yy,xx=np.nonzero(np.array(c)[:,:,3]>=160);bb=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));c=c.crop(bb);size=tuple(round(v*scale) for v in c.size);a=quantize(c,size,rgb,128)
 colors=np.array(c.resize(size,Image.Resampling.BOX))[:,:,:3].astype(np.int32);choices=[v for v in range(1,16) if v!=7];nearest=np.array(choices)[np.argmin(((colors[:,:,None,:]-rgb[None,None,choices,:])**2).sum(3),2)];a[a==7]=nearest[a==7]
 yy,xx=np.nonzero(a);left=round(46-(xx.min()+xx.max())/2) if n==106 else round(48-(xx.min()+xx.max())/2);top=63-int(yy.max()) if n==106 else 60-int(yy.max())
 canvas=np.zeros((80,96),np.uint8);canvas[top:top+size[1],left:left+size[0]]=a;im=save_image(canvas.tobytes(),(96,80),pal,out/f'frame_{n:03d}.png').convert('RGBA');im=im.resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,((i+1)*288,24),im);draw.text(((i+1)*288+8,5),str(n),fill='white')
 records.append({'frame':n,'image':f'frame_{n:03d}.png','scale':scale,'source_box':bb,'size':size,'canvas_offset':[left,top],'opaque_pixels':int(np.count_nonzero(a)),'registration':'normal recoil foot row63; airborne recoil foot row60; original body center retained'})
im=Image.open(d.parent/'standing_buster_v1/parent_000.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,(0,24),im);draw.text((8,5),'ACCEPTED IDLE',fill='white');sheet.save(out/'body_review.png')
(out/'art.json').write_text(json.dumps({'frames':records,'palette_words':pal,'source_inventory':'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json'},indent=2),encoding='utf-8');print(records)
