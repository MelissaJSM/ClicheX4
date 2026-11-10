"""린 낙봉파9 독립 reader. 제작/패킹 함수를 호출하지 않는다."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_frame_edit import frame_coverage
D=ROOT/'work/sprite_style_unification_20261107/zero_audit/rin_extension'
P=D/'prepared_burst_remaining01';B=D/'prepared_arrival01'
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
def png(p):
 z=np.array(Image.open(p));assert z.shape==(384,384) and z.dtype==np.uint8 and z.max()<=15;return z
def raw(g,f):return decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
def atlas(r,count):return np.frombuffer(indexed_atlas(r,count)[0],np.uint8).reshape(-1,256)
def tile(a,t):return a[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
def main():
 old=(B/'PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes()
 assert sha(old)=='adf3b9475dd95cad5ff53ba627e4461dc9cb7ec18d202482b59744b0587c0322'
 assert sha(new)=='626a059f3a290d5d15f647aa6bbb8b9be51e88060638d6a14d62a34508835f6a'
 prop=read(P/'proposal.json');assert prop['source_arc_sha256']==sha(old) and prop['after_sha256']==sha(new)
 g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3)
 assert replace_entry(replace_entry(new,2,g),3,c)==old
 assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
 assert bank_offsets(c,allow_aliases=True)==bank_offsets(nc,allow_aliases=True)
 historical=ROOT/'work/ver_rin_nana/style_revision/v4_special'
 inventory=read(D/'burst_remaining_probe01/inventory.json')
 hp=historical/'assembled_rise_burst_thrust_dashslash/verification.json'
 assert sha(hp.read_bytes())==inventory['historical_verification_sha256']
 hist=read(hp);targets={};effects={};sources=[];effect_count=0
 for n in [177,178,179,180,181,186,187,188,189]:
  # 이전 몸체+효과를 당시 등록표에서 독립 재구성해 효과 마스크 출처를 인증한다.
  source=101 if n==177 else 186 if n==187 else n
  folder=historical/('thrust' if n==177 else 'burst');rec=read(folder/'registered.json')['frames'][str(source)]
  path=folder/rec['file'];assert sha(path.read_bytes())==rec['sha256']
  x,y,r,b=rec['bounds'];small=np.array(Image.open(path));assert small.shape==(b-y,r-x)
  dx=hist['burst_contact_registration'][str(186 if n==187 else n)]['translate_x']
  oldbody=np.zeros((384,384),np.uint8);oldbody[160+y:160+b,160+x+dx:160+r+dx]=small
  fx=np.zeros_like(oldbody)
  for xx,yy,v in hist['embedded_charge_aura'].get(str(n),{}).get('world_pixels',[]):fx[160+yy,160+xx]=v
  assembled=oldbody.copy();assembled[fx>0]=fx[fx>0];assert np.array_equal(assembled,render(old,1,5,n)[0])
  assert np.array_equal(fx,png(D/'burst_remaining_probe01'/f'b1_{n:03}_effect_indices.png'))
  effects[n]=fx;effect_count+=int(np.count_nonzero(fx))
  if n==177:
   body=render(old,1,5,101)[0];path=D/'burst177_reuse_probe01/b1_177_body_indices.png';assert np.array_equal(body,png(path))
  else:
   targetref=186 if n==187 else n
   folder=D/('burst_charge_registered_v1' if n<182 else 'burst_recovery_registered_v1')
   path=folder/f'b1_{targetref:03}_body_indices.png';body=png(path)
   reg=next(q for q in read(folder/'registration.json')['records'] if q['ref']==targetref)
   assert sha(path.read_bytes())==reg['target_sha256']
  target=body.copy();target[fx>0]=fx[fx>0];targets[n]=target
  expected=P/f'b1_{n:03}_indices.png';assert sha(expected.read_bytes())==prop['target_sha256'][str(n)]
  assert np.array_equal(target,png(expected)) and np.array_equal(target,render(new,1,5,n)[0])
  sources.append({'ref':n,'registered_body':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes()),'effect_pixels':int(np.count_nonzero(fx))})
 assert effect_count==1064 and np.array_equal(targets[186],targets[187])
 fs=graphics_bank(g,1)['frames'];ns=graphics_bank(ng,1)['frames'];permitted=set();moves=[];groups=[];gpu=0;unused=0
 for ids,count in [([177,178,179],30),([180,181],30),([186,187],17),([188,189],18)]:
  f,nf=fs[ids[0]],ns[ids[0]];assert f['tile_count']==nf['tile_count']==count
  assert [q['index'] for q in fs if q['offset']==f['offset']]==ids
  assert [q['index'] for q in ns if q['offset']==nf['offset']]==ids
  rr,nr=raw(g,f),raw(ng,nf);aa,zz=atlas(rr,count),atlas(nr,count);owned=set()
  for n in ids:
   oc,cp=composition_frame(c,5,n),composition_frame(nc,5,n);assert len(oc['parts'])==len(cp['parts'])
   for op,np_ in zip(oc['parts'],cp['parts']):
    if n in (177,179,188,189):
     assert {k:v for k,v in op.items() if k not in ('x','y')}=={k:v for k,v in np_.items() if k not in ('x','y')}
     permitted.update((op['record_offset']+2,op['record_offset']+3))
     if (op['x'],op['y'])!=(np_['x'],np_['y']):moves.append({'ref':n,'tile':op['tile'],'old_xy':[op['x'],op['y']],'new_xy':[np_['x'],np_['y']]})
    else:assert op==np_
    ot,nt=tile(aa,np_['tile']),tile(zz,np_['tile'])
    assert not(np_['tile']%16==0 and np.any((nt[:,0]>0)&(ot[:,0]==0)))
    assert not(np_['flip_y'] and np.any((nt[0]>0)&(ot[0]==0)));gpu+=1
   coverage,_,_=frame_coverage(rr,count,cp);owned.update(s for cell in coverage for s in cell)
   fx=effects[n];assert np.array_equal(render(new,1,5,n)[0][fx>0],fx[fx>0])
  for i in range(len(rr)*2):
   byte,shift=i//2,i%2*4
   if (byte,shift) not in owned:assert (rr[byte]>>shift&15)==(nr[byte]>>shift&15);unused+=1
  groups.append({'refs':ids,'tile_count':count,'original_shared_stream_preserved':True})
 diffs={i for i,(x,y) in enumerate(zip(c,nc)) if x!=y};assert diffs<=permitted and len(diffs)==52
 assert moves==prop['verification']['tile_window_moves']
 counts=collections.Counter()
 for b in (0,1):
  for f,nf in zip(graphics_bank(g,b)['frames'],graphics_bank(ng,b)['frames']):
   n=f['index'];selected=b==1 and n in targets;assert f['tile_count']==nf['tile_count']<=32;counts['raw']+=1
   if selected:assert raw(g,f)!=raw(ng,nf)
   else:
    assert raw(g,f)==raw(ng,nf);counts['non_target_raw_exact']+=1
    assert composition_frame(c,b*5,n)==composition_frame(nc,b*5,n)
   if b==1 and 42<=n<=49:counts['partial8_exact']+=1;continue
   counts['display']+=1
   if selected:assert np.array_equal(render(new,b,b*5,n)[0],targets[n]);counts['target_exact']+=1
   else:assert np.array_equal(render(old,b,b*5,n)[0],render(new,b,b*5,n)[0]);counts['non_target_display_exact']+=1
 assert dict(counts)=={'raw':444,'non_target_raw_exact':435,'display':436,'non_target_display_exact':427,'partial8_exact':8,'target_exact':9}
 for name in ('palette.bin','effect_23.png','effect_24.png'):assert (B/name).read_bytes()==(P/name).read_bytes()
 result={'passed':True,'producer_functions_called':False,'source_arc_sha256':sha(old),'candidate_sha256':sha(new),'counts':dict(counts),
  'registered_sources':sources,'groups':groups,'original_effect_world_pixels_exact':effect_count,'historical_effect_source_reconstructed':True,
  'unconsumed_nibbles_exact':unused,'only_original_tile_window_xy_bytes':len(diffs),'tile_window_moves':moves,'gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,
  'all_other_entries_palette_audio_exact':True,'external_static_effects_exact':True,'original_tile_counts_bank_boundaries_exact':True,
  'visual_review_performed':False,'generated_art_reconstructed':False,'native_cpu_run_performed':False,'runtime_verified':False,
  'scope':'등록된 새7몸체와 현재101 재사용·186/187사본에서9표시를 독립 재구성했다. 당시 원화기록으로 인증한 원구체1064화소와 비대상435raw/427표시·부분8 보존. 제작 함수, 새 원화 생성 재현, 실기, 원MIPS 실행은 이 reader 범위가 아니다.'}
 out=N/'rin303_independent_readback.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'passed':True,'counts':dict(counts),'gpu':gpu,'report_sha256':sha(out.read_bytes())}))
if __name__=='__main__':main()
