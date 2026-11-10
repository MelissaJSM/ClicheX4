"""Independent read-only contract audit; no producer patch function reused."""
from preview_restore import *
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,bank_offsets

def main():
 directory=ROOT/'work/sprite_style_unification_20261107/zero_audit/riko_restore';meta=json.loads((directory/'prepared_v1/proposal.json').read_text('utf8'));source=ROOT/meta['source_bin'];need(digest(source)==meta['source_sha256'],'Riko parent');candidate=(directory/'prepared_v1/PL01_U.ARC').read_bytes();need(sha(candidate)==meta['after_sha256'],'Riko candidate')
 with source.open('rb')as f:
  d=DiscReader(f,source.stat().st_size);record=next(r for r in d.inspect()['files']if r['name']=='PL01_U.ARC;1');original=d.read(record['lba'],record['size'])
 need(sha(original)==meta['source_arc_sha256'],'Riko original ARC');g,h=entry(original,2),entry(candidate,2);need(replace_entry(candidate,2,g)==original,'Non-gfx changed');need(bank_offsets(g,allow_aliases=True)==bank_offsets(h,allow_aliases=True),'Bank boundary changed')
 proof={q['frame']:q for q in meta['art_source']['proof']};counts=[];rawsame=0;checked=0
 for b in(0,1):
  oldbank,newbank=graphics_bank(g,b),graphics_bank(h,b)
  for old,new in zip(oldbank['frames'],newbank['frames']):
   n=old['index'];need(old['tile_count']==new['tile_count']<=32,'Native tile count');ar=decode_stream(g,old['offset'],old['limit'],old['tile_count']*128).data;br=decode_stream(h,new['offset'],new['limit'],new['tile_count']*128).data;target=b==0 and n in proof
   if not target:need(ar==br,f'Non-target raw {b}/{n}');rawsame+=1
   if b==1 and 42<=n<=49:continue
   a=render(original,b,0 if b==0 else 5,n)[0];z=render(candidate,b,0 if b==0 else 5,n)[0];diff=z!=a;need(np.array_equal(a>0,z>0),'Alpha');checked+=1
   if target:
    need(np.all(a[diff]==15)and np.all(z[diff]==12),'Restored index mismatch');points={(int(x-160),int(y-160))for y,x in np.argwhere(diff)};need(points=={tuple(v)for v in proof[n]['world_pixels']},'Target mask mismatch');counts.append({'ref':n,'pixels':len(points)})
   else:need(np.array_equal(a,z),'Non-target visible')
 report={'passed':True,'scope':'준비된 실제 ARC의 원본/후보 해시, 444개 디코드 참조와 436개 표시 참조, 지정 9개 명암/비대상 보존 독립 대조. 제작 함수를 호출하지 않음. 원화 미술 승인과 실기는 별도.','source_sha256':digest(source),'before':sha(original),'after':sha(candidate),'raw_non_targets_exact':rawsame,'displayed_checked':checked,'target_changes':counts,'changed_pixels':sum(q['pixels']for q in counts),'other_entries_palette_parts_audio_exact':True,'alpha_and_tile_counts_exact':True,'runtime_verified':False}
 write(OUT/'riko_candidate_independent.json',report);print(json.dumps({k:v for k,v in report.items()if k not in('scope','target_changes')}))

if __name__=='__main__':main()
