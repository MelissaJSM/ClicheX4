"""Fixed-cell quantization; retain the approved framing and game palette."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,helper
from register_page import register
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
m=read(D/'inputs_b01/manifest.json');data=(ROOT/m['parent_arc']).read_bytes();assert sha(data)==m['parent_sha256'];a=Archive(data)
source=D/'art_b01/generated.png';assert sha(source.read_bytes())=='63b98b4e7b749dc66d5dd76f4128a893a3dfe11538faeeb7d485e9762a8350e5';im=Image.open(source).convert('RGBA');assert im.getchannel('A').getextrema()==(0,255)
out=D/'registered_b01';out.mkdir(exist_ok=False);rows=[];frames=[]
for q in m['frames']:
 cell=q['cell'];start=16 if q['mask'] else 0;form=q['form'];n=q['ref'];box=tuple(round(v) for v in ((cell%2)*im.width/2,(cell//2)*im.height/2,(cell%2+1)*im.width/2,(cell//2+1)*im.height/2));cut=im.crop(box)
 pal=np.array([[((int(w)>>s)&31)*255//31 for s in (0,5,10)] for w in a.words[start:start+16]],np.float32)
 z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(cut,(96,96),pal,'area_vote');pic=a.rgba(z,start);old=a.composite(n,q['mask'],2)[0]
 Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png');pic.save(out/f'{form}_{n:03}_rgba.png')
 rows.append((f'{form} ride chaser pose {n}',[('accepted idle',a.composite(0,q['mask'],2)[0]),('current ride chaser pose',old),('new fixed cell',pic)]))
 frames.append({'form':form,'ref':n,'source_crop':box,'native_bbox':pic.getbbox(),'old_bbox':old.getbbox(),'body_translation':[0,0],'bbox_rescale':False,'indices_sha256':sha(z.tobytes()),'rgba_sha256':sha(pic.tobytes()),'components8':int(label(z>0,np.ones((3,3)))[1])})
for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
(out/'manifest.json').write_text(json.dumps({'source_sha256':sha(source.read_bytes()),'parent_sha256':m['parent_sha256'],'source_size':list(im.size),'method':'96x96 고정셀 면적투표, 네이티브15색+투명0. 얼굴/크기/손발 정합은 후속 검사.','frames':frames,'native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(frames))
