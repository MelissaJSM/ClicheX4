"""단독 회복 원화1254→96 팔레트 등록을 제작 함수 없이 검증."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';A=D/'bank1_recovery128';R=D/'bank1_recovery128_registered_v1';P=D/'prepared_bank1_recovery128'
sha=lambda b:hashlib.sha256(b).hexdigest();info=json.loads((A/'inputs.json').read_text('utf8'));reg=json.loads((R/'registration.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();new=(P/'PL01_U.ARC').read_bytes()
assert sha(arc)==info['archive_sha256']==reg['source_arc_sha256'];assert sha(new)=='07ec6077969f17d08c51ffd8e4326b476e1c6ab5635bea8420faee9528b39a89'
im=Image.open(A/'generated.png').convert('RGBA');assert im.size==(1254,1254)and sha((A/'generated.png').read_bytes())==reg['source_generated_sha256']=='7300247eb1281aaaaf71328c42043ab557ac5bc5040b3c6c7234a50ba21c1a28'
pal=struct.unpack_from('<16H',entry(arc,9));assert info['palette_words']==list(pal);colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);v=np.array(im);nearest=np.zeros(v.shape[:2],np.uint8)
for y in range(im.height):nearest[y]=1+np.sum((v[y,:,:3,None].transpose(0,2,1).astype(np.int32)-colors[None,:,:])**2,2).argmin(1)
votes=np.stack([np.array(Image.fromarray(np.where(nearest==i,v[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
alpha=np.array(im.getchannel('A').resize((96,96),Image.Resampling.BOX));cell=np.where(alpha>=128,votes.argmax(0)+1,0).astype(np.uint8);z=np.zeros((384,384),np.uint8);z[104:200,112:208]=cell
assert np.array_equal(z,np.array(Image.open(A/'native_fixed/b1_128_indices.png')));assert np.array_equal(z,np.array(Image.open(R/'b1_128_indices.png')))
assert reg['records'][0]['whole_translation']==[0,0]and reg['records'][0]['operations']==[]
old=render(arc,1,5,128)[0];assert z[154,143]==old[154,143]==15 and np.where(z>0)[0].max()==np.where(old>0)[0].max()==183
for n in(128,129,130,131):assert np.array_equal(z,render(new,1,5,n)[0]);assert np.array_equal(old,render(arc,1,5,n)[0])
j={'passed':True,'candidate_sha256':sha(new),'source_generated_sha256':reg['source_generated_sha256'],'source_cells_rebuilt':1,'display_targets_exact':4,'fixed_grid_reconstructed':True,'floor_and_eye_anchors_exact':True,'translations':0,'local_edits':0,'producer_functions_called':False,'old_head_override':False,'runtime_verified':False}
(D/'rin240_source_proof.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(j))
