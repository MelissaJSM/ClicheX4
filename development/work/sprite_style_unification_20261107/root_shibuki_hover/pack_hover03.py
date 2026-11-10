"""호버 원화50층과 저장 전용 타일순열을 고정 은행에 결속한다."""
from pathlib import Path
import sys,json,hashlib,struct,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];H=W/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(D),str(H),str(W/'nana_audit/native_restore')]
from native_pose_pack import need,Archive
from pack_shibuki_hurt import repack_fixed_global,raw
from repack_part_records_lossless import repack as global_parts
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.prepare_riko_ui import replace_entry
from scripts.optimize_rin_style_tiles import permute
from src.psx_player import composition_frame,bank_offsets,indexed_atlas
from src.psx_compress import encode_stream
from scripts.discover_inputs import psx_arc
from prepare_body_layers04 import comp
from preview_restore import helper
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
PARENT='4ceab054c4fa9170a0e785fb00baa01f05afaceb4d2dfc2dcc4e80eab30ee36f'
PBS=(0,5,6,7,8);REFS=tuple(range(221,231));STORAGE_KEYS=(39,41,43,49,59,61,65,79)
LOCK=D/'hover_input_lock03.json';LOCK_SHA='f2ff91ce1df30fa39adfae38111cb9afc62623b87056c818b410d293af0db561'
def validate(data,reader=lambda p:p.read_bytes()):
 need(sha(data)==PARENT,'New small-head parent hash')
 blob=reader(LOCK);need(sha(blob)==LOCK_SHA,'Input lock changed');lock=json.loads(blob)
 need(lock['parent_sha256']==PARENT,'Locked parent')
 for name,digest in lock['files'].items():
  p=(ROOT/name).resolve();need(p.is_relative_to(ROOT.resolve()),'Input path outside project');need(sha(reader(p))==digest,'Changed input '+name)
 return lock
