"""신규 낙봉파 준비4의 원화 신발색과 실제 색인 역할을 읽기 비교한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import rgba,render
R=D/'rin_extension';A=R/'burst_charge01';O=R/'burst_shoe_audit01';O.mkdir(exist_ok=True)
info=json.loads((A/'inputs.json').read_text('utf8'));src=np.array(Image.open(A/'generated.png').convert('RGBA'));arc=(ROOT/info['source_arc']).read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));rows=[]
sheet=Image.new('RGB',(1600,4*340),'#566476');dr=ImageDraw.Draw(sheet)
for i,rec in enumerate(info['masters']):
 n=rec['ref'];cx,cy=rec['cell'];crop=rec['world_crop'];z=np.array(Image.open(A/'native_fixed'/f'b1_{n:03}_indices.png'));reg=np.array(Image.open(R/'burst_charge_registered_v1'/f'b1_{n:03}_body_indices.png'))
 # Foot diagnostic bounding region; not an editing mask. Includes shins.
 bb=(130,169,193,184);box=(bb[0]-crop[0]+cx*96,bb[1]-crop[1]+cy*64,bb[2]-crop[0]+cx*96,bb[3]-crop[1]+cy*64)
 p=Image.fromarray(src).crop(tuple(v*8 for v in box));back=Image.new('RGB',p.size,'#566476');back.paste(p,(0,0),p);sheet.paste(back,(0,i*340+28))
 pic=rgba(z,pal).crop(bb).resize((630,150),Image.Resampling.NEAREST);sheet.paste(pic,(530,i*340+28),pic)
 for y in range(169,184):
  for x in range(130,193):
   v=int(z[y,x]);
   if v:dr.text((530+(x-130)*10,i*340+195+(y-169)*8),format(v,'X'),fill=tuple(int(c)for c in((255,255,0)if v in(4,5,6)else(230,230,230))))
 means=[]
 for y,x in np.argwhere((z>0)&(np.indices(z.shape)[0]>=173)):
  sx=(x-crop[0]+cx*96)*8;sy=(y-crop[1]+cy*64)*8;cell=src[sy:sy+8,sx:sx+8];opaque=cell[:,:,3]>=128
  if opaque.any():means.append({'world':[int(x),int(y)],'index':int(z[y,x]),'source_mean_rgb':cell[opaque,:3].mean(0).round(1).tolist()})
 hist={str(v):int(np.count_nonzero((z==v)&(np.indices(z.shape)[0]>=173)))for v in range(1,16)}
 rows.append({'ref':n,'diagnostic_region_only':[130,173,193,184],'native_index_histogram':hist,'source_cells':means})
 dr.text((0,i*340+5),f'{n} original generated RGB (8x) / native indexed (10x) / native indices',fill='white')
sheet.save(O/'source_feet_and_indices.png')
result={'source_sha256':hashlib.sha256((A/'generated.png').read_bytes()).hexdigest(),'palette':{i:[(w>>s&31)*255//31 for s in(0,5,10)]for i,w in enumerate(pal)},'records':rows,'observation':'원화의 신발 가죽 자체가 대기보다 채도가 낮은 남색/회청색으로 생성됐다. 단순 RGB 최근접 등록은 이 색을 대기 신발 역할4/5/6보다 상의/회색 음영1/2/3/7/8로 선택한다. 따라서 원화의 신발 색 역할도 보완해야 하며 일반 양자화 손실만이라고 설명하지 않는다. 이 파일은 조사이며 그림을 수정하지 않는다.'}
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps([{'ref':r['ref'],'blue456':sum(r['native_index_histogram'][str(v)]for v in(4,5,6)),'hist':r['native_index_histogram']}for r in rows]))
