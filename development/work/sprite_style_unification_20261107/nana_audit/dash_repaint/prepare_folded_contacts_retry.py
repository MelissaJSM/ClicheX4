"""Create edit guidance from authored shoes; no game asset is changed."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent; ROOT=D.parents[3]
sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,write,digest
from prepare_next_guides import body_path
O=D/'fourth_folded_contacts_inputs_v2';O.mkdir(exist_ok=True)
p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes())
sheet=Image.new('RGBA',(1536,1536));draw=ImageDraw.Draw(sheet)
configs={71:[((-7,20,-3,23),8),((2,19,4,21),3)],75:[((-3,20,1,23),4),((1,18,4,21),3)]}
for k,n in enumerate((71,75)):
 src=np.array(Image.open(D/'fourth_folded_registered_v1'/f'source_rgba8_{n:03}.png').convert('RGBA'))
 z=src.copy();y0=19 if n==71 else 18
 z[(y0+40)*8:64*8,28*8:49*8]=0
 for (x0,y0,x1,y1),dx in configs[n]:
  patch=src[(y0+40)*8:(y1+40)*8,(x0+40)*8:(x1+40)*8].copy()
  dest=z[(y0+40)*8:(y1+40)*8,(x0+dx+40)*8:(x1+dx+40)*8]
  m=patch[:,:,3]>0;dest[m]=patch[m]
 Image.fromarray(z).save(O/f'fixed_shoes_{n}.png')
 field=Image.fromarray(z).crop((0,64,640,576));sheet.alpha_composite(field,(k*768+64,160))
 draw.text((k*768+32,35),f'TARGET {n}: CONNECT KNEES TO FIXED SHOES. KEEP FACE/BODY.',fill=(90,100,110,255))
 native=a.rgba(np.array(Image.open(body_path(n)))).crop((120,128,200,192)).resize((640,512),Image.Resampling.NEAREST)
 sheet.alpha_composite(native,(k*768+64,928));draw.text((k*768+32,805),f'POSE REFERENCE {n}: FOOT POSITIONS ONLY. DO NOT COPY BOOTS.',fill=(90,100,110,255))
sheet.save(O/'edit_target_and_references.png')
write(O/'manifest.json',{'purpose':'새 포스 원화의 두 구두를 원래 발끝에 강체 이동한 편집 입력. 무릎과 구두 사이만 생성 도구로 연결하며 게임 그림이 아님.','shoe_translations':configs,'images':{q.name:digest(q) for q in O.glob('*.png')}})
