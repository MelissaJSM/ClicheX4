"""138/139 새10층을 최신 PL00 고정은행에 패킹하는 별도 후보 제작기."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw,PLACEHOLDERS
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable,pack_planes
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,bank_offsets
from scripts.discover_inputs import psx_arc
from prepare_joint_layers import composite
PBS=(0,5,6,7,8);REFS=(138,139)

def validate(parent,targets,meta,parent_hash):
 need(sha(parent)==parent_hash,'Parent SHA');need(set(targets)=={(n,pb)for n in REFS for pb in PBS},'Target set')
 a=Archive(parent);art=Archive((ROOT/meta['art_parent_arc']).read_bytes());need(sha(art.data)==meta['art_parent_sha256'],'Art parent')
 need(a.p==art.p,'Art palette preserved')
 for q in meta['frames']:
  n=q['ref'];need(n in REFS,'Manifest ref')
  for pb in PBS:
   z=targets[n,pb];need(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16,'Target format');need(sha(z.tobytes())==q['layer_hashes'][str(pb)],'Target hash')
   need(np.array_equal(a.layer(n,pb)[0],art.layer(n,pb)[0]),'Parent target unchanged since generation')
   inside=z.copy();inside[80:240,80:240]=0;need(not inside.any(),'Outside packing canvas')
 for pb in PBS:
  z=np.zeros_like(targets[138,pb]);z[:-1]=targets[138,pb][1:];need(np.array_equal(z,targets[139,pb]),'139 yminus1 relation')
 return a

def build(parent,targets,meta,parent_hash,all_rgba=True):
 a=validate(parent,targets,meta,parent_hash);changes={pb:{}for pb in PBS};replacements={};counts={};groups=[]
 for n in REFS:
  nr,assign=pack_planes(bytes(4096),32,[targets[n,pb][80:240,80:240]for pb in PBS],set(range(32))-{0,16},[16]*5)
  replacements[n]=nr;counts[n]=32
  for pb,rr in zip(PBS,assign):changes[pb][n]=b''.join(struct.pack('<BBbb',flags,t,x-80,y-80)for t,x,y,flags in rr)
  groups.append({'ref':n,'parts':{str(pb):len(rr)for pb,rr in zip(PBS,assign)},'used_tiles':sorted({t for rr in assign for t,x,y,flags in rr}),'raw_sha256':sha(nr)})
  print(json.dumps(groups[-1]),flush=True)
 support=[];offsets={a.banks[0]['frames'][n]['offset']for n in REFS}
 for f in a.banks[0]['frames']:
  if f['offset']in offsets and f['index']not in REFS:
   n=f['index'];replacements[n]=raw(a,0,n);counts[n]=f['tile_count'];support.append(n)
 need(not support,'138139 source streams independent')
 nc=a.c;slack={}
 for pb in PBS:nc,slack[pb]=repack_parts(nc,pb,changes[pb])
 ng,packing=repack_variable(a.g,replacements,counts);result=replace_entry(replace_entry(parent,2,ng),3,nc);b=Archive(result);rc=nr=0
 for gb,bank in enumerate(a.banks):
  need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Bank boundaries')
  for f in bank['frames']:
   n=f['index'];expected=replacements[n]if gb==0 and n in REFS else raw(a,gb,n);need(raw(b,gb,n)==expected,f'Raw {gb}/{n}');rc+=1;nr+=not(gb==0 and n in REFS)
 lc=nl=0
 for n in range(237):
  if n in PLACEHOLDERS:continue
  for pb in PBS:need(np.array_equal(b.layer(n,pb)[0],targets[n,pb]if n in REFS else a.layer(n,pb)[0]),f'Layer {n}/{pb}');lc+=1;nl+=n not in REFS
 pc=gpu=0
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   if pb in PBS and n in REFS:continue
   need(records(a.c,pb,n)==records(b.c,pb,n),f'Composition {pb}/{n}');pc+=1
 for n in REFS:
  for pb in PBS:
   for p in composition_frame(b.c,pb,n)['parts']:need(p['tile']%16!=0 and not p['flip_y'],'GPU boundary');gpu+=1
 need(a.p==b.p,'Palette')
 for e in psx_arc(parent):
  if int(e['type'],16)in(2,3):continue
  s=slice(e['offset'],e['offset']+e['size']);need(parent[s]==result[s],'Other entry')
 rgba=0
 for n in(range(237)if all_rgba else REFS):
  if n in PLACEHOLDERS:continue
  for mask in range(16):
   for arm in(1,2):
    expected=composite(a,{pb:targets[n,pb]for pb in PBS},mask,arm)if n in REFS else a.composite(n,mask,arm)[0];actual=b.composite(n,mask,arm)[0];need(actual.tobytes()==expected.tobytes(),f'RGBA {n}/{mask}/{arm}');rgba+=1
    if n in REFS:need(label(np.array(actual)[:,:,3]>0,np.ones((3,3)))[1]==1,'Part isolation')
 return result,{'passed':True,'before':parent_hash,'after':sha(result),'refs':list(REFS),'raw_checked':rc,'nonselected_raw_exact':nr,'layers_checked':lc,'nonselected_layers_exact':nl,'nonselected_compositions_exact':pc,'gpu_parts_checked':gpu,'rgba_combinations':rgba,'target_rgba_combinations':64,'groups':groups,'packing':packing,'composition_slack':slack,'runtime_verified':False,'target_all_masks_single_connected_body':True,'palette_other_entries_exact':True}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--parent',required=True);ap.add_argument('--parent-sha',required=True);ap.add_argument('--out',required=True);ap.add_argument('--probe',action='store_true');args=ap.parse_args()
 p=ROOT/args.parent;td=D/'joint_layers_probe_v3';meta=json.loads((td/'manifest.json').read_text('utf8'));targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS};out=(D/args.out).resolve();need(out.is_relative_to(D.resolve())and not out.exists(),'New owned output')
 result,report=build(p.read_bytes(),targets,meta,args.parent_sha,not args.probe);out.mkdir();report.update({'parent_path':p.relative_to(ROOT).as_posix(),'targets_manifest_sha256':digest(td/'manifest.json'),'probe_only':args.probe});write(out/'verification.json',report)
 if not args.probe:
  (out/'PL00_U.ARC').write_bytes(result);b=Archive(result);a=Archive(p.read_bytes())
  helper.grid([(str(n),[('old base',a.composite(n)[0]),('new base',b.composite(n)[0]),('old Fourth',a.composite(n,15)[0]),('new Fourth',b.composite(n,15)[0])])for n in REFS],out/'readback.png',7)
  write(out/'proposal.json',{'project':'ver_rin_nana','parent_arc_sha256':args.parent_sha,'files':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':args.parent_sha,'after':sha(result)}},'candidate_only':True})
 print(json.dumps({'asset':sha(result),'packing':report['packing'],'slack':report['composition_slack'],'written_arc':not args.probe}))
if __name__=='__main__':main()
