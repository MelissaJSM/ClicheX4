"""대시 8포즈에 하나의 축척을 적용하고 대기 접지/머리 기준에 등록한다."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
d=Path(__file__).parent;out=d/'normalized02';out.mkdir(exist_ok=True)
src=Image.open(d/'generated.png').convert('RGBA');pal=json.loads((ROOT/'work/ver_buki_riko/shibuki_art/idle_chubby_v2/candidate09/candidate.json').read_text())['palette_words']
rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32)
numbers=[67,69,71,75,77,79,81,83];cells=[]
for i,n in enumerate(numbers):
    x,y=i%4,i//4;chosen=Image.open(d/'compact_generated.png').convert('RGBA') if n in (71,75) else src;cell=chosen.crop((x*src.width//4,y*src.height//2,(x+1)*src.width//4,(y+1)*src.height//2));a=np.array(cell)
    yy,xx=np.nonzero(a[:,:,3]>=160);bb=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));cells.append((n,cell.crop(bb),bb))
scale=47/cells[-1][1].height
sheet=Image.new('RGB',(5*288,2*264),'#28394b');draw=ImageDraw.Draw(sheet);records=[]
eyes={67:41,69:36,71:31,75:31,77:38,79:43,81:43,83:43}
for i,(n,crop,bb) in enumerate(cells):
    size=tuple(round(v*scale) for v in crop.size);a=quantize(crop,size,rgb,128);ey,ex=np.nonzero(a==7)
    if not len(ex):raise ValueError('No eye')
    yy,xx=np.nonzero(a);left=round(eyes[n]-float(np.median(ex)));top=62-int(yy.max());canvas=np.zeros((80,96),np.uint8)
    if left<0 or left+size[0]>96 or top<0:raise ValueError('Clipped frame')
    canvas[top:top+size[1],left:left+size[0]]=a;im=save_image(canvas.tobytes(),(96,80),pal,out/f'run_{n:03d}.png').convert('RGBA')
    x=(i%4+1)*288;y=i//4*264;sheet.paste(im.resize((288,240),Image.Resampling.NEAREST),(x,y+24),im.resize((288,240),Image.Resampling.NEAREST));draw.text((x+8,y+5),str(n),fill='white')
    records.append({'frame':n,'image':f'run_{n:03d}.png','source_box':bb,'scale':scale,'size':size,'canvas_offset':[left,top],'eye_canvas':[eyes[n],float(np.median(ey)+top)],'registration':'artistic forward lean; floor62 and idle eye43; not extracted X coordinates'})
for row in range(2):
    im=Image.open(d.parent/'standing_buster_v1/parent_000.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,(0,row*264+24),im);draw.text((8,row*264+5),'ACCEPTED IDLE',fill='white')
sheet.save(out/'review.png');(out/'art.json').write_text(json.dumps({'frames':records,'palette_words':pal,'source_inventory':'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json'},indent=2));print(json.dumps({'scale':scale,'frames':records}))
