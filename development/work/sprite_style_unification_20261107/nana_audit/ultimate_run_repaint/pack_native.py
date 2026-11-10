"""새 얼티밋 이동/사격32를 고정 은행·32타일 안에 패킹하는 별도 후보."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint'),str(D.parent/'ultimate_dash_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw,PLACEHOLDERS
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from repack_identical import repack_identical
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,bank_offsets
from scripts.discover_inputs import psx_arc
PBS=(0,5,6,7,8);REFS=tuple(range(1,33))
BEFORE='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'
def validate_source(data):
 need(sha(data)==BEFORE,'Parent hash');return Archive(data)
def validate_output(out):
 out=out.resolve();need(out.is_relative_to(D.resolve())and not out.exists(),'Fresh isolated output required');return out
def validate_targets(targets,manifest):
 need(manifest['source_arc_sha256']==BEFORE,'Target parent');need(set(targets)=={(n,pb)for n in REFS for pb in PBS},'Coverage')
 need({q['ref']for q in manifest['frames']}==set(REFS)and len(manifest['frames'])==32,'Manifest coverage')
 for q in manifest['frames']:
  for pb in PBS:
   ar=targets[q['ref'],pb];need(ar.shape==(384,384)and ar.dtype==np.uint8 and ar.max()<16,'Target format')
   need(sha(ar.tobytes())==q['layers'][str(pb)],'Target hash')
   outside=ar.copy();outside[80:240,80:240]=0;need(not outside.any(),'Outside packing window')
def build(a,targets,manifest):
 validate_targets(targets,manifest);replacement={};counts={};changes={pb:{}for pb in PBS};groups=[]
 for n in range(1,33,2):
  pairs=[(r,pb)for r in(n,n+1)for pb in PBS];blank=bytes(4096)
  try:
   newraw,assign=pack_shared(blank,32,[targets[k][80:240,80:240]for k in pairs],set(range(32))-{0,16},[16]*len(pairs));group=[([n,n+1],pairs,newraw,assign)];mode='paired'
  except ValueError as e:
   print(json.dumps({'split':[n,n+1],'reason':str(e)}),flush=True);group=[];mode='separate'
   for r in(n,n+1):
    keys=[(r,pb)for pb in PBS];rr,pp=pack_shared(blank,32,[targets[k][80:240,80:240]for k in keys],set(range(32))-{0,16},[16]*5);group.append(([r],keys,rr,pp))
  for refs,keys,rr,pp in group:
   for r in refs:replacement[r]=rr;counts[r]=32
   for(r,pb),parts in zip(keys,pp):
    need(len(parts)<=16,'Part limit');changes[pb][r]=b''.join(struct.pack('<BBbb',flags,t,x-80,y-80)for t,x,y,flags in parts)
   groups.append({'refs':refs,'mode':mode,'parts':{f'{r}/{pb}':len(p)for(r,pb),p in zip(keys,pp)}})
  print(json.dumps({'packed':[n,n+1],'mode':mode}),flush=True)
 nc=a.c;slack={}
 for pb in PBS:nc,slack[pb]=repack_parts(nc,pb,changes[pb])
 ng,packing=repack_identical(a.g,replacement,counts);result=replace_entry(replace_entry(a.data,2,ng),3,nc);b=Archive(result)
 rawcount=nonraw=0
 for gb,bank in enumerate(a.banks):
  need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Bank boundary')
  for n in range(len(bank['frames'])):
   expected=replacement[n]if gb==0 and n in replacement else raw(a,gb,n)
   need(raw(b,gb,n)==expected,f'Raw {gb}/{n}');rawcount+=1;nonraw+=not(gb==0 and n in replacement)
 layercount=nonlayers=0
 for n in range(237):
  if n in PLACEHOLDERS:continue
  for pb in PBS:
   expected=targets[n,pb]if(n,pb)in targets else a.layer(n,pb)[0]
   need(np.array_equal(b.layer(n,pb)[0],expected),f'Layer {n}/{pb}');layercount+=1;nonlayers+=(n,pb)not in targets
 parts=0;gpu=0
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   if pb in PBS and n in REFS:continue
   need(records(a.c,pb,n)==records(b.c,pb,n),f'Parts {n}/{pb}');parts+=1
 for n in REFS:
  for pb in PBS:
   for p in composition_frame(b.c,pb,n)['parts']:need(p['tile']%16!=0 and not p['flip_y'],'GPU edge');gpu+=1
 need(a.p==b.p,'Palette');check=bytearray(a.data)
 for e in psx_arc(a.data):
  if int(e['type'],16)in(2,3):check[e['offset']:e['offset']+e['size']]=result[e['offset']:e['offset']+e['size']]
 need(check==result,'Other entries')
 return result,{'passed':True,'before':BEFORE,'after':sha(result),'raw_checked':rawcount,'nonselected_raw_exact':nonraw,
  'layers_checked':layercount,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':parts,'composition_slack':slack,
  'packing':packing,'groups':groups,'gpu_parts':gpu,'palette_and_other_entries_exact':True,'gpu_boundary_guard':True,
  'runtime_verified':False,'common_boundary_art_review_pending':True}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',default='packed_run_diagnostic_v1');p.add_argument('--targets',default='joint_native_targets_v1');args=p.parse_args()
 out=validate_output(D/args.out);a=validate_source((D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC').read_bytes())
 td=D/args.targets;manifest=json.loads((td/'manifest.json').read_text('utf8'));targets={(r['ref'],pb):np.array(Image.open(td/f'layer{pb}_{r["ref"]:03}.png'))for r in manifest['frames']for pb in PBS}
 result,verify=build(a,targets,manifest);out.mkdir();(out/'PL02_U.ARC').write_bytes(result);b=Archive(result)
 for page,start in enumerate(range(1,33,8)):
  rows=[]
  for n in range(start,start+8,2):
   rows.append((f'run {n}/{n+1}',[('after idle',b.composite(0)[0]),('new after',b.composite(n)[0]),('after shot',b.composite(n+1)[0]),('before idle',b.composite(0,15)[0]),('new before',b.composite(n,15)[0]),('before shot',b.composite(n+1,15)[0])]))
  helper.grid(rows,out/f'readback_{page+1}.png',5)
 verify['targets_manifest_sha256']=digest(td/'manifest.json');write(out/'verification.json',verify)
 write(out/'proposal.json',{'project':'ver_rin_nana','baseline_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','parent_arc_sha256':BEFORE,
  'files':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','working_parent_before':BEFORE,'after':sha(result)}},'candidate_only':True})
 print(json.dumps({'after':sha(result),'graphics_slack':verify['packing']['remaining_slack'],'parts_slack':verify['composition_slack'],'out':str(out)}),flush=True)
if __name__=='__main__':main()
