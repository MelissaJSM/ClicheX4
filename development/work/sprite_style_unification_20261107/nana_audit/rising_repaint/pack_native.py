"""새 라이징7참조/35층만 고정 PL00 은행에 패킹하는 후보 제작기."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw,PLACEHOLDERS
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,bank_offsets
from scripts.discover_inputs import psx_arc
PBS=(0,5,6,7,8);REFS=(100,101,102,103,104,231,232)
BEFORE='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa'
PARENT=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC'

def composite(a,layers,mask,arm=2):
 im=a.rgba(layers[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(layers[pb],32 if pb==7 and arm==2 else 16))
 return im

def validate_targets(targets,manifest):
 need(manifest['source_arc_sha256']==BEFORE,'Target parent');need(set(targets)=={(n,pb)for n in REFS for pb in PBS},'Target coverage')
 need({q['ref']for q in manifest['frames']}==set(REFS)and len(manifest['frames'])==7,'Manifest coverage')
 for q in manifest['frames']:
  for pb in PBS:
   ar=targets[q['ref'],pb];need(ar.shape==(384,384)and ar.dtype==np.uint8 and ar.max()<16,'Target format');need(sha(ar.tobytes())==(q['base_sha256']if pb==0 else q['layers'][str(pb)]),'Target hash')
   outside=ar.copy();outside[80:240,80:240]=0;need(not outside.any(),'Target outside native registration window')
 for pb in PBS:need(np.array_equal(targets[231,pb],targets[232,pb]),'231/232 exact relation')

def build(data,targets,manifest):
 need(sha(data)==BEFORE,'Parent hash');a=Archive(data);validate_targets(targets,manifest)
 replacement={};counts={};changes={pb:{}for pb in PBS};groups=[]
 for ns in((100,),(101,),(102,),(103,),(104,),(231,232)):
  ps=[(ns[0],pb)for pb in PBS];newraw,assign=pack_shared(bytes(4096),32,[targets[k][80:240,80:240]for k in ps],set(range(32))-{0,16},[16]*5)
  for ref in ns:
   replacement[ref]=newraw;counts[ref]=32
   for(ref0,pb),p in zip(ps,assign):
    need(len(p)<=16,'Part limit');changes[pb][ref]=b''.join(struct.pack('<BBbb',flags,t,x-80,y-80)for t,x,y,flags in p)
  groups.append({'refs':list(ns),'parts':{str(pb):len(p)for(_,pb),p in zip(ps,assign)}})
 nc=a.c;slack={}
 for pb in PBS:nc,slack[pb]=repack_parts(nc,pb,changes[pb])
 ng,packing=repack_variable(a.g,replacement,counts);result=replace_entry(replace_entry(a.data,2,ng),3,nc);b=Archive(result);rawcount=nonraw=0
 for gb,bank in enumerate(a.banks):
  need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Bank boundary')
  for n in range(len(bank['frames'])):
   expect=replacement[n]if gb==0 and n in replacement else raw(a,gb,n);need(raw(b,gb,n)==expect,f'Raw {gb}/{n}');rawcount+=1;nonraw+=not(gb==0 and n in replacement)
 layercount=nonlayers=0
 for n in range(237):
  if n in PLACEHOLDERS:continue
  for pb in PBS:
   expect=targets[n,pb]if(n,pb)in targets else a.layer(n,pb)[0];need(np.array_equal(b.layer(n,pb)[0],expect),f'Layer {n}/{pb}');layercount+=1;nonlayers+=(n,pb)not in targets
 parts=0;gpu=0
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   if pb in PBS and n in REFS:continue
   need(records(a.c,pb,n)==records(b.c,pb,n),f'Parts {n}/{pb}');parts+=1
 for n in REFS:
  for pb in PBS:
   for p in composition_frame(b.c,pb,n)['parts']:need(p['tile']%16!=0 and not p['flip_y'],'Unsafe GPU boundary');gpu+=1
 need(a.p==b.p,'Palette');before=bytearray(a.data);after=bytearray(result)
 for e in psx_arc(a.data):
  if int(e['type'],16)in(2,3):before[e['offset']:e['offset']+e['size']]=after[e['offset']:e['offset']+e['size']]
 need(before==after,'Other entry')
 checks=selected=0
 for n in range(237):
  if n in PLACEHOLDERS:continue
  for arm in(1,2):
   for mask in range(16):
    expected=composite(a,{pb:targets[n,pb]for pb in PBS},mask,arm)if n in REFS else a.composite(n,mask,arm)[0]
    actual=b.composite(n,mask,arm)[0];need(actual.tobytes()==expected.tobytes(),f'RGBA {n}/{mask}/{arm}');checks+=1;selected+=n in REFS
    if n in REFS:need(label(np.array(actual)[:,:,3]>0,np.ones((3,3)))[1]==1,f'Isolated part {n}/{mask}/{arm}')
 verification={'passed':True,'scope':'새 기본/포스 라이징7 기술후보. 미술 최종수용·실기 미확인.','before':BEFORE,'after':sha(result),'raw_checked':rawcount,'nonselected_raw_exact':nonraw,'layers_checked':layercount,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':parts,'composition_slack':slack,'packing':packing,'groups':groups,'palette_and_other_entries_exact':True,'gpu_boundary_parts_checked':gpu,'rgba_combinations':checks,'target_combinations':selected,'other_combinations_exact':checks-selected,'target_all_masks_single_connected_body':True,'runtime_verified':False}
 return result,verification

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='packed_base_candidate_v1');args=ap.parse_args();out=(D/args.out).resolve();need(out.is_relative_to(D.resolve())and not out.exists(),'Fresh own output')
 td=D/'joint_layers_probe_v2';manifest=json.loads((td/'manifest.json').read_text('utf8'));targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS};result,verification=build(PARENT.read_bytes(),targets,manifest);out.mkdir();(out/'PL00_U.ARC').write_bytes(result);b=Archive(result)
 for i,ns in enumerate(((100,101),(102,103),(104,231))):
  helper.grid([(f'Rising {n}',[('basic idle',b.composite(0)[0]),('new base',b.composite(n)[0]),('Fourth idle',b.composite(0,15)[0]),('new Fourth arm2',b.composite(n,15)[0]),('new Fourth arm1',b.composite(n,15,1)[0])])for n in ns],out/f'readback_{i+1}.png',6)
 verification['targets_manifest_sha256']=digest(td/'manifest.json');write(out/'verification.json',verification)
 write(out/'proposal.json',{'project':'ver_rin_nana','parent_arc_sha256':BEFORE,'files':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':BEFORE,'after':sha(result)}},'candidate_only':True})
 print(json.dumps({'after':sha(result),'raw':verification['raw_checked'],'rgba':verification['rgba_combinations'],'slack':verification['composition_slack'],'packing':verification['packing']}))
if __name__=='__main__':main()
