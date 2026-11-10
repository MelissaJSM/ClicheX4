from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore'),str(W/'nana_audit/base_run_repaint')]
from preview_restore import Archive,helper
from register_page import register
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((D/'input_audit.json').read_text('utf8'));order=json.loads((D/'art02_input_audit.json').read_text('utf8'))['pose_order'];source=D/'art02_generated.png'
assert sha(source)=='163409f93ed016ccb6af795829a64451c72b3e045fcabafb5193871a3c14aa46'
parent=ROOT/m['input']['path'];assert sha(parent)==m['input']['sha256'];a=Archive(parent.read_bytes())
im=Image.open(source).convert('RGBA');assert im.getchannel('A').getextrema()==(0,255)
out=D/'registered02';out.mkdir(exist_ok=False);rows=[];frames=[]
for cell,(n,mask) in enumerate(order):
 start=0 if mask==8 else 16;form='base_legs' if mask==8 else 'fourth';idle_mask=0 if mask==8 else 15
 box=tuple(round(v) for v in ((cell%2)*im.width/2,(cell//2)*im.height/2,(cell%2+1)*im.width/2,(cell//2+1)*im.height/2))
 pal=np.array([[((int(w)>>s)&31)*255//31 for s in (0,5,10)] for w in a.words[start:start+16]],np.float32)
 z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(im.crop(box),(96,96),pal,'area_vote')
 pic=a.rgba(z,start);old=a.composite(n,mask)[0]
 Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png');pic.save(out/f'{form}_{n:03}_rgba.png')
 rows.append((f'{form} hovering {n}',[('approved idle',a.composite(0,idle_mask)[0]),('current hovering',old),('new fixed cell',pic)]))
 frames.append({'ref':n,'mask':mask,'form':form,'source_crop':box,'bbox':pic.getbbox(),'old_bbox':old.getbbox(),'body_translation':[0,0],'bbox_rescale':False,'components8':int(label(z>0,np.ones((3,3)))[1]),'indices_sha256':hashlib.sha256(z.tobytes()).hexdigest()})
for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
(out/'manifest.json').write_text(json.dumps({'source':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source),'parent_sha256':sha(parent),'source_size':list(im.size),'frames':frames,'native_packed':False,'runtime_verified':False,'method':'고정96격자 면적투표·실제15색+투명. 체격/눈/발 접점은 후속 판정.'},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(frames))
