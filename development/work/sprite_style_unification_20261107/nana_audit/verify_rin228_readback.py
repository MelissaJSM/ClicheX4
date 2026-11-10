"""린 bank1 준비/회복6: 제작 함수를 호출하지 않는 별도 읽기 감사."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
sha=lambda b:hashlib.sha256(b).hexdigest()
D=ROOT/'work/sprite_style_unification_20261107/zero_audit/rin_extension';P=D/'prepared_bank1_special01';B=D/'prepared_dash_saber01';A=D/'bank1_special_registered_v1'
def sem(cp):return [(p['flags'],p['tile'],p['x'],p['y'])for p in cp['parts']]
def main():
 old=(B/'PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(old)=='94b24181ee1d6ce463f1647e89f58fcf29c57e8eb8cc6ede457cc46e22fc36da';assert sha(new)=='989b68597fa276164a16902806136f897c16ef3c1c81950b3b16fa039bede7a0'
 prop=json.loads((P/'proposal.json').read_text('utf8'));assert prop['source_arc_sha256']==sha(old)and prop['after_sha256']==sha(new)
 g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3)
 assert replace_entry(replace_entry(new,2,g),3,c)==old
 assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)and bank_offsets(c)==bank_offsets(nc)
 source={91:91,93:93,101:101,103:101,105:105,107:105};target={(1,n):np.array(Image.open(A/f'b1_{s:03}_indices.png'))for n,s in source.items()};support={(1,n)for n in(92,94,102,104,106)}
 count=collections.Counter();raw_changes=[];parts_changes=[];support_tiles=[];gpu=0
 for b in(0,1):
  ob,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(ob['frames'])==len(nb['frames'])
  for f,nf in zip(ob['frames'],nb['frames']):
   n=f['index'];k=(b,n);assert f['tile_count']==nf['tile_count']<=32
   raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;count['raw']+=1
   cp,qp=composition_frame(c,b*5,n),composition_frame(nc,b*5,n)
   if raw!=nr:assert k in target or k in support;raw_changes.append([b,n])
   if k not in target and k not in support:assert raw==nr;count['non_target_raw_exact']+=1
   if sem(cp)!=sem(qp):assert k in target;parts_changes.append([b,n])
   assert len(cp['parts'])==len(qp['parts'])
   if k in target or k in support:
    aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
    if k in support:
     assert sem(cp)==sem(qp);ts=sorted({p['tile']for p in cp['parts']})
     for t in ts:
      y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16]),('support full tile',k,t)
     support_tiles.append({'ref':n,'whole_tiles_exact':ts})
    for p in qp['parts']:
     t=p['tile'];y,x=t//16*16,t%16*16
     if t%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]!=0)),('new U alpha',k,t)
     if p['flip_y']and t//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]!=0)),('new V alpha',k,t)
     gpu+=1
   if b==1 and 42<=n<=49:assert raw==nr and sem(cp)==sem(qp);count['partial8_exact']+=1;continue
   before=render(old,b,b*5,n)[0];after=render(new,b,b*5,n)[0];count['display']+=1
   if k in target:
    assert np.array_equal(after,target[k])and not np.array_equal(before,after)
    assert sha((A/f'b1_{source[n]:03}_indices.png').read_bytes())==prop['native_master_sha256'][f'b1_{source[n]:03}'];count['authored_exact']+=1
   else:assert np.array_equal(after,before);count['non_target_display_exact']+=1
 for bank in(1,2,3,4,6):
  for n in range(composition_frame(c,bank,0)['bank_frame_count']):assert sem(composition_frame(c,bank,n))==sem(composition_frame(nc,bank,n))
 assert count['raw']==444 and count['non_target_raw_exact']==433 and count['display']==436 and count['authored_exact']==6 and count['non_target_display_exact']==430 and count['partial8_exact']==8
 ob,nb=graphics_bank(g,1),graphics_bank(ng,1);groups=[(91,92,93,94),(101,102,103,104),(105,106,107)]
 for group in groups:
  assert len({ob['frames'][n]['offset']for n in group})==1 and len({nb['frames'][n]['offset']for n in group})==1
  # 표시에 사용하지 않는 타일까지 임의 정리하지 않았는지 별도 검사.
  n=group[0];f,nf=ob['frames'][n],nb['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
  pool={p['tile']for m in group if m in source for p in composition_frame(c,5,m)['parts']}|{p['tile']for m in group if m in source for p in composition_frame(nc,5,m)['parts']}
  aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
  for tile in range(f['tile_count']):
   if tile not in pool:
    y,x=tile//16*16,tile%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16]);count['non_body_whole_raw_tiles_exact']+=1
 for f in('palette.bin','effect_23.png','effect_24.png'):assert(P/f).read_bytes()==(B/f).read_bytes()
 r=json.loads((P/'static_effects.json').read_text('utf8'));br=json.loads((B/'static_effects.json').read_text('utf8'));assert r.pop('parts_sha256')==sha(nc);br.pop('parts_sha256');assert r==br
 result={'passed':True,'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'candidate_sha256':sha(new),'parent_sha256':sha(old),'producer_functions_called':False,'counts':dict(count),'changed_raw_refs':raw_changes,'changed_parts':parts_changes,'support_full_consumed_tiles':support_tiles,'gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,'three_shared_stream_groups_preserved':groups,'bank_bounds_tile_counts_part_counts_exact':True,'other_entries_sound_palette_static_exact':True,'source_generation_reconstruction_performed':False,'runtime_verified':False,'native_cpu_run_performed':False,'visual_review_performed':True,'actually_viewed_sheets':[{'path':str((A/f).relative_to(ROOT)),'sha256':sha((A/f).read_bytes())}for f in('normal_comparison.png','black_comparison.png')],'visual_observation':'일반/레드 두 비교판의4고유자세를 직접 열람했다. 새 머릿결·커프·치마 주름이 대기 세부와 이어지며,101/105 손 정합 후 새 팔목/다리의 명백한 절단은 찾지 못했다. 실제 시간표·게임 검증은 별도다.','scope':'독립 reader로444raw/436표시와등록6목표를 대조했다. 5지원 검기는 전체 소비타일·조립·표시를 모두 보존하며,433은11관련raw를 뺀 수,430은6새몸체를 뺀 불변표시 수다.'}
 out=N/'rin228_independent_readback.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'gpu':gpu,'report_sha256':sha(out.read_bytes())}))
if __name__=='__main__':main()
