"""허용된 사다리7참조를 기존5공유그룹/고정은행에 패킹한다."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw,PLACEHOLDERS
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable,pack_planes
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,bank_offsets,indexed_atlas
from scripts.discover_inputs import psx_arc
from prepare_first7_targets import composite
PBS=(0,5,6,7,8);REFS=(143,144,145,146,147,154,183)
PARENT=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC'
BEFORE='493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29'
def build(parent,targets,meta,all_rgba=True):
 need(sha(parent)==BEFORE,'Parent SHA');a=Archive(parent);need(set(targets)=={(n,pb)for n in REFS for pb in PBS},'Exact targets')
 for (n,pb),z in targets.items():need(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16 and sha(z.tobytes())==meta['targets'][str(n)][str(pb)],'Target hash/format')
 raw_groups={}
 for n in REFS:raw_groups.setdefault(a.banks[0]['frames'][n]['offset'],[]).append(n)
 replacements={};counts={};changes={pb:{}for pb in PBS};groups=[];gpu_parts=0
 for off,ns in raw_groups.items():
  need(set(ns)=={f['index']for f in a.banks[0]['frames']if f['offset']==off},'Outside raw owner')
  keys=[(n,pb)for n in ns for pb in PBS];nr,assign=pack_planes(bytes(4096),32,[targets[k][80:240,80:240]for k in keys],set(range(32))-{0,16},[16]*len(keys))
  for n in ns:replacements[n]=nr;counts[n]=32
  for (n,pb),rr in zip(keys,assign):changes[pb][n]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80)for t,x,y,flag in rr)
  atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256);need(not atlas[:,0].any(),'GPU U boundary')
  for rr in assign:
   for t,x,y,flag in rr:
    need(t not in (0,16),'Excluded GPU edge tile')
    if flag&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),'GPU V boundary')
    gpu_parts+=1
  groups.append({'refs':ns,'parts':{f'{n}/{pb}':len(rr)for (n,pb),rr in zip(keys,assign)},'used_tiles':sorted({t for rr in assign for t,x,y,flag in rr}),'raw_sha256':sha(nr),'shared_group_preserved':True})
  print(json.dumps({'packed_refs':ns,'parts':groups[-1]['parts'],'tiles':len(groups[-1]['used_tiles'])}),flush=True)
 nc=a.c;slack={}
 for pb in PBS:nc,slack[pb]=repack_parts(nc,pb,changes[pb])
 ng,packing=repack_variable(a.g,replacements,counts);result=replace_entry(replace_entry(parent,2,ng),3,nc);b=Archive(result);need(bank_offsets(a.c)==bank_offsets(b.c),'Part bank boundaries')
 rc=nonraw=layers=nonlayers=parts=rgba=target_rgba=0
 for gb,bank in enumerate(a.banks):
  need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Graphics bank boundaries')
  for f in bank['frames']:
   n=f['index'];new=gb==0 and n in REFS;need(raw(b,gb,n)==(replacements[n]if new else raw(a,gb,n)),f'Raw{gb}/{n}');rc+=1;nonraw+=not new
 for n in range(237):
  if n in PLACEHOLDERS:continue
  for pb in PBS:
   expected=targets[n,pb]if n in REFS else a.layer(n,pb)[0];need(np.array_equal(b.layer(n,pb)[0],expected),f'Layer{n}/{pb}');layers+=1;nonlayers+=n not in REFS
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   if pb in PBS and n in REFS:continue
   need(records(a.c,pb,n)==records(b.c,pb,n),f'Composition{pb}/{n}');parts+=1
 need(a.p==b.p,'Palette')
 for e in psx_arc(parent):
  if int(e['type'],16)in(2,3):continue
  s=slice(e['offset'],e['offset']+e['size']);need(parent[s]==result[s],'Other entry')
 for n in(range(237)if all_rgba else REFS):
  if n in PLACEHOLDERS:continue
  for mask in range(16):
   for arm in (1,2):
    expected=composite(a,{pb:targets[n,pb]for pb in PBS},mask,arm)if n in REFS else a.composite(n,mask,arm)[0]
    need(b.composite(n,mask,arm)[0].tobytes()==expected.tobytes(),f'RGBA{n}/{mask}/{arm}');rgba+=1;target_rgba+=n in REFS
 for ns in ((144,145),(146,147)):need(len({b.banks[0]['frames'][n]['offset']for n in ns})==1,'Physical mirrored stream sharing')
 report={'passed':True,'before':BEFORE,'after':sha(result),'refs':list(REFS),'remaining_unmodified_refs':[148,149,150,151,152,153,155],'raw_checked':rc,'nonselected_raw_exact':nonraw,'layers_checked':layers,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':parts,'rgba_combinations':rgba,'target_rgba_combinations':target_rgba,'gpu_parts_safe':gpu_parts,'groups':groups,'packing':packing,'composition_slack':slack,'palette_and_other_entries_exact':True,'frozen':False,'runtime_verified':False,'scope':'허용된5고유몸체와2반전만의 별도후보. 보류149151153 및연동148150152155의모든raw/층/조립/표시보존. 기존5공유그룹/빈층비대상공유소유/은행경계보존. 새MIPS/독립/원순서/최종미술은별도.'}
 return result,report
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--targets',default='first7_targets_v1');ap.add_argument('--out',default='packed_first7_diagnostic_v1');ap.add_argument('--probe',action='store_true');args=ap.parse_args();td=D/args.targets;meta=json.loads((td/'manifest.json').read_text('utf8'));targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS};out=(D/args.out).resolve();need(out.is_relative_to(D.resolve())and not out.exists(),'Fresh owned path')
 result,report=build(PARENT.read_bytes(),targets,meta,not args.probe);out.mkdir();write(out/'verification.json',{**report,'targets_manifest':(td/'manifest.json').relative_to(ROOT).as_posix(),'targets_manifest_sha256':digest(td/'manifest.json')})
 if not args.probe:
  (out/'PL02_U.ARC').write_bytes(result);b=Archive(result);a=Archive(PARENT.read_bytes())
  for i,ns in enumerate(((143,144,145),(146,147),(154,183)),1):helper.grid([(str(n),[('old before',a.composite(n,15)[0]),('new before',b.composite(n,15)[0]),('old after',a.composite(n)[0]),('new after',b.composite(n)[0])])for n in ns],out/f'readback_{i}.png',6)
  write(out/'proposal.json',{'project':'ver_rin_nana','baseline_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','parent_arc_sha256':BEFORE,'files':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','after':sha(result),'parent_arc_sha256':BEFORE}}})
 print(json.dumps({'after':sha(result),'packing':report['packing'],'slack':report['composition_slack'],'written_arc':not args.probe}))
if __name__=='__main__':main()
