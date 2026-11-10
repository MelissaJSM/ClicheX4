"""새 탑승65층을 기존4공유스트림·고정은행에 저장하고 재독출한다."""
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
from prepare_targets import comp,PBS,KEYS,DY,PARENT,BEFORE
REFS=tuple(DY)
def build(parent,targets,meta,all_rgba=True):
 need(sha(parent)==BEFORE,'Parent SHA');a=Archive(parent);need(set(targets)=={(n,pb)for n in REFS for pb in PBS},'Exact targets')
 for (n,pb),z in targets.items():need(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16 and sha(z.tobytes())==meta['targets'][str(n)][str(pb)],'Target hash/format')
 replacements={};counts={};changes={pb:{}for pb in PBS};groups=[];gpu_parts=0
 for key in KEYS:
  ns=[key]if key==174 else list(range(key,key+4));f=a.banks[0]['frames'][key];off=f['offset'];count=f['tile_count'];need(set(ns)=={q['index']for q in a.banks[0]['frames']if q['offset']==off},'Outside raw owner')
  nr,assign=pack_planes(bytes(count*128),count,[targets[key,pb][80:240,80:240]for pb in PBS],set(range(count))-{0,16},[16]*5)
  atlas=np.frombuffer(indexed_atlas(nr,count)[0],np.uint8).reshape(-1,256);need(not atlas[:,0].any(),'GPU U boundary')
  for n in ns:
   replacements[n]=nr;counts[n]=count
   for pb,rr in zip(PBS,assign):
    need(np.array_equal(targets[n,pb],np.roll(targets[key,pb],DY[n],0)),'Exact native Y alias');changes[pb][n]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80+DY[n])for t,x,y,flag in rr)
    for t,x,y,flag in rr:
     need(t not in(0,16),'Excluded GPU edge tile')
     if flag&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),'GPU V boundary')
     gpu_parts+=1
  groups.append({'refs':ns,'original_tile_count':count,'new_tile_count':count,'parts_per_layer':{str(pb):len(rr)for pb,rr in zip(PBS,assign)},'used_tiles':sorted({t for rr in assign for t,x,y,flag in rr}),'raw_sha256':sha(nr),'shared_group_preserved':True});print(json.dumps(groups[-1]),flush=True)
 nc=a.c;slack={}
 for pb in PBS:nc,slack[pb]=repack_parts(nc,pb,changes[pb])
 ng,packing=repack_variable(a.g,replacements,counts);result=replace_entry(replace_entry(parent,2,ng),3,nc);b=Archive(result);need(bank_offsets(a.c)==bank_offsets(b.c),'Part bank boundaries')
 rc=nonraw=layers=nonlayers=parts=rgba=target_rgba=0
 for gb,bank in enumerate(a.banks):
  need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Graphics bank boundaries')
  for q in bank['frames']:
   n=q['index'];new=gb==0 and n in REFS;need(raw(b,gb,n)==(replacements[n]if new else raw(a,gb,n)),f'Raw{gb}/{n}');need(q['tile_count']==b.banks[gb]['frames'][n]['tile_count'],'Original tile count');rc+=1;nonraw+=not new
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
   for arm in(1,2):
    expected=comp(a,{pb:targets[n,pb]for pb in PBS},mask,arm)if n in REFS else a.composite(n,mask,arm)[0];need(b.composite(n,mask,arm)[0].tobytes()==expected.tobytes(),f'RGBA{n}/{mask}/{arm}');rgba+=1;target_rgba+=n in REFS
 for g in groups:need(len({b.banks[0]['frames'][n]['offset']for n in g['refs']})==1,'Physical Y alias stream sharing')
 return result,{'passed':True,'before':BEFORE,'after':sha(result),'refs':list(REFS),'raw_checked':rc,'nonselected_raw_exact':nonraw,'layers_checked':layers,'target_layers_exact':65,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':parts,'rgba_combinations':rgba,'target_rgba_combinations':target_rgba,'gpu_parts_safe':gpu_parts,'groups':groups,'packing':packing,'composition_slack':slack,'palette_and_other_entries_exact':True,'frozen':False,'runtime_verified':False,'scope':'새4몸체/양의상8원화와 원Y별칭9개의 후보. 원4공유stream/각타일수/은행경계·비대상 소유 보존. 독립·MIPS·원순서·실기는 별도.'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--targets',default='targets_v1');ap.add_argument('--out',default='packed_vehicle_candidate_v1');ap.add_argument('--probe',action='store_true');args=ap.parse_args();td=D/args.targets;meta=json.loads((td/'manifest.json').read_text('utf8'));targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS};out=(D/args.out).resolve();need(out.is_relative_to(D.resolve())and not out.exists(),'Fresh owned path')
 result,report=build(PARENT.read_bytes(),targets,meta,not args.probe);out.mkdir();write(out/'verification.json',{**report,'targets_manifest':(td/'manifest.json').relative_to(ROOT).as_posix(),'targets_manifest_sha256':digest(td/'manifest.json')})
 if not args.probe:
  (out/'PL02_U.ARC').write_bytes(result);b=Archive(result);a=Archive(PARENT.read_bytes())
  for i in range(0,len(REFS),3):helper.grid([(str(n),[('idle',b.composite(0,15)[0]),('new jacket',b.composite(n,15)[0]),('new bare',b.composite(n)[0]),('old bare',a.composite(n)[0])])for n in REFS[i:i+3]],out/f'readback_{i//3+1}.png',6)
  write(out/'proposal.json',{'project':'ver_rin_nana','baseline_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','parent_arc_sha256':BEFORE,'files':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','after':sha(result),'parent_arc_sha256':BEFORE}}})
 print(json.dumps({'after':sha(result),'packing':report['packing'],'slack':report['composition_slack'],'written_arc':not args.probe}))
if __name__=='__main__':main()
