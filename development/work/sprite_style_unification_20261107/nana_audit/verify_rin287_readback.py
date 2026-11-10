"""린 체이서28 독립 reader. 제작 모듈을 호출하지 않는다."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas,compose_indices
sha=lambda b:hashlib.sha256(b).hexdigest()
D=ROOT/'work/sprite_style_unification_20261107/zero_audit/rin_extension'
P=D/'prepared_chaser01';B=D/'prepared_ride_heads02';A=D/'chaser_contacts_probe_v1'
def world(raw,count,c):
 if not c['parts']:return np.zeros((384,384),np.uint8)
 px,sz,bb,_=compose_indices(raw,count,c,allowed_cluts={0});v=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);z=np.zeros((384,384),np.uint8);z[bb[1]+160:bb[3]+160,bb[0]+160:bb[2]+160]=v;return z
def atlas(raw,count):return np.frombuffer(indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256)
def tile(v,t):return v[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
def raw(g,f):return decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
def main():
 old=(B/'PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes()
 assert sha(old)=='c82e6230bcc687e2cc851a88735b695b04636b9fce3baddcf4c771abf81e265b'
 assert sha(new)=='99603ab0c003149a4fa415b3dcea78a0967a3be615d226471888bb3ece092a11'
 prop=json.loads((P/'proposal.json').read_text('utf8'));reg=json.loads((A/'registration.json').read_text('utf8'));inp=json.loads((D/'chaser_detail01/inputs.json').read_text('utf8'))
 assert prop['source_arc_sha256']==sha(old)and prop['after_sha256']==sha(new)
 assert prop['registration_sha256']==sha((A/'registration.json').read_bytes())
 g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3)
 assert replace_entry(replace_entry(new,2,g),3,c)==old
 assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
 assert bank_offsets(c,allow_aliases=True)==bank_offsets(nc,allow_aliases=True)
 shifts={14:{12:1},22:{15:1},30:{},38:{28:1,15:1}}
 fs=graphics_bank(g,1)['frames'];ns=graphics_bank(ng,1)['frames'];permitted=set();targets={};proofs=[];gpu=0;nonowned=0
 for m in inp['masters']:
  master=m['ref'];ids=list(range(master,min(master+8,42)));owned=set(m['body_tiles']);f,nf=fs[master],ns[master]
  assert ids==m['body_aliases']and f['tile_count']==nf['tile_count']==32
  assert [z['index']for z in fs if z['offset']==f['offset']]==ids
  assert len({ns[n]['offset']for n in ids})==1
  r,nr=raw(g,f),raw(ng,nf);aa,zz=atlas(r,32),atlas(nr,32)
  src=A/f'b1_{master:03}_body_indices.png';rr=next(q for q in reg['records']if q['ref']==master)
  assert sha(src.read_bytes())==rr['output_sha256'];body=np.array(Image.open(src));assert body.shape==(384,384)and body.max()<=15
  for t in set(range(32))-owned:assert np.array_equal(tile(aa,t),tile(zz,t));nonowned+=1
  mastercp=composition_frame(c,5,master);mb=sorted([p for p in mastercp['parts']if p['tile']in owned],key=lambda p:p['tile'])
  rows=[]
  for n in ids:
   oc,cp=composition_frame(c,5,n),composition_frame(nc,5,n)
   assert len(oc['parts'])==len(cp['parts']);expected=[]
   for op,np_ in zip(oc['parts'],cp['parts']):
    v=dict(op)
    if op['tile']in shifts[master]:v['x']+=1;permitted.add(op['record_offset']+2)
    assert np_==v
   ob=sorted([p for p in oc['parts']if p['tile']in owned],key=lambda p:p['tile']);assert len(ob)==len(mb)
   dyset={p['y']-q['y']for p,q in zip(ob,mb)};assert len(dyset)==1;dy=next(iter(dyset))
   for p,q in zip(ob,mb):
    assert p['tile']==q['tile']and p['x']==q['x']and p['flip_x']==q['flip_x']and p['flip_y']==q['flip_y']
   expectedbody=np.roll(body,dy,axis=0);actualbody=world(nr,32,{**cp,'parts':[p for p in cp['parts']if p['tile']in owned]})
   assert np.array_equal(expectedbody,actualbody)
   tail=world(r,32,{**oc,'parts':[p for p in oc['parts']if p['tile']not in owned]})
   newtail=world(nr,32,{**cp,'parts':[p for p in cp['parts']if p['tile']not in owned]})
   assert np.array_equal(tail,newtail)
   combined=np.where(expectedbody,expectedbody,tail).astype(np.uint8)
   assert np.array_equal(combined,render(new,1,5,n)[0]);assert np.array_equal(combined,np.array(Image.open(P/f'b1_{n:03}_indices.png')))
   targets[(1,n)]=combined
   for part in cp['parts']:
    tt=tile(zz,part['tile']);assert not(part['tile']%16==0 and tt[:,0].any());assert not(part['flip_y']and tt[0].any());gpu+=1
   rows.append({'ref':n,'bob_y_from_original_parts':dy,'body_exact':True,'ribbon_exact':True})
  proofs.append({'master':master,'source_sha256':sha(src.read_bytes()),'refs':ids,'non_owned_tiles_exact':32-len(owned),'frames':rows})
 diff={i for i,(a,b)in enumerate(zip(c,nc))if a!=b};assert diff==permitted and len(diff)==24
 counts=collections.Counter()
 for b in(0,1):
  for f,nf in zip(graphics_bank(g,b)['frames'],graphics_bank(ng,b)['frames']):
   n=f['index'];k=(b,n);assert f['tile_count']==nf['tile_count']<=32;counts['raw']+=1
   if k in targets:assert raw(g,f)!=raw(ng,nf)
   else:
    assert raw(g,f)==raw(ng,nf);counts['non_target_raw_exact']+=1
    assert composition_frame(c,b*5,n)==composition_frame(nc,b*5,n)
   if b==1 and 42<=n<=49:counts['partial8_exact']+=1;continue
   counts['display']+=1
   if k in targets:assert np.array_equal(render(new,b,b*5,n)[0],targets[k]);counts['target_exact']+=1
   else:assert np.array_equal(render(old,b,b*5,n)[0],render(new,b,b*5,n)[0]);counts['non_target_display_exact']+=1
 assert dict(counts)=={'raw':444,'non_target_raw_exact':416,'display':436,'non_target_display_exact':408,'target_exact':28,'partial8_exact':8}
 result={'passed':True,'producer_functions_called':False,'source_arc_sha256':sha(old),'candidate_sha256':sha(new),'counts':dict(counts),'source4_and_original_bob_ribbon_reconstructed':proofs,'non_owned_tiles_exact':nonowned,'only_original_part_window_x_plus1_bytes':sorted(diff),'composition_other_bytes_exact':True,'original32tiles_and_bank_boundaries_exact':True,'all_other_entries_palette_audio_exact':True,'gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,'visual_review_performed':False,'source_generation_reconstructed':False,'native_cpu_run_performed':False,'runtime_verified':False,'scope':'제작 모듈을 호출하지 않고 실제 ARC를 별도 디코드했다. 등록된 새 몸체4와 원래 조립의 상하진동·리본으로28표시를 재구성했다. 새 원화 생성 출처·미술열람·원MIPS·실기는 이 독립 검사 범위가 아니다.'}
 out=N/'rin287_independent_readback.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'gpu':gpu,'report_sha256':sha(out.read_bytes())}))
if __name__=='__main__':main()
