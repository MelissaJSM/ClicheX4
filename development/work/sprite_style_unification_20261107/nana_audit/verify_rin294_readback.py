"""린 등장7 독립 읽기 검사. 제작 모듈/패치 함수를 호출하지 않는다."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
sha=lambda b:hashlib.sha256(b).hexdigest()
D=ROOT/'work/sprite_style_unification_20261107/zero_audit/rin_extension'
P=D/'prepared_arrival01';B=D/'prepared_chaser01';A=D/'arrival_contacts_probe_v3'
def raw(g,f):return decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
def atlas(r,count):return np.frombuffer(indexed_atlas(r,count)[0],np.uint8).reshape(-1,256)
def tile(v,t):return v[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
def derived(body):
 mask=body!=0;expanded=binary_dilation(mask,iterations=2)
 return {247:np.where(mask,11,np.where(expanded,10,0)).astype(np.uint8),248:np.where(mask,11,0).astype(np.uint8)}
def main():
 old=(B/'PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes()
 assert sha(old)=='99603ab0c003149a4fa415b3dcea78a0967a3be615d226471888bb3ece092a11'
 assert sha(new)=='adf3b9475dd95cad5ff53ba627e4461dc9cb7ec18d202482b59744b0587c0322'
 prop=json.loads((P/'proposal.json').read_text('utf8'));reg=json.loads((A/'registration.json').read_text('utf8'))
 assert prop['source_arc_sha256']==sha(old)and prop['after_sha256']==sha(new)
 assert prop['registration_sha256']==sha((A/'registration.json').read_bytes())
 g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3)
 assert replace_entry(replace_entry(new,2,g),3,c)==old
 assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
 assert bank_offsets(c,allow_aliases=True)==bank_offsets(nc,allow_aliases=True)
 targets={};sources=[]
 for r in reg['records']:
  n=r['ref'];fp=A/f'b0_{n:03}_indices.png';assert sha(fp.read_bytes())==r['output_sha256']
  z=np.array(Image.open(fp));assert z.shape==(384,384)and z.max()<=15;targets[n]=z
  sources.append({'ref':n,'registered_source_sha256':sha(fp.read_bytes())})
 assert set(targets)==set(range(249,254))
 for n,z in derived(render(old,0,0,249)[0]).items():assert np.array_equal(z,render(old,0,0,n)[0])
 targets.update(derived(targets[249]))
 fs=graphics_bank(g,0)['frames'];ns=graphics_bank(ng,0)['frames'];permitted=set();groups=[];gpu=0;nonowned=0
 moves={252:{5:-1,6:-1,7:-1},253:{17:-2,18:-2,19:-2}}
 for ids,count in [([247,248],25),([249,250],22),([251],11),([252,253],20)]:
  f,nf=fs[ids[0]],ns[ids[0]];assert f['tile_count']==nf['tile_count']==count
  assert [q['index']for q in fs if q['offset']==f['offset']]==ids
  assert [q['index']for q in ns if q['offset']==nf['offset']]==ids
  aa,zz=atlas(raw(g,f),count),atlas(raw(ng,nf),count);owned=set()
  for n in ids:
   oc,cp=composition_frame(c,0,n),composition_frame(nc,0,n);assert len(oc['parts'])==len(cp['parts'])
   for op,np_ in zip(oc['parts'],cp['parts']):
    expected=dict(op)
    if op['tile']in moves.get(n,{}):expected['x']+=moves[n][op['tile']];permitted.add(op['record_offset']+2)
    assert np_==expected;owned.add(np_['tile'])
    ot,nt=tile(aa,np_['tile']),tile(zz,np_['tile'])
    assert not(np_['tile']%16==0 and np.any((nt[:,0]>0)&(ot[:,0]==0)))
    assert not(np_['flip_y']and np.any((nt[0]>0)&(ot[0]==0)));gpu+=1
   assert np.array_equal(render(new,0,0,n)[0],targets[n])
   assert np.array_equal(np.array(Image.open(P/f'b0_{n:03}_indices.png')),targets[n])
  for t in set(range(count))-owned:assert np.array_equal(tile(aa,t),tile(zz,t));nonowned+=1
  groups.append({'refs':ids,'tile_count':count,'original_shared_stream_preserved':True,'unconsumed_tiles_exact':count-len(owned)})
 diffs={i for i,(x,y)in enumerate(zip(c,nc))if x!=y};assert diffs==permitted and len(diffs)==6
 counts=collections.Counter()
 for b in(0,1):
  for f,nf in zip(graphics_bank(g,b)['frames'],graphics_bank(ng,b)['frames']):
   n=f['index'];selected=b==0 and n in targets
   assert f['tile_count']==nf['tile_count']<=32;counts['raw']+=1
   if selected:assert raw(g,f)!=raw(ng,nf)
   else:
    assert raw(g,f)==raw(ng,nf);counts['non_target_raw_exact']+=1
    assert composition_frame(c,b*5,n)==composition_frame(nc,b*5,n)
   if b==1 and 42<=n<=49:counts['partial8_exact']+=1;continue
   counts['display']+=1
   if selected:assert np.array_equal(render(new,b,b*5,n)[0],targets[n]);counts['target_exact']+=1
   else:assert np.array_equal(render(old,b,b*5,n)[0],render(new,b,b*5,n)[0]);counts['non_target_display_exact']+=1
 assert dict(counts)=={'raw':444,'non_target_raw_exact':437,'display':436,'non_target_display_exact':429,'target_exact':7,'partial8_exact':8}
 result={'passed':True,'producer_functions_called':False,'source_arc_sha256':sha(old),'candidate_sha256':sha(new),
  'counts':dict(counts),'registered_sources':sources,'groups':groups,'source_and_candidate_flash_rule_exact':True,
  'original_pure_beam53_60_exact':True,'non_owned_whole_tiles_exact':nonowned,'only_six_original_part_x_bytes':sorted(diffs),
  'composition_other_bytes_exact':True,'original_tile_counts_and_bank_boundaries_exact':True,'all_other_entries_palette_audio_exact':True,
  'gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,'visual_review_performed':False,'source_generation_reconstructed':False,
  'native_cpu_run_performed':False,'runtime_verified':False,
  'scope':'제작 함수를 호출하지 않고 등록5몸체와 원래 섬광규칙을 독립 재구성해 실제 ARC7표시를 대조했다. 비대상437 raw/429표시와 부분VRAM8·음향 보존. 미술열람·원화 생성 출처·원MIPS·실기는 이 검사 범위가 아니다.'}
 out=N/'rin294_independent_readback.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'passed':True,'counts':dict(counts),'gpu':gpu,'report_sha256':sha(out.read_bytes())}))
if __name__=='__main__':main()
