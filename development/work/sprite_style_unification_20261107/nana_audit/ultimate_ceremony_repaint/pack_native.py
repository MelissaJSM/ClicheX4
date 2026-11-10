"""새 등장10참조를 고정 은행에 패킹하고 비대상/부분표시를 대조한다."""
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
from src.psx_player import composition_frame,bank_offsets
from scripts.discover_inputs import psx_arc
from prepare_arrival_targets import composite
PBS=(0,5,6,7,8);REFS=(130,131,133,134,135,136,137,138,139,141)
PARENT=N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC'
BEFORE='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
def build(parent,targets,meta,all_rgba=True):
 need(sha(parent)==BEFORE,'Parent SHA');a=Archive(parent);need(set(targets)=={(n,pb)for n in REFS for pb in PBS},'Target set')
 for (n,pb),z in targets.items():
  need(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<48,'Target format');need(sha(z.tobytes())==meta['targets'][str(n)][str(pb)],'Target hash')
 replacements={};counts={};changes={pb:{}for pb in PBS};groups=[]
 for n in REFS:
  nr,assign=pack_planes(bytes(4096),32,[targets[n,pb][80:240,80:240]for pb in PBS],set(range(32))-{0,16},[16]*5)
  replacements[n]=nr;counts[n]=32
  for pb,rr in zip(PBS,assign):changes[pb][n]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80)for t,x,y,flag in rr)
  groups.append({'refs':[n],'parts':{str(pb):len(rr)for pb,rr in zip(PBS,assign)},'used_tiles':sorted({t for rr in assign for t,x,y,flag in rr}),'raw_sha256':sha(nr)})
  print(json.dumps({'packed_ref':n,'parts':groups[-1]['parts'],'tiles':len(groups[-1]['used_tiles'])}),flush=True)
 # 131 and the unchanged pure-energy132 share their historical stream. Split
 # only storage:132 keeps every decoded byte/count and all composition records.
 support=[]
 selected_offsets={a.banks[0]['frames'][n]['offset']for n in REFS}
 for f in a.banks[0]['frames']:
  n=f['index']
  if f['offset']in selected_offsets and n not in REFS:
   replacements[n]=raw(a,0,n);counts[n]=f['tile_count'];support.append(n)
 need(support==[132],'Only expected pure energy support132')
 nc=a.c;slack={}
 for pb in PBS:nc,slack[pb]=repack_parts(nc,pb,changes[pb])
 ng,packing=repack_variable(a.g,replacements,counts);result=replace_entry(replace_entry(parent,2,ng),3,nc);b=Archive(result)
 rawcount=nonraw=0
 for gb,bank in enumerate(a.banks):
  need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Bank boundaries')
  for f in bank['frames']:
   n=f['index'];expected=replacements[n]if gb==0 and n in replacements else raw(a,gb,n);need(raw(b,gb,n)==expected,f'Raw{gb}/{n}');rawcount+=1;nonraw+=not(gb==0 and n in REFS)
 layers=nonlayers=0
 for n in range(237):
  if n in PLACEHOLDERS:continue
  for pb in PBS:
   expected=targets[n,pb]if n in REFS else a.layer(n,pb)[0];need(np.array_equal(b.layer(n,pb)[0],expected),f'Layer{n}/{pb}');layers+=1;nonlayers+=n not in REFS
 otherparts=0
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   if pb in PBS and n in REFS:continue
   need(records(a.c,pb,n)==records(b.c,pb,n),f'Composition{pb}/{n}');otherparts+=1
 need(a.p==b.p,'Palette')
 for e in psx_arc(parent):
  if int(e['type'],16)in(2,3):continue
  s=slice(e['offset'],e['offset']+e['size']);need(parent[s]==result[s],'Other entries')
 rgba=0
 for n in(range(237)if all_rgba else REFS):
  if n in PLACEHOLDERS:continue
  for mask in range(16):
   for arm in(1,2):
    expected=composite(a,{pb:targets[n,pb]for pb in PBS},mask,arm)if n in REFS else a.composite(n,mask,arm)[0]
    need(b.composite(n,mask,arm)[0].tobytes()==expected.tobytes(),f'RGBA{n}/{mask}/{arm}');rgba+=1
 report={'passed':True,'before':BEFORE,'after':sha(result),'refs':list(REFS),'support_raw_unchanged':support,'raw_checked':rawcount,'nonselected_raw_exact':nonraw,'layers_checked':layers,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':otherparts,'rgba_combinations':rgba,'target_rgba_combinations':320,'groups':groups,'packing':packing,'composition_slack':slack,'palette_and_other_entries_exact':True,'frozen':False,'runtime_verified':False,'scope':'登場5新몸체+5파생의고정은행native후보.원효과좌표/규칙보존,132공유스트림분리시decodedraw불변.미술최종/독립/원MIPS/실기별도.'}
 return result,report
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--targets',default='arrival_targets_probe_v2');ap.add_argument('--out',default='packed_arrival_diagnostic_v1');ap.add_argument('--probe',action='store_true');args=ap.parse_args();td=D/args.targets;meta=json.loads((td/'manifest.json').read_text('utf8'));targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS};out=(D/args.out).resolve();need(out.is_relative_to(D.resolve())and not out.exists(),'New owned path');result,report=build(PARENT.read_bytes(),targets,meta,not args.probe)
 out.mkdir();write(out/'verification.json',{**report,'targets_manifest':(td/'manifest.json').relative_to(ROOT).as_posix(),'targets_manifest_sha256':digest(td/'manifest.json')})
 if not args.probe:
  (out/'PL02_U.ARC').write_bytes(result);b=Archive(result)
  for k,ns in enumerate(((133,135),(136,137),(138,139),(130,131),(134,141)),1):helper.grid([(str(n),[('old before',Archive(PARENT.read_bytes()).composite(n,15)[0]),('new before',b.composite(n,15)[0]),('old after',Archive(PARENT.read_bytes()).composite(n)[0]),('new after',b.composite(n)[0])])for n in ns],out/f'readback_{k}.png',6)
  write(out/'proposal.json',{'project':'ver_rin_nana','baseline_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','parent_arc_sha256':BEFORE,'files':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','after':sha(result),'parent_arc_sha256':BEFORE}}})
 print(json.dumps({'after':sha(result),'packing':report['packing'],'slack':report['composition_slack'],'written_arc':not args.probe}))
if __name__=='__main__':main()
