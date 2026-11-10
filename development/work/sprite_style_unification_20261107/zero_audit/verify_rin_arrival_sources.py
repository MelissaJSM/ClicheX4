"""등장원화 전체정규화·홍채표본·국소정합 및 준비ARC 재현/거부 검증."""
from pathlib import Path
import sys,json,hashlib,struct,subprocess
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(D))
from scripts.prepare_rin_run import quantize
from scripts.prepare_riko_ui import entry
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
import pack_rin_arrival01 as producer
R=D/'rin_extension';A=R/'arrival_detail01';T=R/'arrival_contacts_probe_v3';P=R/'prepared_arrival01';read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
expected='adf3b9475dd95cad5ff53ba627e4461dc9cb7ec18d202482b59744b0587c0322';assert sha(P/'PL01_U.ARC')==expected;source=producer.P.read_bytes();pal=struct.unpack_from('<16H',entry(source,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);im=Image.open(A/'generated.png').convert('RGBA');assert sha(A/'generated.png')=='bf30c20b17cb4002e980f8ef135ff96b0304adbd4a258f98bf9bdff16de89ac9';z=quantize(im,colors,192/im.width);full=np.array(im);s=im.width/192;reg1=read(R/'arrival_contacts_probe_v1/registration.json');reg3=read(T/'registration.json');targets={};records=[]
for i,r in enumerate(reg1['records']):
 n=r['ref'];cx=i%2;cy=i//2;a=np.zeros((384,384),np.uint8);a[120:184,112:208]=z[cy*64:(cy+1)*64,cx*96:(cx+1)*96];assert np.array_equal(a,np.array(Image.open(A/'native_fixed'/f'b0_{n:03}_indices.png')))
 for eye in r['actual_source_eye_samples']:
  x,y=eye['world'];sx=x-112+cx*96;sy=y-120+cy*64;cell=full[round(sy*s):round((sy+1)*s),round(sx*s):round((sx+1)*s)];rr,gg,bb,aa=[cell[:,:,k].astype(int)for k in range(4)];mask=(aa>=128)&(gg>rr+15)&(bb>rr+15)&(gg>70)&(gg>bb*.65);assert mask.sum()==eye['count'] and mask.sum()>=20;assert int(a[y,x])==eye['old_quantized_index'];a[y,x]=15
 dx,dy=r['whole_body_translation'];a=np.roll(np.roll(a,dy,0),dx,1);assert np.array_equal(a,np.array(Image.open(R/f'arrival_contacts_probe_v1/b0_{n:03}_indices.png')))
 q=next(v for v in reg3['records']if v['ref']==n)
 for op in q['operations']:
  mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(op['polygon'],fill=1);mask=np.array(mask)&(a>0);assert int(mask.sum())==op['source_pixels'];layer=np.where(mask,a,0);a[mask]=0;dx,dy=op['translation'];m=np.roll(np.roll(layer,dy,0),dx,1);assert int(np.count_nonzero((m>0)&(a>0)))==op['new_source_overlap'];a[m>0]=m[m>0]
 assert np.array_equal(a,np.array(Image.open(T/f'b0_{n:03}_indices.png')));targets[n]=a;records.append({'ref':n,'source_normalization_exact':True,'actual_generated_iris_samples':len(r['actual_source_eye_samples']),'whole_translation':r['whole_body_translation'],'local_operations':q['operations'],'registered_target_exact':True})
out,_,_=producer.build(source);assert out==(P/'PL01_U.ARC').read_bytes();rejects=[]
def reject(name,fn):
 try:fn()
 except (AssertionError,ValueError):rejects.append(name)
 else:raise AssertionError('Unexpected acceptance '+name)
bad=bytearray(source);bad[0]^=1;reject('wrong_parent_hash',lambda:producer.build(bytes(bad)))
reject('missing_pose',lambda:producer.build(source,{k:v for k,v in targets.items()if k!=253}))
bad={k:v.copy()for k,v in targets.items()};bad[249][0,0]=1;reject('outside_tile_windows',lambda:producer.build(source,bad))
bad={k:v.copy()for k,v in targets.items()};bad[249][142,155]=16;reject('palette_index16',lambda:producer.build(source,bad))
bad={k:v.copy()for k,v in targets.items()};bad[249]=bad[249].astype(np.int16);reject('wrong_dtype',lambda:producer.build(source,bad))
cp=subprocess.run([sys.executable,'-c',"import sys,hashlib;sys.path.insert(0,"+repr(str(D))+");import pack_rin_arrival01 as p;o,*_=p.build(p.P.read_bytes());print(hashlib.sha256(o).hexdigest())"],cwd=ROOT,check=True,text=True,capture_output=True);assert cp.stdout.strip()==expected
plan=read(R/'rin287_components.json');plan['resources']['PL01_U.ARC'].update(path=rel(P/'PL01_U.ARC'),after=expected);(R/'rin294_components.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
baseline=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];static=check_static_body(baseline,out,read(P/'proposal.json')['static_body_patch'])
proof={'passed':True,'candidate_sha256':expected,'source_reconstruction':records,'source_whole_canvas_scale':192/im.width,'source_actual_size':im.size,'old_head_pasted':False,'body_scale_per_pose':False,'parent_flash_rule_exact':True,'rejections':rejects,'separate_process_reproduction_exact':True,'static_binding':static,'runtime_verified':False,'user_accepted':False};(R/'rin294_source_proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'candidate':expected,'rejections':rejects}))
