"""Independent readback of Riko rear candidate, without producer calls."""
from preview_restore import *
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,bank_offsets

def main():
 d=ROOT/'work/sprite_style_unification_20261107/zero_audit/riko_restore';meta=json.loads((d/'prepared_rear_v1/proposal.json').read_text('utf8'));old=(ROOT/meta['source_arc']).read_bytes();new=(ROOT/meta['resource']).read_bytes();need(sha(old)==meta['source_arc_sha256']and sha(new)==meta['after_sha256'],'ARC hashes');regfile=d/'rear_registered_v1/registration.json';need(digest(regfile)==meta['registration_sha256'],'Registration hash');reg=json.loads(regfile.read_text('utf8'));need(digest(ROOT/reg['source_image'])==reg['source_sha256'],'Generated source');targetsfile=d/'rear_registered_v1/targets.npz';need(digest(targetsfile)==reg['targets_sha256'],'Targets hash');targets=np.load(targetsfile);headfile=d/'rear_registered_v1/head_registered.png';need(digest(headfile)==reg['indexed_head_sha256'],'Authored head hash');head=np.array(Image.open(headfile));template=np.array(Image.open(ROOT/'work/ver_buki_riko/art_pilot/ladder_v1/rear_head_indexed.png'));inputs=json.loads((d/'rear_head_inputs/inputs.json').read_text('utf8'));mask=np.zeros_like(template,bool)
 for y,(x0,x1)in inputs['rear_old_head_spans'].items():mask[int(y),x0:x1]=template[int(y),x0:x1]>0
 expected={};bodychecks=0
 for q in reg['frames']:
  a=render(old,q['bank'],q['parts_bank'],q['ref'])[0];mirror=q['view']=='rear_mirrored';x,y=q['old_template_origin_world'];ox,oy=q['new_grid_origin_world'];owned=np.zeros_like(a,bool);owned[y+160:y+179,x+160:x+183]=np.fliplr(mask)if mirror else mask;protected=(a>0)&~owned;h=np.zeros_like(a);h[oy+160:oy+192,ox+160:ox+192]=np.fliplr(head)if mirror else head;want=a.copy();want[owned]=0;use=(h>0)&~protected;want[use]=h[use];need(np.array_equal(want,targets[q['id']]),'Authored target drift');need(np.array_equal(a[protected],want[protected]),'Protected body');expected[q['id']]=want;bodychecks+=1
 g,h=entry(old,2),entry(new,2);need(replace_entry(new,2,g)==old,'Non-gfx entry');need(bank_offsets(g,allow_aliases=True)==bank_offsets(h,allow_aliases=True),'Bank layout');raws=0;display=0;rawsame=0;shownsame=0;changed=0
 for bi in(0,1):
  for a,b in zip(graphics_bank(g,bi)['frames'],graphics_bank(h,bi)['frames']):
   n=a['index'];key=f'b{bi}_{n:03}';need(a['tile_count']==b['tile_count']<=32,'Tile count');ar=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;br=decode_stream(h,b['offset'],b['limit'],b['tile_count']*128).data;raws+=1
   if key not in expected:need(ar==br,'Other raw');rawsame+=1
   if bi==1 and 42<=n<=49:continue
   before=render(old,bi,0 if bi==0 else 5,n)[0];after=render(new,bi,0 if bi==0 else 5,n)[0];need(np.array_equal(after,expected.get(key,before)),'Decoded display');display+=1
   if key not in expected:shownsame+=1
   else:changed+=int(np.count_nonzero(after!=before))
 report={'passed':True,'source_sha256':sha(old),'after_sha256':sha(new),'raw_references':raws,'displayed_references':display,'non_target_raw_exact':rawsame,'non_target_display_exact':shownsame,'source_head_and_protected_body_checks':bodychecks,'changed_display_pixels':changed,'palette_composition_audio_other_entries_exact':True,'first_restoration_9_preserved':True,'tile_counts_bank_boundaries_exact':True,'method':'제작 함수 미호출. 입력 해시 후 새 머리/기존 의미 마스크를 독립 재구성하여 실제 ARC표시와 비교.','runtime_verified':False}
 write(OUT/'riko_rear_independent.json',report);print(json.dumps(report))

if __name__=='__main__':main()
