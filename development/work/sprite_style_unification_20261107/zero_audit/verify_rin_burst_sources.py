"""낙봉파7원화/국소신발색/원구체 재구성과 후보303 재현·거부 검사."""
from pathlib import Path
import sys,json,hashlib,struct,subprocess
import numpy as np
from PIL import Image
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(D))
from scripts.prepare_rin_run import quantize
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
import pack_rin_burst_remaining02 as producer
R=D/'rin_extension';P=R/'prepared_burst_remaining02';read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
EXPECTED='1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9';assert sha(P/'PL01_U.ARC')==EXPECTED
old=producer.P.read_bytes();pal=struct.unpack_from('<16H',entry(old,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);bodies={};records=[]
for page,reg,expected in [('burst_charge01','burst_charge_registered_v1','be785a35f9211044dab6c23efd59ba200a296569f57e25d49e9edbcdbe777e18'),('burst_recovery01','burst_recovery_registered_v1','eec875b4c047a679692856809014221dcec85309364eadb7362a9bcc82287f45')]:
 A=R/page;T=R/reg;assert sha(A/'generated.png')==expected;im=Image.open(A/'generated.png').convert('RGBA');assert im.size==(1536,1024);source=np.array(im);full=quantize(im,colors,1/8);info=read(A/'inputs.json');rr={x['ref']:x for x in read(T/'registration.json')['records']}
 for q in info['masters']:
  n=q['ref'];cx,cy=q['cell'];x0,y0,x1,y1=q['world_crop'];z=np.zeros((384,384),np.uint8);z[y0:y1,x0:x1]=full[cy*64:(cy+1)*64,cx*96:(cx+1)*96];assert np.array_equal(z,np.array(Image.open(A/'native_fixed'/f'b1_{n:03}_indices.png')))
  row=rr[n]
  for eye in row['source_eye_registration']:
   x,y=eye['world'];sx=(x-x0+cx*96)*8;sy=(y-y0+cy*64)*8;cell=source[sy:sy+8,sx:sx+8];r,g,b,al=[cell[:,:,k].astype(int)for k in range(4)];m=(al>=128)&(g>r+15)&(b>r+15)&(g>70)&(g>b*.65);expected_count=eye.get('count',eye.get('source_sample_count'));assert int(m.sum())==expected_count and expected_count>=14;assert z[y,x]==eye['old_index'];z[y,x]=15
  dx,dy=row['whole_body_translation'];z=np.roll(np.roll(z,dy,0),dx,1);assert np.array_equal(z,np.array(Image.open(T/f'b1_{n:03}_body_indices.png')));bodies[n]=z;records.append({'ref':n,'whole_canvas_scale':1/8,'source_sha256':expected,'actual_iris_cells':len(row['source_eye_registration']),'translation':[dx,dy],'registered_body_exact':True})
# Shoe-color edit: reproduce exact generated colors, not a hand-painted LUT replacement.
S=R/'burst_shoe_edit01';assert sha(S/'generated.png')=='ddd35dc51e12faa45cfb4048c7ab17798b0058bcbe5bd463b673220b47a62069';im=Image.open(S/'generated.png').convert('RGBA');assert im.size==(1536,1024);full=quantize(im,colors,1/8);info=read(R/'burst_charge01/inputs.json');reg={x['ref']:x for x in read(R/'burst_charge_registered_v1/registration.json')['records']};shoe=read(R/'burst_charge_registered_v2/registration.json');Y,X=np.indices((384,384));shoe_count=0
for q in info['masters']:
 n=q['ref'];cx,cy=q['cell'];x0,y0,x1,y1=q['world_crop'];z=np.zeros((384,384),np.uint8);z[y0:y1,x0:x1]=full[cy*64:(cy+1)*64,cx*96:(cx+1)*96];dx,dy=reg[n]['whole_body_translation'];z=np.roll(np.roll(z,dy,0),dx,1);base=bodies[n];mask=(Y>=173+dy)&(X>=130)&(X<193)&np.isin(base,(2,3,4,7,8))&np.isin(z,(4,5,6));want=base.copy();want[mask]=z[mask];changes=[{'world':[int(x),int(y)],'old_index':int(base[y,x]),'generated_index':int(z[y,x])}for y,x in np.argwhere(want!=base)];row=next(x for x in shoe['records']if x['ref']==n);assert changes==row['source_color_cells'];assert np.array_equal(want,np.array(Image.open(R/'burst_charge_registered_v2'/f'b1_{n:03}_body_indices.png')));assert np.array_equal(want>0,base>0) and np.array_equal(want[np.isin(base,(1,9,10,11))],base[np.isin(base,(1,9,10,11))]);bodies[n]=want;shoe_count+=len(changes)
assert shoe_count==154
histpath=ROOT/'work/ver_rin_nana/style_revision/v4_special/assembled_rise_burst_thrust_dashslash/verification.json';hist=read(histpath);inv=read(R/'burst_remaining_probe01/inventory.json');assert sha(histpath)==inv['historical_verification_sha256'];bodies[177]=render(old,1,5,101)[0];bodies[187]=bodies[186].copy();targets={};effects=[]
plan=read(R/'rin294_components.json');baseline=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC']
for row in inv['refs']:
 n=row['ref'];source=ROOT/row['body_source'];assert sha(source)==row['body_source_sha256'];small=np.array(Image.open(source));x,y,r,b=row['source_bounds'];dx=row['original_registration_dx'];body=np.zeros((384,384),np.uint8);body[160+y:160+b,160+x+dx:160+r+dx]=small
 if n==177:assert np.array_equal(body,render(baseline,1,5,101)[0])
 fx=np.zeros_like(body)
 for x,y,v in hist['embedded_charge_aura'].get(str(n),{}).get('world_pixels',[]):fx[160+y,160+x]=v
 assert np.array_equal(fx,np.array(Image.open(R/'burst_remaining_probe01'/f'b1_{n:03}_effect_indices.png')));oldcombined=body.copy();oldcombined[fx>0]=fx[fx>0];assert np.array_equal(oldcombined,render(old,1,5,n)[0]);want=bodies[n].copy();want[fx>0]=fx[fx>0];targets[n]=want;assert np.array_equal(want,np.array(Image.open(P/f'b1_{n:03}_indices.png')));effects.append({'ref':n,'historical_body_plus_effect_reconstructs_parent':True,'original_effect_world_pixels':int(np.count_nonzero(fx))})
assert sum(r['original_effect_world_pixels']for r in effects)==1064
out,_,_=producer.build(old);assert out==(P/'PL01_U.ARC').read_bytes();assert all(np.array_equal(targets[k],v)for k,v in producer.targets().items());rejects=[]
def reject(name,fn):
 try:fn()
 except (AssertionError,ValueError):rejects.append(name)
 else:raise AssertionError('Unexpected acceptance '+name)
bad=bytearray(old);bad[0]^=1;reject('wrong_parent_hash',lambda:producer.build(bytes(bad)))
reject('missing_registered_pose',lambda:producer.build(old,{k:v for k,v in targets.items()if k!=189}))
bad={k:v.copy()for k,v in targets.items()};bad[177][0,0]=1;reject('uncoverable_pixel',lambda:producer.build(old,bad))
bad={k:v.copy()for k,v in targets.items()};bad[177][142,155]=16;reject('palette_index16',lambda:producer.build(old,bad))
bad={k:v.copy()for k,v in targets.items()};bad[177]=bad[177].astype(np.int16);reject('wrong_dtype',lambda:producer.build(old,bad))
cp=subprocess.run([sys.executable,'-c',"import sys,hashlib;sys.path.insert(0,"+repr(str(D))+");import pack_rin_burst_remaining02 as p;o,*_=p.build(p.P.read_bytes());print(hashlib.sha256(o).hexdigest())"],cwd=ROOT,check=True,text=True,capture_output=True);assert cp.stdout.strip()==EXPECTED
plan['resources']['PL01_U.ARC'].update(path=rel(P/'PL01_U.ARC'),after=EXPECTED);(R/'rin303_v2_components.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8');static=check_static_body(baseline,out,read(P/'proposal.json')['static_body_patch'])
result={'passed':True,'candidate_sha256':EXPECTED,'new_body_source_reconstruction':records,'shoe_color_source_reconstruction_pixels':shoe_count,'all_shoe_alpha_geometry_white_highlights_and_dark_outline_preserved':True,'historical_effect_reconstruction':effects,'old177_equals_baseline101_proven':True,'old_head_pasted':False,'pose_bbox_scaling':False,'rejections':rejects,'separate_process_reproduction_exact':True,'static_binding':static,'runtime_verified':False,'user_accepted':False}
(R/'rin303_v2_source_proof.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'candidate':EXPECTED,'rejections':rejects,'shoe_pixels':shoe_count}))
