"""95/96/97의 새15층을 고정은행에 시험 패킹하며 비대상 전체를 대조한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from scripts.export_x_consistency import Archive,page
from scripts.overhaul_sprites_costume_pack import pack_planes
from scripts.prepare_shibuki_ultimate_production import records,repack_parts
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,composition_frame,indexed_atlas
from pack_shibuki_hurt import raw,repack_fixed_global
from repack_part_records_lossless import repack as repack_global
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose
PBS=(0,5,6,7,8);REFS=(95,96,97);PARENT='87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b'
def build(data,log):
 need(sha(data)==PARENT,'Wrong parent');a=Archive(data);s=H/'standing_special_layers01';targets={n:{b:np.array(Image.open(s/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in(95,97)};targets[96]={b:np.roll(v,1,axis=1)for b,v in targets[95].items()};changes={b:{}for b in PBS};raws={};counts={};groups=[];gpu=0
 for ns in((95,96),(97,)):
  n=ns[0];need(all(set(f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][k]['offset'])<=set(REFS)for k in ns),'Non-target raw alias');nr,rr=pack_planes(bytes(4096),32,[crop(targets[n][b])for b in PBS],set(range(32))-{0,16},[24]*5);atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256)
  for k in ns:
   raws[k]=nr;counts[k]=32
   for b,ps in zip(PBS,rr):
    record=b''.join(struct.pack('<BBbb',fl,t,x-80+(k-n),y-80)for t,x,y,fl in ps)or struct.pack('<BBbb',0,0,-8,-8);need(len(record)<=96,'Part limit');changes[b][k]=record
    for fl,t,x,y in struct.iter_unpack('<BBbb',record):
     tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
     if t%16==0:need(not tile[:,0].any(),'GPU U boundary')
     if fl&128 and t//16==0:need(not tile[0].any(),'GPU V boundary')
     gpu+=1
  groups.append({'refs':list(ns),'raw_sha256':sha(nr),'parts':{str(k):{str(b):len(changes[b][k])//4 for b in PBS}for k in ns}});log(groups[-1])
 nc=a.c;slack={};methods={}
 for b,r in changes.items():
  try:nc,slack[b]=repack_parts(nc,b,r);methods[b]='existing'
  except ValueError:nc,slack[b],methods[b]=repack_global(nc,b,r)
 log({'parts_slack':slack});ng,gr=repack_fixed_global(a,raws,counts);out=replace_entry(replace_entry(data,2,ng),3,nc);z=Archive(out);need(bank_offsets(z.c)==bank_offsets(a.c),'Parts boundaries');allraw=nonraw=0
 for gb,bank in enumerate(a.banks):
  nb=z.banks[gb];need((bank['base'],bank['end'],len(bank['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Graphics boundaries')
  for f in bank['frames']:
   n=f['index'];need(raw(z,gb,n)==(raws[n]if gb==0 and n in raws else raw(a,gb,n)),'Raw mismatch');allraw+=1;nonraw+=not(gb==0 and n in raws)
 layers=nonlayers=partials=parts=0
 for n in range(237):
  if n in(105,*range(175,183)):continue
  for b in PBS:need(np.array_equal(z.layer(n,b)[0],targets[n][b]if n in targets else a.layer(n,b)[0]),f'Layer mismatch {n}/{b}');layers+=1;nonlayers+=n not in targets
  if n in targets:
   for arm in(1,2):
    for mask in range(16):need(z.composite(n,mask,arm)[0].tobytes()==compose(a,targets[n],mask,arm).tobytes(),'RGBA mismatch');partials+=1
 for b in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
   if b in PBS and n in REFS:continue
   need(records(a.c,b,n)==records(z.c,b,n),'Other records');parts+=1
 return out,{'passed':True,'parent_sha256':PARENT,'candidate_sha256':sha(out),'target_refs':list(REFS),'target_layers':15,'allraw':allraw,'non_target_raw':nonraw,'layers':layers,'non_target_layers':nonlayers,'other_records':parts,'partial_RGBA':partials,'gpu_parts':gpu,'groups':groups,'part_slack':slack,'part_methods':methods,'graphics':gr,'protected_entries':protected_entries(data,out),'source_inputs':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p.read_bytes())for p in sorted(s.iterdir())if p.is_file()},'all_boundaries_preserved':True,'native96_equals95_x_plus1':True,'native_cpu_pending':True,'root_final_art_pending':True,'independent_pending':True,'frozen':False,'gameplay_verified':False}
def main():
 o=H/'standing_special_pack01';need(not o.exists(),'Fresh probe');o.mkdir();progress=[]
 def log(v):progress.append(v);write(o/'progress.json',progress);print(json.dumps(v),flush=True)
 try:out,r=build((H/'prepared_hurt_base01/PL00_U.ARC').read_bytes(),log)
 except Exception as e:write(o/'report.json',{'passed':False,'error':str(e),'arc_written':False,'progress':progress});raise
 (o/'PL00_U.ARC').write_bytes(out);a=Archive(out)
 for f,mask in(('base',0),('fourth',15)):page([(f'{n} actual {f}',a.composite(n,mask)[0])for n in REFS],a.composite(0,mask)[0],o/f'{f}_readback.png',cols=2,scale=5)
 for n in(95,97):page([(f'{n} mask{m:X}',a.composite(n,m)[0])for m in range(16)],a.composite(0,15)[0],o/f'partial_{n:03}.png',cols=4,scale=4)
 write(o/'report.json',r);print(json.dumps({'candidate':sha(out),'report':sha((o/'report.json').read_bytes()),'graphics':r['graphics']}),flush=True)
if __name__=='__main__':main()
