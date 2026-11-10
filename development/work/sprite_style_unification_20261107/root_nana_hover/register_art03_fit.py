"""One direct source quantization with uniform cell scale to correct generation framing."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore'),str(W/'nana_audit/base_run_repaint')]
from preview_restore import Archive,helper
from register_page import register
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((D/'input_audit.json').read_text('utf8'));order=json.loads((D/'art03_input_audit.json').read_text('utf8'))['pose_order'];source=D/'art03_generated.png';assert sha(source)=='a2af52fb5a283b0dfdf6226712229b9bc2ccb86e81e80ddb690c7ce3a9da112d'
parent=ROOT/m['input']['path'];assert sha(parent)==m['input']['sha256'];a=Archive(parent.read_bytes());im=Image.open(source).convert('RGBA')
out=D/'registered03_fit01';out.mkdir(exist_ok=False);rows=[];frames=[]
for cell,(n,mask)in enumerate(order):
 start=0 if mask==8 else 16;form='base_legs' if mask==8 else 'fourth';box=tuple(round(v)for v in((cell%2)*im.width/2,(cell//2)*im.height/2,(cell%2+1)*im.width/2,(cell//2+1)*im.height/2))
 pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
 z=np.zeros((384,384),np.uint8);z[120:195,124:199]=register(im.crop(box),(75,75),pal,'area_vote');pic=a.rgba(z,start);old=a.composite(n,mask)[0]
 Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png');pic.save(out/f'{form}_{n:03}_rgba.png')
 rows.append((f'{form} hover {n} registration',[('approved idle',a.composite(0,0 if mask==8 else 15)[0]),('current hover',old),('new uniform source fit',pic)]));frames.append({'ref':n,'form':form,'bbox':pic.getbbox(),'old_bbox':old.getbbox(),'source_crop':box,'source_cell_to_native':[75,75],'destination':[124,120],'prior_96_cell_scale_ratio':75/96,'axis_scales_equal':True})
for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
(out/'manifest.json').write_text(json.dumps({'source_sha256':sha(source),'source_size':list(im.size),'frames':frames,'accepted':False,'native_packed':False,'reason':'생성원화가 고정96셀에 몸72px를 점유해 기준56px보다 커짐. 새고해상도 원본에서 단1회 균일75셀 등록; 기존도트 확대/축소 재사용 없음. 발/눈/총구/공통층 후속검토.'},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(frames))
