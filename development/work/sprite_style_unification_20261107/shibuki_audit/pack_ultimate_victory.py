"""새 Ultimate 승리4를 고정은행 안에 패킹하고 전참조를 재독출한다."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from prepare_ultimate_victory_targets import P,PARENT,PBS,REFS,OUT as TD
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import pack_planes
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,composition_frame,indexed_atlas
from pack_shibuki_hurt import raw,repack_fixed_global
from repack_part_records_lossless import repack as repack_global
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose
def build(data,manifest_sha,progress=lambda x:None):
 need(sha(data)==PARENT,'Wrong exact parent');need(sha((TD/'manifest.json').read_bytes())==manifest_sha,'Target manifest changed');meta=json.loads((TD/'manifest.json').read_text('utf8'))
 for name,h in meta['source_files'].items():need(sha((ROOT/name).read_bytes())==h,'Source changed '+name)
 a=Archive(data);targets={n:{b:np.array(Image.open(TD/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in REFS}
 for n,ls in targets.items():
  for b,v in ls.items():need(sha(v.tobytes())==meta['targets'][str(n)][str(b)],'Target pixels changed')
 changes={b:{}for b in PBS};raws={};groups=[];gpu=0
 for n in REFS:
  nr,pp=pack_planes(bytes(4096),32,[crop(targets[n][b])for b in PBS],set(range(32))-{0,16},[24]*5);atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256)
  for b,ps in zip(PBS,pp):
   rr=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in ps)
   if not rr:need(not atlas[:16,:16].any(),'Blank tile occupied');rr=struct.pack('<BBbb',0,0,-8,-8)
   need(len(rr)//4<=24,'Part limit exceeded')
   for fl,t,x,y in struct.iter_unpack('<BBbb',rr):
    if t%16==0:need(not atlas[t//16*16:t//16*16+16,0].any(),f'GPU U edge {n}/{b}/{t}')
    if fl&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),f'GPU V edge {n}/{b}/{t}')
    gpu+=1
   changes[b][n]=rr
  raws[n]=nr;groups.append({'ref':n,'raw_sha256':sha(nr),'parts':{str(b):len(changes[b][n])//4 for b in PBS},'old_stream_owners':[f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']]});progress(groups[-1])
 nc=a.c;slack={};methods={}
 for b,rr in changes.items():
  try:nc,slack[b]=repack_parts(nc,b,rr);methods[b]='exact_record_repack'
  except ValueError:nc,slack[b],methods[b]=repack_global(nc,b,rr)
 progress({'part_slack':slack});ng,gfx=repack_fixed_global(a,raws,{n:32 for n in REFS});new=replace_entry(replace_entry(data,2,ng),3,nc);actual=Archive(new);need(bank_offsets(nc)==bank_offsets(a.c),'Part bank boundaries changed')
 total=nonraw=layers=kept=partial=otherparts=0
 for gb,bank in enumerate(a.banks):
  nb=actual.banks[gb];need((bank['base'],bank['end'],len(bank['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Graphics bank boundaries changed')
  for f in bank['frames']:
   n=f['index'];selected=gb==0 and n in REFS;need(raw(actual,gb,n)==(raws[n]if selected else raw(a,gb,n)),f'Raw mismatch {gb}/{n}');total+=1;nonraw+=not selected
 for n in range(237):
  if n in(105,*range(175,183)):continue
  for b in PBS:
   need(np.array_equal(actual.layer(n,b)[0],targets[n][b]if n in targets else a.layer(n,b)[0]),f'Layer mismatch {n}/{b}');layers+=1;kept+=n not in targets
  if n in targets:
   for arm in(1,2):
    for mask in range(16):need(actual.composite(n,mask,arm)[0].tobytes()==compose(a,targets[n],mask,arm).tobytes(),'Partial RGBA differs');partial+=1
   for form,mask in(('before',15),('after',0)):need(actual.composite(n,mask)[0].tobytes()==Image.open(TD/f'{form}_{n:03}.png').convert('RGBA').tobytes(),'Complete source body differs')
 for b in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
   if b in PBS and n in REFS:continue
   need(records(actual.c,b,n)==records(a.c,b,n),'Non-target part record changed');otherparts+=1
 return new,{'passed':True,'parent_sha256':PARENT,'candidate_sha256':sha(new),'target_manifest_sha256':manifest_sha,'refs':list(REFS),'groups':groups,'part_slack':slack,'part_storage_methods':methods,'graphics':gfx,'counts':{'raw':total,'non_target_raw':nonraw,'layers':layers,'non_target_layers':kept,'partial_RGBA':partial,'non_target_records':otherparts,'GPU_parts':gpu},'preserved_entries':protected_entries(data,new),'art_pixel_loss':False,'runtime_verified':False,'scope':'고정은행4참조 정적 후보. 원MIPS/독립/최종미술/실기 별도.'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='ultimate_victory_pack01');ap.add_argument('--manifest-sha',required=True);z=ap.parse_args();o=(H/z.output).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh owned output');o.mkdir();progress=[]
 def log(v):progress.append(v);write(o/'progress.json',progress);print(json.dumps(v),flush=True)
 try:new,proof=build(P.read_bytes(),z.manifest_sha,log)
 except Exception as e:write(o/'report.json',{'passed':False,'error':str(e),'arc_written':False,'progress':progress});raise
 (o/'PL02_U.ARC').write_bytes(new);actual=Archive(new)
 for form,mask in(('before',15),('after',0)):
  for i,ns in enumerate(((204,205),(206,207))):page([(f'{n} actual {form}',actual.composite(n,mask)[0])for n in ns],actual.composite(0,mask)[0],o/f'{form}_readback_{i:02}.png',cols=2,scale=5)
 for n in REFS:page([(f'{n} mask{mask}',actual.composite(n,mask,1)[0])for mask in range(16)],actual.composite(0,0)[0],o/f'partial_{n}.png',cols=4,scale=3)
 write(o/'report.json',proof);print(json.dumps({'candidate':sha(new),'counts':proof['counts']}))
if __name__=='__main__':main()