def build(data):
 validate(data);a=Archive(data)
 lock=read(D/'packed_hover_shared_optimized02/input_lock.json');targets={};sources={}
 for n in REFS:
  for pb in PBS:
   q=lock['sources'][str(n)][str(pb)];p=(ROOT/q['path']).resolve();need(p.is_relative_to(ROOT.resolve())and sha(p.read_bytes())==q['sha256'],'Locked source PNG')
   z=np.array(Image.open(p));need(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16 and sha(z.tobytes())==lock['targets'][str(n)][str(pb)],'Locked target indices');targets[n,pb]=z;sources[q['path']]=q['sha256']
 old=Archive((H/'prepared_nova_strike_base01/PL00_U.ARC').read_bytes());need(sha(old.data)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e','Geometry parent')
 need(a.p==old.p,'Palette parent rebase');need(all(np.array_equal(a.layer(n,pb)[0],old.layer(n,pb)[0])for n in REFS for pb in PBS),'Hover50 rebase')
 raws={};counts={};changes={pb:{}for pb in PBS};groups=[];storage_proofs=[]
 for key in REFS[::2]:
  folder=D/('sharing_optimized03'if key in(221,225,229)else'packed_hover_shared_optimized02/tile_storage');proof=read(folder/f'{key}.json');nr=(folder/f'{key}.raw').read_bytes()
  need(sha(nr)==proof['output_raw_sha256']and len(nr)==4096 and len(encode_stream(nr))==proof['after'],'Optimized raw recipe')
  for j,n in enumerate((key,key+1)):
   raws[n]=nr;counts[n]=32
   for pb,rr in zip(PBS,proof['assignments'][j*5:(j+1)*5]):
    need(len(rr)<=24,'Target part limit24')
    changes[pb][n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rr)
  groups.append({'refs':[key,key+1],'recipe':(folder/f'{key}.json').relative_to(ROOT).as_posix(),'recipe_sha256':sha((folder/f'{key}.json').read_bytes()),'raw_sha256':sha(nr),'encoded_bytes':proof['after']})
 audit=read(H/'hover_existing_tileorder01/report.json');need(audit['parent_sha256']==sha(old.data),'Storage audit parent');selected=[]
 for g in audit['groups']:
  ns=g['refs']
  if ns[0]not in STORAGE_KEYS:continue
  need(ns==[ns[0],ns[0]+1],'Storage pair scope');selected+=ns;mp={int(k):v for k,v in g['mapping'].items()};nr=(H/f'hover_existing_tileorder01/{ns[0]:03}_trial_raw.bin').read_bytes();source=raw(a,0,ns[0])
  need(sha(source)==g['source_raw_sha256']and sha(nr)==g['optimized_raw_sha256'],'Storage parent/output hash')
  need(permute(nr,32,[mp[t]for t in range(32)])==source,'All32 tile inverse exact');need(all(mp[t]==t for t in g['optimization']['fixed_tiles']),'Fixed tile moved')
  for n in ns:
   need(raw(a,0,n)==source,'Storage pair raw');raws[n]=nr;counts[n]=32
   for pb in PBS:changes[pb][n]=b''.join(struct.pack('<BBbb',p['flags'],mp[p['tile']],p['x'],p['y'])for p in composition_frame(a.c,pb,n)['parts'])
  storage_proofs.append(g)
 need(set(selected)=={n for key in STORAGE_KEYS for n in(key,key+1)},'Exact storage refs')
 for n in raws:
  owners={f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']};need(owners<=set(raws),'No outside raw owner')
 nc=a.c;slack={}
 for pb,q in changes.items():
  try:nc,slack[pb]=repack_parts(nc,pb,q)
  except ValueError:nc,slack[pb],_=global_parts(nc,pb,q)
 ng,gfx=repack_fixed_global(a,raws,counts);need(bank_offsets(a.c)==bank_offsets(nc),'Composition boundaries');need(ng[:56]==a.g[:56]and ng[a.banks[0]['end']:]==a.g[a.banks[0]['end']:],'Other graphics banks')
 result=replace_entry(replace_entry(data,2,ng),3,nc);b=Archive(result);raw_checked=nonraw=layers=nonlayers=part_records=rgba=gpu=0;unreconstructed=[]
 for gb,bank in enumerate(a.banks):
  need((bank['base'],bank['end'],len(bank['frames']))==(b.banks[gb]['base'],b.banks[gb]['end'],len(b.banks[gb]['frames'])),'Graphics boundaries')
  for f in bank['frames']:
   n=f['index'];changed=gb==0 and n in raws;need(raw(b,gb,n)==(raws[n]if changed else raw(a,gb,n)),'Decoded raw exact');need(b.banks[gb]['frames'][n]['tile_count']==(counts[n]if changed else f['tile_count']),'Tile count');raw_checked+=1;nonraw+=not changed
 for n in range(237):
  for pb in PBS:
   try:oldlayer=a.layer(n,pb)[0]
   except(ValueError,IndexError)as e:
    need(n not in raws,'Selected invalid layer')
    try:b.layer(n,pb)
    except(ValueError,IndexError)as e2:need(type(e)==type(e2)and str(e)==str(e2),'Unreconstructed preserved');unreconstructed.append([n,pb,str(e)]);continue
    raise ValueError('Unexpected valid layer')
   need(np.array_equal(b.layer(n,pb)[0],targets[n,pb]if n in REFS else oldlayer),f'Layer{n}/{pb}');layers+=1;nonlayers+=n not in REFS
  if n not in raws:continue
  for mask in range(16):
   for arm in(1,2):
    want=comp(a,{pb:targets[n,pb]for pb in PBS},mask,arm)if n in REFS else a.composite(n,mask,arm)[0]
    need(b.composite(n,mask,arm)[0].tobytes()==want.tobytes(),f'RGBA{n}/{mask}/{arm}');rgba+=1
  atlas=np.frombuffer(indexed_atlas(raws[n],32)[0],np.uint8).reshape(32,256)
  for pb in PBS:
   for p in composition_frame(b.c,pb,n)['parts']:
    t=p['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16];need(t<32,'GPU tile');need(t%16!=0 or not tile[:,0].any(),'GPU U edge');need(not p['flip_y']or t//16!=0 or not tile[0].any(),'GPU V edge');gpu+=1
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   need(records(b.c,pb,n)==(changes[pb][n]if pb in PBS and n in raws else records(a.c,pb,n)),f'Record{pb}/{n}');part_records+=1
 need(a.p==b.p,'Palette')
 for e in psx_arc(data):
  if int(e['type'],16)in(2,3):continue
  span=slice(e['offset'],e['offset']+e['size']);need(data[span]==result[span],'Other ARC entry')
 for key in REFS[::2]:need(b.banks[0]['frames'][key]['offset']==b.banks[0]['frames'][key+1]['offset'],'Shot shared pair')
 return result,{'passed':True,'parent_sha256':PARENT,'after':sha(result),'refs':list(REFS),'storage_only_refs':selected,'storage_proofs':storage_proofs,'target_sources':sources,'target_groups':groups,'raw_checked':raw_checked,'nonselected_raw_exact':nonraw,'storage_inverse_exact':len(selected),'layers_checked':layers,'target_layers_exact':50,'nonart_layers_exact':nonlayers,'composition_records_checked':part_records,'partial_RGBA_checked':rgba,'GPU_parts_checked':gpu,'composition_slack':slack,'graphics':gfx,'unreconstructed_layers_preserved':unreconstructed,'pixels_reduced':False,'bank_boundaries_changed':False,'native_cpu_pending':True,'independent_pending':True,'runtime_verified':False,'frozen':False}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--output',default='packed_hover_candidate03');a=ap.parse_args();out=D/a.output;need(not out.exists()and out.resolve().is_relative_to(D.resolve()),'Fresh owned output')
 result,report=build(a.parent.read_bytes());out.mkdir();(out/'PL00_U.ARC').write_bytes(result);(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');b=Archive(result)
 for n in REFS:helper.grid([(str(n),[('idle basic',b.composite(0,8)[0]),('new basic',b.composite(n,8)[0]),('idle Fourth',b.composite(0,15)[0]),('new Fourth',b.composite(n,15)[0])])],out/f'readback_{n}.png',5)
 print(json.dumps({k:report[k]for k in('after','raw_checked','nonselected_raw_exact','layers_checked','partial_RGBA_checked','GPU_parts_checked','graphics')}))
if __name__=='__main__':main()
