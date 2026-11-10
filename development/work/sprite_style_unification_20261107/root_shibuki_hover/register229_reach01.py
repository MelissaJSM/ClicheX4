from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from scripts.export_x_consistency import Archive
from preview_restore import helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=D/'reach229_inputs03/generated_v1.png';assert sha(src)=='53e745de653b960a1680762a51db2b8915aced3cc0c6ce76b04c8161fd754465'
p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';assert sha(p)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e';a=Archive(p.read_bytes());im=Image.open(src).convert('RGBA');assert im.width==2*im.height
out=D/'reach229_registered01';out.mkdir(exist_ok=False);rows=[];frames=[]
for col,mask in enumerate((8,15)):
 start=0 if mask==8 else 16;form='base_legs'if mask==8 else'fourth';pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
 crop=im.crop((col*im.height,0,(col+1)*im.height,im.height));q=np.array(crop.resize((128,128),Image.Resampling.NEAREST));v=1+((q[:,:,:3].astype(np.float32)[:,:,None,:]-pal[None,None,1:,:])**2).sum(3).argmin(2).astype(np.uint8);v[q[:,:,3]<128]=0
 z=np.zeros((384,384),np.uint8);z[96:224,96:224]=v
 old=np.array(Image.open(D/'registered_neutral03'/f'{form}_229_nearest_indices.png'))
 region=np.zeros_like(old,bool);region[126:142,138:179]=True;region[142:153,138:150]=True;region[142:153,166:179]=True
 final=old.copy();final[region]=z[region];assert np.array_equal(final[153:],old[153:]);assert np.array_equal(final[142:153,150:166],old[142:153,150:166])
 for suffix,data in(('full',z),('local',final)):
  Image.fromarray(data).save(out/f'{form}_{suffix}_indices.png');a.rgba(data,start).save(out/f'{form}_{suffix}_rgba.png')
 Image.fromarray((region*255).astype(np.uint8)).save(out/f'{form}_edit_region.png')
 rows.append((form,[('original pose',a.composite(229,mask)[0]),('before ear/hand',a.rgba(old,start)),('generated full',a.rgba(z,start)),('local candidate',a.rgba(final,start))]))
 frames.append({'form':form,'bbox':a.rgba(final,start).getbbox(),'components8':int(label(final>0,np.ones((3,3)))[1]),'changed_pixels':int((old!=final).sum()),'protected_face_and_lower_exact':True,'body_translation':[0,0],'bbox_rescale':False})
helper.grid(rows,out/'comparison.png',6)
(out/'manifest.json').write_text(json.dumps({'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'parent_sha256':sha(p),'input_prompt':'reach229_inputs03/corrected_prompt.txt','excluded_guide':'미검증 green-box 좌표와 prompt.txt는 생성 입력에서 제외했다.','native_cell':128,'region_rectangles':[[138,126,179,142],[138,142,150,153],[166,142,179,153]],'frames':frames,'native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(frames))
