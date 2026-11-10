"""새 머리3개를 패킹하며 원 노바 효과는 독립 층 전체 픽셀로 보존한다."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw,PLACEHOLDERS
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable
from repack_identical import repack_identical
from pack_single_safe import pack_single_safe
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,bank_offsets,indexed_atlas
from scripts.discover_inputs import psx_arc
PARENT='f02cf1d60ac27fc46b48d9b575b29360eb9eb965a7ffc2fcdb7123b02b931449';REFS=(217,218,220);PBS=(0,5,6,7,8)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--parent',default='packed_dash_diagnostic_v2/PL02_U.ARC');parser.add_argument('--out',default='packed_dash_nova_diagnostic_v3');args=parser.parse_args();src=(D/args.parent).resolve();out=(D/args.out).resolve();need(src.is_relative_to(D.resolve())and out.is_relative_to(D.resolve())and not out.exists(),'Fresh isolated paths');need(digest(src)==PARENT,'Parent');a=Archive(src.read_bytes());out.mkdir();targetdir=D/'nova_head_registered_v1';meta=json.loads((targetdir/'registration.json').read_text('utf8'));repls={};counts={};changes={pb:{}for pb in PBS};targets={};groups=[]
 for n in REFS:
  t=np.array(Image.open(targetdir/f'target_{n:03}.png'));need(sha(t.tobytes())==next(q['target_index_sha256']for q in meta['frames']if q['ref']==n),'Head target');targets[n,0]=t;oldraw=raw(a,0,n);keep={p['tile']for pb in PBS[1:]for p in composition_frame(a.c,pb,n)['parts']};pool=set(range(32))-keep-{0,16}
  try:
   nr,assign=pack_shared(oldraw,32,[t[80:240,80:240]],pool,[16]);pbs=(0,);mode='base_only_old_effect_raw_exact'
  except ValueError as e:
   print(json.dumps({'ref':n,'base_pool':len(pool),'base_only_failed':str(e)}),flush=True);pbs=(0,);nr,assign=pack_single_safe(oldraw,32,t[80:240,80:240],set(range(32))-keep,16);mode='base_only_page_edge_padded_effect_raw_exact'
  for pb,parts in zip(pbs,assign):changes[pb][n]=b''.join(struct.pack('<BBbb',flag,ti,x-80,y-80)for ti,x,y,flag in parts)
  repls[n]=nr;counts[n]=32;groups.append({'ref':n,'mode':mode,'parts':{str(pb):len(parts)for pb,parts in zip(pbs,assign)},'old_effect_tiles':sorted(keep),'old_effect_raw_exact':all(np.frombuffer(indexed_atlas(oldraw,32)[0],np.uint8).reshape(32,256)[ti//16*16:ti//16*16+16,ti%16*16:ti%16*16+16].tobytes()==np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256)[ti//16*16:ti//16*16+16,ti%16*16:ti%16*16+16].tobytes()for ti in keep)});print(json.dumps(groups[-1]),flush=True)
 nc=a.c;slack={}
 for pb,rep in changes.items():
  if rep:nc,slack[pb]=repack_parts(nc,pb,rep)
 ng,packing=repack_identical(a.g,repls,counts);result=replace_entry(replace_entry(a.data,2,ng),3,nc);b=Archive(result);rawchecks=nonraw=0
 for gb,bank in enumerate(a.banks):
  need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Bank boundary')
  for n in range(len(bank['frames'])):
   expected=repls[n]if gb==0 and n in repls else raw(a,gb,n);need(raw(b,gb,n)==expected,f'Raw {gb}/{n}');rawchecks+=1;nonraw+=not(gb==0 and n in repls)
 layers=nonlayers=0
 for n in range(237):
  if n in PLACEHOLDERS:continue
  for pb in PBS:
   expected=targets.get((n,pb),a.layer(n,pb)[0]);need(np.array_equal(b.layer(n,pb)[0],expected),f'Layer {n}/{pb}');layers+=1;nonlayers+=(n,pb)not in targets
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   if n in changes.get(pb,{}):continue
   need(records(a.c,pb,n)==records(b.c,pb,n),f'Original composition {n}/{pb}')
 gpu=0
 for n in REFS:
  ar=np.frombuffer(indexed_atlas(raw(b,0,n),32)[0],np.uint8).reshape(32,256)
  for pb in PBS:
   for p in composition_frame(b.c,pb,n)['parts']:
    ti=p['tile'];tile=ar[ti//16*16:ti//16*16+16,ti%16*16:ti%16*16+16]
    if ti%16==0:need(not tile[:,0].any(),'GPU first-column')
    if p['flip_y']and ti//16==0:need(not tile[0].any(),'GPU flipY row')
    gpu+=1
 before=bytearray(a.data);after=bytearray(result)
 for e in psx_arc(a.data):
  if int(e['type'],16)in(2,3):before[e['offset']:e['offset']+e['size']]=after[e['offset']:e['offset']+e['size']]
 need(before==after,'Other entries/palette/audio');(out/'PL02_U.ARC').write_bytes(result)
 helper.grid([(f'Nova {n}',[('old after body',a.composite(n,15)[0]),('new head native',b.composite(n,15)[0])])for n in(217,218,219,220)],out/'nova_readback.png',6)
 write(out/'verification.json',{'passed':True,'before':PARENT,'after':sha(result),'changed_head_refs':list(REFS),'raw_checks':rawchecks,'nonselected_raw_exact':nonraw,'layers_checked':layers,'nonselected_layers_exact':nonlayers,'original_effect_layer_pixels_exact':True,'palette_audio_other_entries_exact':True,'gpu_parts':gpu,'packing':packing,'composition_slack':slack,'groups':groups,'native_mips_pending':True,'runtime_verified':False});print(json.dumps({'after':sha(result),'out':str(out),'slack':packing['remaining_slack']}))
if __name__=='__main__':main()
