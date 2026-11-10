"""린 탑승 머리19의 별도 reader. 제작 함수/프로세스/게임 파일 쓰기 없음."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
sha=lambda b:hashlib.sha256(b).hexdigest()
D=ROOT/'work/sprite_style_unification_20261107/zero_audit/rin_extension';P=D/'prepared_ride_heads02';B=D/'prepared_bank1_recovery128';A=D/'ride_head_registered_v3'
def main():
 old=(B/'PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(old)=='07ec6077969f17d08c51ffd8e4326b476e1c6ab5635bea8420faee9528b39a89';assert sha(new)=='c82e6230bcc687e2cc851a88735b695b04636b9fce3baddcf4c771abf81e265b'
 prop=json.loads((P/'proposal.json').read_text('utf8'));assert prop['source_arc_sha256']==sha(old)and prop['after_sha256']==sha(new);assert prop['registration_sha256']==sha((A/'registration.json').read_bytes())
 g,c=entry(old,2),entry(old,3);ng=entry(new,2);assert replace_entry(new,2,g)==old;assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
 targets={(1,n):np.array(Image.open(A/f'b1_{n:03}_indices.png'))for n in(*range(66,80),*range(81,86))};reg=json.loads((A/'registration.json').read_text('utf8'))
 for q in reg['registered_refs']:assert sha((A/(q['key']+'_indices.png')).read_bytes())==q['output_sha256']
 assert len(reg['registered_refs'])==len(targets)==19
 count=collections.Counter();changes=[];tiles=[];gpu=0
 for b in(0,1):
  ob,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(ob['frames'])==len(nb['frames'])
  for f,nf in zip(ob['frames'],nb['frames']):
   n=f['index'];k=(b,n);assert f['tile_count']==nf['tile_count']<=32;raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;count['raw']+=1;cp=composition_frame(c,b*5,n)
   if raw!=nr:assert k in targets or k==(1,80);changes.append([b,n])
   else:count['unchanged_raw']+=1
   if b==1 and 42<=n<=49:assert raw==nr;count['partial8_exact']+=1;continue
   before=render(old,b,b*5,n)[0];after=render(new,b,b*5,n)[0];count['display']+=1
   if k in targets:
    assert np.array_equal(after,targets[k])and not np.array_equal(before,after);count['authored_exact']+=1
    assert len(cp['parts'])==1
    aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
    used=cp['parts'][0]['tile'];tiles.append({'ref':n,'tile':used,'raw_count':f['tile_count']})
    p=cp['parts'][0];y,x=used//16*16,used%16*16
    if used%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]!=0))
    if p['flip_y']and used//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]!=0))
    gpu+=1
   else:assert np.array_equal(before,after);count['non_target_display_exact']+=1
 # 모든 변경 raw nibble은 같은 공유 스트림의 대상 머리들이 소비하는16x16타일 합집합에 한정.
 ob,nb=graphics_bank(g,1),graphics_bank(ng,1);groups=collections.defaultdict(list)
 for f in ob['frames']:groups[f['offset']].append(f['index'])
 protected_tiles=0;shared=[]
 for group in groups.values():
  selected=[n for n in group if(1,n)in targets]
  if not selected:continue
  assert len({nb['frames'][n]['offset']for n in group})==1;shared.append(group);f=ob['frames'][group[0]];nf=nb['frames'][group[0]]
  raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256);owned={p['tile']for n in selected for p in composition_frame(c,5,n)['parts']}
  for t in range(f['tile_count']):
   y,x=t//16*16,t%16*16
   if t not in owned:assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16]);protected_tiles+=1
 f,nf=ob['frames'][80],nb['frames'][80];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
 for p in composition_frame(c,5,80)['parts']:
  t=p['tile'];y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16])
 assert not render(new,1,5,80)[0].any();assert dict(count)=={'raw':444,'unchanged_raw':424,'display':436,'non_target_display_exact':417,'partial8_exact':8,'authored_exact':19}
 result={'passed':True,'candidate_sha256':sha(new),'parent_sha256':sha(old),'producer_functions_called':False,'counts':dict(count),'changed_raw_refs':changes,'native_targets_exact':19,'shared_groups_preserved':shared,'all_non_head_tiles_exact':protected_tiles,'blank80_consumed_tiles_and_display_exact':True,'composition_entry_whole_exact':True,'other_entries_audio_palette_exact':True,'original_bank_bounds_tile_counts_exact':True,'head_tile_records':tiles,'gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,'source_generation_reconstructed':False,'visual_review_performed':False,'native_cpu_run_performed':False,'runtime_verified':False,'scope':'준비된19머리 목표와 최종 ARC를 별도 reader로 대조.14→12px 체형 미술수용과 원화출처 재구성은 제작자/루트의 별도 검토이며 이 검사의 기술통과로 대신하지 않는다.'}
 previous=(D/'prepared_ride_heads01/PL01_U.ARC').read_bytes()
 incremental=[]
 for bank in(0,1):
  for f in graphics_bank(entry(new,2),bank)['frames']:
   n=f['index']
   if bank==1 and 42<=n<=49:continue
   if not np.array_equal(render(previous,bank,bank*5,n)[0],render(new,bank,bank*5,n)[0]):incremental.append([bank,n])
 assert incremental==[[1,75],[1,76],[1,77]]
 result['previous_candidate_sha256']=sha(previous)
 result['incremental_changed_display_refs']=incremental
 result['previous_candidate_other_displays_exact']=True
 result['scope']='제작 함수 없이 후보19머리의 목표 픽셀과 비대상/공유/경계를 대조했다. 첫 후보와 비교하면75/76/77표시만 달라진다. 이번 증거에는 새 비교판 시각 열람·원화 재구성·실기 검사를 포함하지 않는다.'
 out=N/'rin259_v2_independent_readback.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'gpu':gpu,'protected_tiles':protected_tiles,'report_sha256':sha(out.read_bytes())}))
if __name__=='__main__':main()
