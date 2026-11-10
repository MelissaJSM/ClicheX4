"""Ultimate 등장8 고정은행 패킹. 보류135와 공유 비대상132를 포함해 보존한다."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop,same_rgba
from prepare_ultimate_arrival_partial import P,PARENT,PBS,REFS,SOURCE,OUT as TD
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts,records,pack_shared
from scripts.overhaul_sprites_costume_pack import pack_planes
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,composition_frame,indexed_atlas
from src.psx_ui_atlas import tile_pixels
from pack_shibuki_hurt import raw,repack_fixed_global,tile_seed
from pack_air_targets_probe import pack_pinned
from repack_part_records_lossless import repack as repack_global
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose
MANIFEST='bf9a17ed79a5bc4e7dfffcd47e33351240a9645b7656d41e43fb01747521c000'

def build(data,progress):
 need(sha(data)==PARENT,'Wrong exact parent');need(sha((TD/'manifest.json').read_bytes())==MANIFEST,'Targets changed');meta=json.loads((TD/'manifest.json').read_text('utf8'))
 for name,h in meta['source_files'].items():need(sha((ROOT/name).read_bytes())==h,'Source changed '+name)
 need(sha((SOURCE/'report.json').read_bytes())==meta['body_report_sha256'],'Body report changed')
 a=Archive(data);hist=Archive((ROOT/meta['historical_source']).read_bytes());targets={n:{b:np.array(Image.open(TD/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in REFS}
 for n,ls in targets.items():
  for b,v in ls.items():need(sha(v.tobytes())==meta['targets'][str(n)][str(b)],'Target pixels changed')
 changes={b:{}for b in PBS};raws={};groups=[];gpu=0
 for n in REFS:
  keep={7}if n in(136,137)else set();seed=tile_seed(hist,n,keep)if keep else bytes(4096);pool=set(range(32))-{0,16}-keep;extra={};variants={};background=None
  if n in(130,131,134):
   background=np.array(Image.open(TD/f'{n:03}_background_indices.png'))
   if n==134:front=targets[133]
   else:front={0:np.array(Image.open(TD/f'{n:03}_silhouette_indices.png')),**{b:np.zeros((384,384),np.uint8)for b in PBS[1:]}}
   nr,pp,mode=pack_pinned(seed,[crop(background)]+[crop(front[b])for b in PBS],pool)
   rr=[pp[0]+pp[1]]+pp[2:];background_parts=pp[0]
  elif keep:
   before=np.array(Image.open(SOURCE/f'before_{n:03}_indices.png'));after=np.array(Image.open(SOURCE/f'after_{n:03}_indices.png'));body={0:after,5:np.where(same_rgba(a,before,after),0,before).astype(np.uint8),**{b:np.zeros_like(after)for b in(6,7,8)}}
   nr,rr=pack_shared(seed,32,[crop(body[b])for b in PBS],pool,[24]*5);mode='whole_historical_effect_tile'
   ps=meta['protected_effect_records'][str(n)];extra={0:ps,5:ps}
  else:nr,rr=pack_planes(seed,32,[crop(targets[n][b])for b in PBS],pool,[24]*5);mode='separate_costume_planes'
  atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256)
  for t in keep:need(tile_pixels(nr,t)==tile_pixels(seed,t),'Whole historical effect tile changed')
  for b,ps in zip(PBS,rr):
   record=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in ps)
   if not record:need(not atlas[:16,:16].any(),'Blank tile occupied');record=struct.pack('<BBbb',0,0,-8,-8)
   record+=b''.join(struct.pack('<BBbb',p['flags'],p['tile'],p['x'],p['y'])for p in extra.get(b,[]));need(len(record)//4<=24,f'Part limit {n}/{b}')
   for fl,t,x,y in struct.iter_unpack('<BBbb',record):
    if t%16==0:need(not atlas[t//16*16:t//16*16+16,0].any(),f'GPU U edge {n}/{b}/{t}')
    if fl&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),f'GPU V edge {n}/{b}/{t}')
    gpu+=1
   changes[b][n]=record
  if background is not None:
   rendered=np.zeros((384,384),np.uint8)
   for t,x,y,fl in background_parts:
    pixels=np.frombuffer(tile_pixels(nr,t),np.uint8).reshape(16,16)
    if fl&64:pixels=pixels[:,::-1]
    if fl&128:pixels=pixels[::-1]
    window=rendered[y+80:y+96,x+80:x+96];window[pixels>0]=pixels[pixels>0]
   need(np.array_equal(rendered,background),f'Whole background source lost {n}')
  owners=[f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']]
  raws[n]=nr;groups.append({'ref':n,'method':mode,'parts':{str(b):len(changes[b][n])//4 for b in PBS},'raw_sha256':sha(nr),'historical_effect_tiles_exact':sorted(keep),'whole_background_exact':background is not None,'old_shared_refs':owners,'non_target_shared_owners_preserved_by_separate_new_stream':[k for k in owners if k not in REFS]});progress(groups[-1])
 nc=a.c;slack={};methods={}
 for b,rr in changes.items():
  try:nc,slack[b]=repack_parts(nc,b,rr);methods[b]='exact_record_repack'
  except ValueError:nc,slack[b],methods[b]=repack_global(nc,b,rr)
 progress({'part_slack':slack});ng,graphics=repack_fixed_global(a,raws,{n:32 for n in REFS});new=replace_entry(replace_entry(data,2,ng),3,nc);actual=Archive(new);need(bank_offsets(nc)==bank_offsets(a.c),'Part bank boundaries changed')
 total=nonraw=layers=kept=partial=otherparts=0
 for gb,bank in enumerate(a.banks):
  nb=actual.banks[gb];need((bank['base'],bank['end'],len(bank['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Graphics bank boundaries changed')
  for f in bank['frames']:
   n=f['index'];selected=gb==0 and n in REFS;want=raws[n]if selected else raw(a,gb,n);need(raw(actual,gb,n)==want,f'Raw mismatch{gb}/{n}');total+=1;nonraw+=not selected
 for n in range(237):
  if n in(105,*range(175,183)):continue
  for b in PBS:
   want=targets[n][b]if n in targets else a.layer(n,b)[0];need(np.array_equal(actual.layer(n,b)[0],want),f'Layer mismatch {n}/{b}');layers+=1;kept+=n not in targets
  if n in targets:
   for arm in(1,2):
    for mask in range(16):need(actual.composite(n,mask,arm)[0].tobytes()==compose(a,targets[n],mask,arm).tobytes(),'Partial RGBA differs');partial+=1
 for b in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
   if b in PBS and n in REFS:continue
   need(records(actual.c,b,n)==records(a.c,b,n),'Non-target part record changed');otherparts+=1
 for n in(0,115,116,117,118,119,126,127,128,129,132,135,140,141,142):
  need(raw(actual,0,n)==raw(a,0,n),'Protected selected witness raw');need(all(np.array_equal(actual.layer(n,b)[0],a.layer(n,b)[0])for b in PBS),'Protected witness layer')
 return new,{'passed':True,'parent_sha256':PARENT,'candidate_sha256':sha(new),'target_manifest_sha256':MANIFEST,'refs':list(REFS),'excluded_ref135_preserved':True,'groups':groups,'part_slack':slack,'part_storage_methods':methods,'graphics':graphics,'counts':{'raw':total,'non_target_raw':nonraw,'layers':layers,'non_target_layers':kept,'partial_RGBA':partial,'non_target_records':otherparts,'GPU_parts':gpu},'preserved_entries':protected_entries(data,new),'art_pixel_loss':False,'runtime_verified':False,'scope':'고정은행8참조 정적 후보. 별도 원MIPS/독립/최종미술/실기 전.'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='ultimate_arrival_pack01');z=ap.parse_args();o=(H/z.output).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh owned output');o.mkdir();progress=[]
 def log(v):progress.append(v);write(o/'progress.json',progress);print(json.dumps(v),flush=True)
 try:new,proof=build(P.read_bytes(),log)
 except Exception as e:write(o/'report.json',{'passed':False,'error':str(e),'arc_written':False,'progress':progress});raise
 (o/'PL02_U.ARC').write_bytes(new);actual=Archive(new)
 for form,mask in(('before',15),('after',0)):
  for i,ns in enumerate(((130,131,133,134),(136,137),(138,139))):page([(f'{n} actual {form}',actual.composite(n,mask)[0])for n in ns],actual.composite(0,mask)[0],o/f'{form}_readback_{i:02}.png',cols=2,scale=4)
 for n in(133,136,138,139):page([(f'{n} mask {mask}',actual.composite(n,mask,1)[0])for mask in range(16)],actual.composite(0,0)[0],o/f'partial_{n}.png',cols=4,scale=3)
 write(o/'report.json',proof);print(json.dumps({'candidate':sha(new),'counts':proof['counts']}))
if __name__=='__main__':main()
