from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'rear_continuation01/anchor_review';O.mkdir(exist_ok=True)
arc=(D/'prepared_third_saber_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));rows=[]
wrists={178:[(148,127,158,134),(166,137,177,146)],182:[(166,130,178,139)],186:[(165,129,175,140),(144,142,154,153)],190:[(167,138,176,147),(146,140,156,150)]}
legs={178:(158,164,168,179),182:(149,165,162,179),186:(155,167,169,180),190:(157,162,171,177)}
for n in wrists:
 old=render(arc,0,0,n)[0];new=np.array(Image.open(D/f'rear_continuation01/native/b0_{n:03}_indices.png'))
 row={'ref':n,'wrists':[],'standing_leg_rows':[]}
 for box in wrists[n]:
  x0,y0,x1,y1=box;stats=[]
  for a in(old,new):
   y,x=np.nonzero(np.isin(a[y0:y1,x0:x1],(12,13,14)));stats.append({'count':len(x),'centroid':[float(x.mean()+x0),float(y.mean()+y0)]if len(x)else None,'bbox':[int(x.min()+x0),int(y.min()+y0),int(x.max()+x0+1),int(y.max()+y0+1)]if len(x)else None})
  row['wrists'].append({'roi':box,'before':stats[0],'after':stats[1],'delta':[round(stats[1]['centroid'][i]-stats[0]['centroid'][i],3)for i in(0,1)]if all(s['count']for s in stats)else None})
 x0,y0,x1,y1=legs[n]
 for y in range(y0,y1):
  spans=[]
  for a in(old,new):
   xs=np.where(a[y,x0:x1]>0)[0]+x0;spans.append([int(xs.min()),int(xs.max())]if len(xs)else None)
  row['standing_leg_rows'].append({'y':y,'before':spans[0],'after':spans[1]})
 rows.append(row)
box=(140,120,182,182);scale=10;cell=(470,680);out=Image.new('RGB',(940,2720),(77,87,104));dr=ImageDraw.Draw(out)
for i,n in enumerate(wrists):
 for j,a in enumerate((render(arc,0,0,n)[0],np.array(Image.open(D/f'rear_continuation01/native/b0_{n:03}_indices.png')))):
  pic=rgba(a,pal).crop(box).resize((420,620),Image.Resampling.NEAREST);x=j*470+35;y=i*680+28;out.paste(pic,(x,y),pic);dr.text((x,y-22),f'{n} '+('before'if j==0 else'new'),fill='white')
  for xx in range(box[0],box[2],2):dr.text((x+(xx-box[0])*scale,y-12),str(xx),fill='white')
  for yy in range(box[1],box[3],2):dr.text((x-27,y+(yy-box[1])*scale),str(yy),fill='white')
  for xx in range(box[0],box[2]+1):dr.line((x+(xx-box[0])*scale,y,x+(xx-box[0])*scale,y+620),fill=(40,48,61))
  for yy in range(box[1],box[3]+1):dr.line((x,y+(yy-box[1])*scale,x+420,y+(yy-box[1])*scale),fill=(40,48,61))
out.save(O/'joint_grid.png');(O/'source_vs_generic.json').write_text(json.dumps({'rows':rows,'scope':'피부 색인 표본과 지정 다리 ROI의 행별 외곽을 비교한다. 명암 위치 변화는 골격 이동과 구분해 해석해야 한다.'},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rows))
