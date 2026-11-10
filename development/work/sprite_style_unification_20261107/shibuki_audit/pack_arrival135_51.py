"""최신 BR31의135만 교체하고 모든 비대상 해석 결과를 보존한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;W=H.parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop,same_rgba
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import pack_planes
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,composition_frame,indexed_atlas
from pack_shibuki_hurt import raw,repack_fixed_global
from repack_part_records_lossless import repack as repack_global
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose
PBS=(0,5,6,7,8);TD=H/'ultimate_arrival135_common51';OUT=H/'packed_arrival135_51b'
def main():
 need(not OUT.exists(),'Fresh output required');OUT.mkdir()
 plan=json.loads((W/'staging_br_v31.json').read_text('utf8'));src=plan['resources']['PL02_U.ARC'];p=ROOT/src['path'];data=p.read_bytes();need(sha(data)==src['after'],'Exact BR31 parent required');a=Archive(data)
 before=np.array(Image.open(TD/'before_135_indices.png'));after=np.array(Image.open(TD/'after_135_indices.png'));need(not ((after>0)&(before==0)).any(),'Costume erasure required')
 targets={0:after,5:np.where(same_rgba(a,before,after),0,before).astype(np.uint8),**{b:np.zeros_like(after)for b in(6,7,8)}}
 nr,rr=pack_planes(bytes(4096),32,[crop(targets[b])for b in PBS],set(range(32))-{0,16},[24]*5)
 atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256);nc=a.c;part_rows=[];edge=0
 for b,ps in zip(PBS,rr):
  record=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in ps)
  if not record:need(not atlas[:16,:16].any(),'Tile0 must stay transparent');record=struct.pack('<BBbb',0,0,-8,-8)
  need(len(record)//4<=24,'Part limit')
  for fl,t,x,y in struct.iter_unpack('<BBbb',record):
   if t%16==0:need(not atlas[t//16*16:t//16*16+16,0].any(),'GPU U edge')
   if fl&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),'GPU V edge')
   edge+=1
  try:nc,slack=repack_parts(nc,b,{135:record});method='exact_record_repack'
  except ValueError:nc,slack,method=repack_global(nc,b,{135:record})
  part_rows.append({'bank':b,'parts':len(record)//4,'slack':slack,'method':method})
 ng,graphics=repack_fixed_global(a,{135:nr},{135:32});new=replace_entry(replace_entry(data,2,ng),3,nc);actual=Archive(new);need(bank_offsets(nc)==bank_offsets(a.c),'Composition bank boundaries')
 counts={'raw':0,'unchanged_raw':0,'layers':0,'unchanged_layers':0,'partial_rgba':0,'unchanged_records':0,'gpu_edges':edge}
 for gb,bank in enumerate(a.banks):
  nb=actual.banks[gb];need((bank['base'],bank['end'],len(bank['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Graphics boundary')
  for f in bank['frames']:
   n=f['index'];selected=gb==0 and n==135;need(raw(actual,gb,n)==(nr if selected else raw(a,gb,n)),f'Raw {gb}/{n}');counts['raw']+=1;counts['unchanged_raw']+=not selected
 for n in range(237):
  if n in(105,*range(175,183)):continue
  for b in PBS:need(np.array_equal(actual.layer(n,b)[0],targets[b]if n==135 else a.layer(n,b)[0]),f'Layer {n}/{b}');counts['layers']+=1;counts['unchanged_layers']+=n!=135
 for arm in(1,2):
  for mask in range(16):need(actual.composite(135,mask,arm)[0].tobytes()==compose(a,targets,mask,arm).tobytes(),'Partial costume mismatch');counts['partial_rgba']+=1
 for b in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
   if b in PBS and n==135:continue
   need(records(actual.c,b,n)==records(a.c,b,n),f'Non-target records {b}/{n}');counts['unchanged_records']+=1
 need(np.array_equal(actual.words,a.words),'Palette changed');protected=protected_entries(data,new)
 (OUT/'PL02_U.ARC').write_bytes(new)
 for form,mask in [('before',15),('after',0)]:
  page([(f'135 BR31 {form}',a.composite(135,mask)[0]),(f'135 candidate {form}',actual.composite(135,mask)[0])],a.composite(0,mask)[0],OUT/f'{form}_readback.png',cols=2,scale=5)
  page([(f'{n} {form}',actual.composite(n,mask)[0])for n in(133,134,135,0,136,137)],actual.composite(0,mask)[0],OUT/f'{form}_transition.png',cols=3,scale=4)
 report={'passed':True,'parent':src,'candidate_sha256':sha(new),'target_source_report_sha256':sha((TD/'report.json').read_bytes()),'artwork':{f:sha((TD/f'{f}_135_indices.png').read_bytes())for f in['before','after']},'refs':[135],'counts':counts,'graphics':graphics,'parts':part_rows,'protected_entries':protected,'palette_changed':False,'timing_changed':False,'native_decoder_pending':True,'runtime_verified':False}
 write(OUT/'report.json',report)
 trial={'project':'ver_buki_riko','source_bin':'out/ver_buki_riko/sprite_style_unification_20261107_v31/shibuki_riko.bin','source_sha256':'ad4f2ceab100098e88977f383d314efd0337379feb70999989eaa53926332516','output':'out/ver_buki_riko/sprite_style_unification_20261107_v32','resources':{'PL02_U.ARC':{'path':(OUT/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':src['after'],'after':sha(new)}},'checkpoint_only':True,'full_art_unification_complete':False,'checkpoint_label':'shibuki_ultimate_arrival135_resume51','prior_plan':'work/sprite_style_unification_20261107/staging_br_v31.json','review_images':[]}
 write(W/'staging_br_v32.json',trial);print(json.dumps({'candidate':sha(new),'counts':counts,'parts':part_rows}))
if __name__=='__main__':main()
