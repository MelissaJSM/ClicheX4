"""고정 셀 원화 등록. 접점 검토용이며 게임 자원은 쓰지 않는다."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1]
sys.path[:0]=[str(D),str(ROOT),str(W/'nana_audit/native_restore')]
from register_neutral import quantize
from prepare_body_layers04 import Archive,comp
from preview_restore import helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC'
assert sha(p)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
a=Archive(p.read_bytes());out=D/'shot_registered01';out.mkdir(exist_ok=False);records=[]
for page,refs in enumerate(((222,224),(226,228),(230,)),1):
 src=D/f'shot_inputs01/page{page:02}'/('generated_cleanup01.png' if page==1 else 'generated_v1.png')
 im=Image.open(src).convert('RGBA');rows=[]
 for row,n in enumerate(refs):
  ls={pb:np.array(Image.open(D/f'body_layers_probe04/layer{pb}_{n-1:03}.png'))for pb in(0,5,6,7,8)}
  for col,(form,mask,start)in enumerate((('base_legs',8,0),('fourth',15,16))):
   crop=tuple(round(v)for v in(col*im.width/2,row*im.height/len(refs),(col+1)*im.width/2,(row+1)*im.height/len(refs)))
   pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
   z=np.zeros((384,384),np.uint8);z[112:208,112:208]=quantize(im.crop(crop),pal,'nearest')
   Image.fromarray(z).save(out/f'{form}_{n}_source_indices.png');pic=a.rgba(z,start);pic.save(out/f'{form}_{n}_source_rgba.png')
   rows.append((f'{form} {n}',[('idle',a.composite(0,mask)[0]),('protected new body',comp(a,ls,mask)),('registered shooting donor',pic),('old shot pose',a.composite(n,mask)[0])]))
   records.append({'ref':n,'form':form,'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'source_crop':crop,'output_sha256':sha(out/f'{form}_{n}_source_indices.png'),'native_cell':96,'body_translation':[0,0],'bbox_rescaled':False})
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{refs[i//2]}.png',5)
(out/'manifest.json').write_text(json.dumps({'parent_sha256':sha(p),'records':records,'native_packed':False,'runtime_verified':False,'scope':'생성 원화의 고정 셀 등록만 수행. 이후 팔·공통 얼굴·하체·총구 영역을 검토하여 합성해야 한다.'},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'registered':len(records),'native_packed':False}))
