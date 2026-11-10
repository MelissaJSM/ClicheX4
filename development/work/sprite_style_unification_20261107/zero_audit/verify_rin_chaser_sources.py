"""체이서 원화/정합 재구성·거부·재현을 게임 파일 쓰기 없이 확인한다."""
from pathlib import Path
import sys,json,hashlib,struct,subprocess
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(D))
from scripts.prepare_rin_run import quantize
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
import pack_rin_chaser01 as producer
R=D/'rin_extension';A=R/'chaser_detail01';T=R/'chaser_contacts_probe_v1';P=R/'prepared_chaser01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
expected='99603ab0c003149a4fa415b3dcea78a0967a3be615d226471888bb3ece092a11';assert sha(P/'PL01_U.ARC')==expected
source=(R/'prepared_ride_heads02/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(source,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);im=Image.open(A/'generated.png').convert('RGBA');assert sha(A/'generated.png')=='bc3858a5cabda3f8b8f58be6e2599f1a88538d4f05701761f9a0e47cae94ad86';z=quantize(im,colors,1/8);reg=read(T/'registration.json');targets={};reconstructed=[]
for i,r in enumerate(reg['records']):
 n=r['ref'];a=np.zeros((384,384),np.uint8);a[120:184,112:208]=z[i//2*64:(i//2+1)*64,i%2*96:(i%2+1)*96];assert np.array_equal(a,np.array(Image.open(A/'native_fixed'/f'b1_{n:03}_indices.png')))
 for op in r['operations']:
  mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(op['polygon'],fill=1);mask=np.array(mask)&(a>0);layer=np.where(mask,a,0);a[mask]=0;dx,dy=op['translation'];mov=np.roll(np.roll(layer,dy,axis=0),dx,axis=1);a[mov>0]=mov[mov>0]
 assert np.array_equal(a,np.array(Image.open(T/f'b1_{n:03}_body_indices.png')));targets[n]=a;reconstructed.append({'ref':n,'source_reconstructed_exact':True,'operations':r['operations']})
out,_,worlds,_=producer.build(source);assert out==(P/'PL01_U.ARC').read_bytes()
rejects=[]
def reject(name,fn):
 try:fn()
 except (AssertionError,ValueError):rejects.append(name)
 else:raise AssertionError('Unexpected acceptance: '+name)
wrong=bytearray(source);wrong[0]^=1;reject('wrong_parent_hash',lambda:producer.build(bytes(wrong)))
reject('missing_master',lambda:producer.build(source,{k:v for k,v in targets.items()if k!=38}))
bad={k:v.copy()for k,v in targets.items()};bad[14][0,0]=1;reject('opaque_outside_body_windows',lambda:producer.build(source,bad))
bad={k:v.copy()for k,v in targets.items()};bad[14][150,149]=16;reject('palette_index16',lambda:producer.build(source,bad))
bad={k:v.copy()for k,v in targets.items()};bad[14]=bad[14].astype(np.int16);reject('wrong_pixel_dtype',lambda:producer.build(source,bad))
# Different process must reproduce all bytes; no output file is written there.
cmd=[sys.executable,'-c',"import sys,hashlib;from pathlib import Path;sys.path.insert(0,"+repr(str(D))+ ");import pack_rin_chaser01 as p;o,*_=p.build(p.P.read_bytes());print(hashlib.sha256(o).hexdigest())"]
cp=subprocess.run(cmd,cwd=ROOT,check=True,text=True,capture_output=True);assert cp.stdout.strip()==expected
plan=read(R/'rin259_v2_components.json');plan['resources']['PL01_U.ARC'].update(path=rel(P/'PL01_U.ARC'),after=expected);(R/'rin287_components.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
baseline=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];check=check_static_body(baseline,out,read(P/'proposal.json')['static_body_patch'])
proof={'passed':True,'candidate_sha256':expected,'source_reconstruction':reconstructed,'source_normalization':'fixed whole1536x1024 to192x128, alpha128 palette vote','28_original_ribbon_and_bob_exact':True,'meaningful_rejections':rejects,'separate_process_reproduction_exact':True,'static_binding':check,'runtime_verified':False,'user_accepted':False}
(R/'rin287_source_proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'rejections':rejects,'candidate':expected}))
