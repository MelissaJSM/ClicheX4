"""린 질풍아8 준비 자원의 독립 읽기 검사. 제작/패킹 함수를 호출하지 않는다."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
sha=lambda b:hashlib.sha256(b).hexdigest()
D=ROOT/'work/sprite_style_unification_20261107/zero_audit/rin_extension';P=D/'prepared_dash_saber01';B=D/'prepared_ladder_dash01';A=D/'dash_saber_registered_v1'
def sem(cp):return [(p['flags'],p['tile'],p['x'],p['y'])for p in cp['parts']]
def main():
 old=(B/'PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(old)=='c2ec4099740eb77cca2d37e4b0f997728e1748a35e47b45475289725ec1dd09b';assert sha(new)=='94b24181ee1d6ce463f1647e89f58fcf29c57e8eb8cc6ede457cc46e22fc36da';proposal=json.loads((P/'proposal.json').read_text('utf8'));assert proposal['source_arc_sha256']==sha(old)and proposal['after_sha256']==sha(new)
 g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3);assert replace_entry(replace_entry(new,2,g),3,c)==old;assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True);assert bank_offsets(c)==bank_offsets(nc)
 targets={(0,n):np.array(Image.open(A/f'b0_{n}_indices.png'))for n in range(158,173,2)};support={(0,n)for n in range(159,174,2)};counts=collections.Counter();changes=[];support_tiles=[];parts=[];gpu=0
 for b in(0,1):
  ob,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(ob['frames'])==len(nb['frames'])
  for f,nf in zip(ob['frames'],nb['frames']):
   n=f['index'];key=(b,n);assert f['tile_count']==nf['tile_count']<=32;raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;counts['raw']+=1;cp,qp=composition_frame(c,b*5,n),composition_frame(nc,b*5,n)
   if raw!=nr:assert key in targets or key in support;changes.append([b,n])
   if key not in targets and key not in support:assert raw==nr;counts['non_target_raw_exact']+=1
   if sem(cp)!=sem(qp):assert key in targets;parts.append({'key':[b,n],'before_count':len(cp['parts']),'after_count':len(qp['parts'])})
   if key in targets or key in support:
    aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
    if key in support:
     assert sem(cp)==sem(qp);ts=sorted({p['tile']for p in cp['parts']})
     for t in ts:
      y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16]),('support tile',key,t)
     support_tiles.append({'ref':n,'full_consumed_tiles_exact':ts})
    for p in qp['parts']:
     t=p['tile'];y,x=t//16*16,t%16*16
     if t%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]!=0)),('GPU U',key,t)
     if p['flip_y']and t//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]!=0)),('GPU V',key,t)
     gpu+=1
   if b==1 and 42<=n<=49:assert raw==nr and sem(cp)==sem(qp);counts['partial8_exact']+=1;continue
   before=render(old,b,b*5,n)[0];after=render(new,b,b*5,n)[0];counts['display']+=1
   if key in targets:
    assert np.array_equal(after,targets[key])and not np.array_equal(before,after);assert sha((A/f'b0_{n}_indices.png').read_bytes())==proposal['native_master_sha256'][f'b0_{n}'];counts['authored_exact']+=1
   else:assert np.array_equal(after,before);counts['non_target_display_exact']+=1
 for bank in(1,2,3,4,6):
  for n in range(composition_frame(c,bank,0)['bank_frame_count']):assert sem(composition_frame(c,bank,n))==sem(composition_frame(nc,bank,n))
 assert counts['raw']==444 and counts['non_target_raw_exact']==428 and counts['display']==436 and counts['authored_exact']==8 and counts['non_target_display_exact']==428 and counts['partial8_exact']==8
 nb=graphics_bank(ng,0);offsets=[]
 for n in(168,170,172):assert nb['frames'][n]['tile_count']==31 and nb['frames'][n]['offset']==nb['frames'][n+1]['offset'];offsets.append(nb['frames'][n]['offset'])
 assert len(set(offsets))==3
 for n in(158,160,162,164,166):assert nb['frames'][n]['offset']==nb['frames'][n+1]['offset']
 for f in('palette.bin','effect_23.png','effect_24.png'):assert(P/f).read_bytes()==(B/f).read_bytes()
 r=json.loads((P/'static_effects.json').read_text('utf8'));oldr=json.loads((B/'static_effects.json').read_text('utf8'));assert r.pop('parts_sha256')==sha(nc);oldr.pop('parts_sha256');assert r==oldr
 result={'passed':True,'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'candidate_sha256':sha(new),'parent_sha256':sha(old),'producer_functions_called':False,'counts':dict(counts),'changed_raw_refs':changes,'changed_parts':parts,'support_full_consumed_tiles':support_tiles,'gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,'split_31_tile_groups':offsets,'five_other_body_effect_shares_preserved':True,'bank_bounds_tile_counts_exact':True,'other_entries_sound_palette_static_exact':True,'registered_native_pngs_exact':True,'source_generation_reconstruction_performed':False,'runtime_verified':False,'visual_review_performed':False,'scope':'별도 reader로444raw/436표시를 읽고 새8원화 인덱스·비대상·검기 소비타일·부분VRAM·고정은행을 대조했다. 원화 재양자화/MIPS/실기 검사를 대신하지 않는다.'}
 result['visual_review_performed']=True;result['actually_viewed_sheets']=[{'path':str((A/f).relative_to(ROOT)),'sha256':sha((A/f).read_bytes())}for f in('normal_comparison_00.png','normal_comparison_01.png')];result['visual_observation']='정상색 비교2판의8자세에서 머리 가닥·소매·치마 주름이 늘고 대기 세부와 가까워짐을 직접 확인했다. 새 종아리/손목의 명백한 절단은 찾지 못했다. 블랙·원시간표 연속재생·실기는 이 감사에서 미열람이다.'
 out=N/'rin222_independent_readback.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'gpu':gpu,'report_sha256':sha(out.read_bytes())}))
if __name__=='__main__':main()
