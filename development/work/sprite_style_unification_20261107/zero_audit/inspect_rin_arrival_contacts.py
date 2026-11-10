"""등장 원화의 얼굴 원색/정합 후보를 읽기 표로 남긴다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
R=Path(__file__).parent/'rin_extension';A=R/'arrival_detail01';O=A/'contact_analysis';O.mkdir(exist_ok=True)
im=Image.open(A/'generated.png').convert('RGBA');a=np.array(im);s=im.width/192;info=json.loads((A/'inputs.json').read_text('utf8'));pal=struct.unpack_from('<16H',entry((ROOT/info['source']).read_bytes(),9));rows=[];board=Image.new('RGB',(1000,5*200),(35,38,48));dr=ImageDraw.Draw(board)
for i,m in enumerate(info['masters']):
 cx,cy=m['cell'];n=m['ref'];x0=cx*96+33;y0=cy*64+10;box=tuple(round(q*s)for q in(x0,y0,x0+23,y0+23));pic=im.crop(box);pic.thumbnail((400,190),Image.Resampling.NEAREST);board.paste(pic,(0,i*200),pic);dr.text((0,i*200),str(n),fill='white');cells=[]
 for y in range(cy*64+15,cy*64+34):
  for x in range(cx*96+34,cx*96+55):
   p=a[round(y*s):round((y+1)*s),round(x*s):round((x+1)*s)];r,g,b,alpha=[p[:,:,k].astype(int)for k in range(4)];mask=(alpha>=128)&(g>r+15)&(b>r+15)&(g>70)&(g>b*.65)
   if mask.any():cells.append({'world':[x-cx*96+112,y-cy*64+120],'count':int(mask.sum()),'area':int(mask.size),'mean':p[mask,:3].mean(axis=0).round(1).tolist()})
 rows.append({'ref':n,'cyan_source_cells':cells})
board.save(O/'generated_faces.png');j={'palette_rgb':[[int(w>>s&31)*255//31 for s in(0,5,10)]for w in pal],'cyan_cells':rows};(O/'source_eye_cells.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(j,ensure_ascii=False))
