"""원화의 고정 셀/팔레트 표본/전신 정합을 제작함수 없이 재구성한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';A=D/'bank1_special02';R=D/'bank1_special02_registered_v1';P=D/'prepared_bank1_special02'
sha=lambda b:hashlib.sha256(b).hexdigest();info=json.loads((A/'inputs.json').read_text('utf8'));reg=json.loads((R/'registration.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();new=(P/'PL01_U.ARC').read_bytes()
assert sha(arc)==info['archive_sha256']==reg['source_arc_sha256'];assert sha(new)=='0f6073c262c0b851a1330b86fec51d1bae62838a73241b3e9140a0b7727a5d1e'
im=Image.open(A/'generated.png').convert('RGBA');assert im.size==(1254,1254)and sha((A/'generated.png').read_bytes())==reg['source_generated_sha256']=='97cd7913ab9092298259ba62800c5d090c1385985eb04a0d7b96ff4dd884cd22'
pal=struct.unpack_from('<16H',entry(arc,9));assert info['palette_words']==list(pal);colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
shifts={108:(-1,-3),110:(1,-3),112:(-1,0),119:(1,0)};proof=[]
for f in info['frames']:
 n=f['ref'];cx,cy=f['cell'];crop=im.crop((cx*627,cy*627,(cx+1)*627,(cy+1)*627));v=np.array(crop);nearest=np.zeros(v.shape[:2],np.uint8)
 for y in range(627):nearest[y]=1+np.sum((v[y,:,:3,None].transpose(0,2,1).astype(np.int32)-colors[None,:,:])**2,2).argmin(1)
 votes=np.stack([np.array(Image.fromarray(np.where(nearest==i,v[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
 alpha=np.array(crop.getchannel('A').resize((96,96),Image.Resampling.BOX));cell=np.where(alpha>=128,votes.argmax(0)+1,0).astype(np.uint8);z=np.zeros((384,384),np.uint8);z[104:200,112:208]=cell
 assert np.array_equal(z,np.array(Image.open(A/'native_fixed'/f'b1_{n:03}_indices.png')))
 dx,dy=shifts[n];z=np.roll(z,(dy,dx),(0,1));assert np.array_equal(z,np.array(Image.open(A/'anchor_probe_v1'/f'b1_{n:03}_indices.png')))
 row=next(r for r in reg['records']if r['ref']==n);assert sha((ROOT/row['source_native']).read_bytes())==row['source_native_sha256'];assert row['whole_translation']==[dx,dy]
 if n==119:
  assert len(row['operations'])==1;op=row['operations'][0];assert op['operation']=='semantic_eye_palette_vote'and op['xy']==[135,154]and op['before']==3 and op['after']==15
  xx,yy=135-112-dx,154-104-dy;assert int(votes[14,yy,xx])==op['source_cyan_weight']==92 and int(votes[:,yy,xx].max())==op['winner_weight']==99 and z[154,135]==3;z[154,135]=15
 else:assert not row['operations']
 png=R/f'b1_{n:03}_indices.png';assert sha(png.read_bytes())==row['output_sha256'];assert np.array_equal(z,np.array(Image.open(png)))
 aliases=[int(k.rsplit('_',1)[1])for k in f['exact_aliases']]
 for alias in aliases:assert np.array_equal(z,render(new,1,5,alias)[0]);assert np.array_equal(render(arc,1,5,n)[0],render(arc,1,5,alias)[0])
 assert np.nonzero(z)[0].max()==np.nonzero(render(arc,1,5,n)[0])[0].max()
 proof.append({'source_ref':n,'aliases':aliases,'fixed_grid_reconstructed':True,'floor_anchor_exact':True,'source_semantic_eye_samples':1 if n==119 else 0})
j={'passed':True,'candidate_sha256':sha(new),'source_generated_sha256':reg['source_generated_sha256'],'source_cells_rebuilt':4,'display_targets_exact':8,'records':proof,'producer_functions_called':False,'old_head_override':False,'runtime_verified':False}
(D/'rin236_source_proof.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(j))
