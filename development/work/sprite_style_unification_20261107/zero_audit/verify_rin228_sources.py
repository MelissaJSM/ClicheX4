"""원화 고정 셀/양자화/전신·앞팔 정합을 제작함수 없이 다시 계산한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';A=D/'bank1_special01';R=D/'bank1_special_registered_v1';P=D/'prepared_bank1_special01'
sha=lambda b:hashlib.sha256(b).hexdigest();info=json.loads((A/'inputs.json').read_text('utf8'));reg=json.loads((R/'registration.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();new=(P/'PL01_U.ARC').read_bytes()
assert sha(arc)==info['archive_sha256']==reg['source_arc_sha256'];assert sha(new)=='989b68597fa276164a16902806136f897c16ef3c1c81950b3b16fa039bede7a0'
im=Image.open(A/'generated.png').convert('RGBA');assert im.size==(1254,1254)and sha((A/'generated.png').read_bytes())==reg['source_generated_sha256']=='63045dd29f76bbed0f8b5e00c72d0cdfac45430dbce50dc0529f18b12c046da7'
pal=struct.unpack_from('<16H',entry(arc,9));assert info['palette_words']==list(pal);colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
shifts={91:(1,-3),93:(3,-3),101:(1,3),105:(4,2)};proof=[]
for f in info['frames']:
 n=f['ref'];cx,cy=f['cell'];crop=im.crop((cx*627,cy*627,(cx+1)*627,(cy+1)*627));v=np.array(crop);nearest=np.zeros(v.shape[:2],np.uint8)
 for y in range(627):nearest[y]=1+np.sum((v[y,:,:3,None].transpose(0,2,1).astype(np.int32)-colors[None,:,:])**2,2).argmin(1)
 votes=np.stack([np.array(Image.fromarray(np.where(nearest==i,v[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
 alpha=np.array(crop.getchannel('A').resize((96,96),Image.Resampling.BOX));cell=np.where(alpha>=128,votes.argmax(0)+1,0).astype(np.uint8);z=np.zeros((384,384),np.uint8);z[104:200,112:208]=cell
 assert np.array_equal(z,np.array(Image.open(A/'native_fixed'/f'b1_{n:03}_indices.png')))
 dx,dy=shifts[n];z=np.roll(z,(dy,dx),(0,1));assert np.array_equal(z,np.array(Image.open(A/'anchor_probe_v1'/f'b1_{n:03}_indices.png')))
 row=next(r for r in reg['records']if r['ref']==n)
 assert sha((ROOT/row['source_native']).read_bytes())==row['source_native_sha256']
 for op in row['operations']:
  mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(op['polygon'],fill=1);m=np.array(mask,bool);yy,xx=np.where(m);dx,dy=op['translation'];before=z.copy();z[m]=0;z[yy+dy,xx+dx]=before[yy,xx]
  assert np.count_nonzero(z!=before)==op['changed_pixels']
 png=R/f'b1_{n:03}_indices.png';assert sha(png.read_bytes())==row['output_sha256'];assert np.array_equal(z,np.array(Image.open(png)))
 aliases=[int(k.rsplit('_',1)[1])for k in f['exact_aliases']]
 for alias in aliases:assert np.array_equal(z,render(new,1,5,alias)[0]);assert np.array_equal(render(arc,1,5,n)[0],render(arc,1,5,alias)[0])
 assert np.nonzero(z)[0].max()==np.nonzero(render(arc,1,5,n)[0])[0].max()
 proof.append({'source_ref':n,'aliases':aliases,'fixed_grid_reconstructed':True,'floor_anchor_exact':True,'source_and_hand_negative_space_preserved':True})
j={'passed':True,'candidate_sha256':sha(new),'source_generated_sha256':reg['source_generated_sha256'],'source_cells_rebuilt':4,'display_targets_exact':6,'records':proof,'producer_functions_called':False,'old_head_override':False,'runtime_verified':False}
(D/'rin228_source_proof.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(j))
