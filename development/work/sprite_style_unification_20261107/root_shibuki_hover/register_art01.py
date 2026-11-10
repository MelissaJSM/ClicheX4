"""Register the first four authored hover cells on their fixed native lattice."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(W/'nana_audit/base_run_repaint'),str(W/'nana_audit/native_restore')]
from scripts.export_x_consistency import Archive
from preview_restore import helper
from register_page import register
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=D/'art01_generated.png';assert sha(src)=='c3d23700267209f703c89c6b1d2d040785f0854ef1cdc71caf541031d29f3a80'
p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';assert sha(p)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
a=Archive(p.read_bytes());im=Image.open(src).convert('RGBA');assert im.getchannel('A').getextrema()==(0,255)
out=D/'registered01';out.mkdir(exist_ok=False);rows=[];frames=[]
for cell,(n,mask)in enumerate(((221,8),(221,15),(223,8),(223,15))):
    form='base_legs'if mask==8 else'fourth';start=0 if mask==8 else 16
    box=tuple(round(v)for v in(cell%2*im.width/2,cell//2*im.height/2,(cell%2+1)*im.width/2,(cell//2+1)*im.height/2))
    pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
    z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(im.crop(box),(96,96),pal,'area_vote');pic=a.rgba(z,start);old=a.composite(n,mask)[0]
    Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png');pic.save(out/f'{form}_{n:03}_rgba.png')
    rows.append((f'{form} hover {n}',[('approved idle',a.composite(0,mask)[0]),('current',old),('new fixed lattice',pic)]))
    frames.append({'ref':n,'mask':mask,'form':form,'source_crop':box,'bbox':pic.getbbox(),'old_bbox':old.getbbox(),'components8':int(label(z>0,np.ones((3,3)))[1]),'indices_sha256':hashlib.sha256(z.tobytes()).hexdigest(),'body_translation':[0,0],'bbox_rescale':False})
for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
(out/'manifest.json').write_text(json.dumps({'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'source_size':list(im.size),'parent_sha256':sha(p),'method':'고정96셀 면적투표. 기존15색+투명. 자동bbox스케일 없음.','frames':frames,'native_packed':False,'runtime_verified':False,'limits':['눈/발의 최종 정합과 부분별 소유는 다음 단계다.']},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(frames))
