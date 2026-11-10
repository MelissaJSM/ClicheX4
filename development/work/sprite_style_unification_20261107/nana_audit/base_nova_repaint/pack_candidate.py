"""PL00 노바 새30층: 원공유그룹/은행/비대상 보존 패킹과 실제 재독출."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(W/'shibuki_audit'),str(D)]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw,PLACEHOLDERS
from prepare_common import comp
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable,pack_planes
from repack_part_records_lossless import repack as lossless_parts
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,bank_offsets,indexed_atlas
from scripts.discover_inputs import psx_arc
PBS=(0,5,6,7,8);REFS=(213,214,215,216,217,220)
PARENT=W/'root_nana_hover/packed_hover_final01/PL00_U.ARC'
BEFORE='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c'
def pack_with_head(ns,images,origin,limits):
 choices=json.loads((D/'head_templates_probe_v2/choices.json').read_text('utf8'));failure=None
 for choice in sorted(choices[str(ns[0])],key=lambda q:(len(q['records']),q['source_ref'])):
  geom=choice['records'];out=bytearray(4096);_,loc,_=indexed_atlas(bytes(out),32);used=set();reserved={r[1]for r in geom};patches={};assign=[[]for _ in images]
  try:
   for j,n in enumerate(ns):
    rem=images[j*5+1].copy()
    for fl,original,wx,wy in geom:
     x,y=wx+origin,wy+origin;z=rem[y:y+16,x:x+16].copy();rem[y:y+16,x:x+16]=0;t=original
     if t in used and not np.array_equal(patches[t],z):t=next(t for t in range(1,32)if t!=16 and t not in(used|reserved))
     if t not in used:
      for yy,xx in np.argwhere(z):pos,sh=loc[(t//16*16+int(yy))*256+t%16*16+int(xx)];out[pos]|=int(z[yy,xx])<<sh
      patches[t]=z.copy();used.add(t)
     assign[j*5+1].append((t,x,y,0))
    need(not rem.any(),'기존 head geometry 범위')
   order=[i for i,z in enumerate(images)if i%5!=1 and z.any()]
   nr,rr=pack_planes(bytes(out),32,[images[i]for i in order],set(range(32))-used,[limits[i]for i in order])
   for i,r in zip(order,rr):assign[i]=r
   return nr,assign,choice
  except (ValueError,StopIteration)as e:failure=e
 raise ValueError('Pinned head 대안 실패: '+str(failure))
def targets():
 result={};sources=[]
 for n in REFS:
  folder=D/('preparation_effect_probe_v2'if n<217 else'dash_layers_probe_v1')
  for pb in PBS:
   f=folder/f'layer{pb}_{n}.png';z=np.array(Image.open(f));need(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16,'층형식');result[n,pb]=z
   sources.append({'ref':n,'bank':pb,'path':f.relative_to(ROOT).as_posix(),'file_sha256':digest(f),'indices_sha256':sha(z.tobytes())})
 return result,sources
def build(out,all_rgba):
 need(digest(PARENT)==BEFORE,'동결부모');parent=PARENT.read_bytes();a=Archive(parent);target,sources=targets();groups={}
 for n in REFS:groups.setdefault(a.banks[0]['frames'][n]['offset'],[]).append(n)
 replacements={};counts={};changes={pb:{}for pb in PBS};packed=[];gpu=0
 for off,ns in groups.items():
  f=a.banks[0]['frames'][ns[0]];need(set(ns)=={q['index']for q in a.banks[0]['frames']if q['offset']==off},'비대상 stream소유자');old_count=f['tile_count'];count=32
  crop=64 if 220 in ns else 80;origin=160-crop
  images=[target[n,pb][crop:320-crop,crop:320-crop]for n in ns for pb in PBS]
  active=[i for i,z in enumerate(images)if z.any()];limits=[max(16,len(composition_frame(a.c,pb,n)['parts']))for n in ns for pb in PBS]
  nr,assign,head_choice=pack_with_head(ns,images,origin,limits)
  atlas=np.frombuffer(indexed_atlas(nr,count)[0],np.uint8).reshape(-1,256);need(not atlas[:,0].any(),'GPU U경계')
  for j,n in enumerate(ns):
   replacements[n]=nr;counts[n]=count
   for pb,r in zip(PBS,assign[j*5:j*5+5]):
    changes[pb][n]=b''.join(struct.pack('<BBbb',flag,t,x-origin,y-origin)for t,x,y,flag in r)
    for t,x,y,flag in r:
     if t%16==0:need(not atlas[t//16*16:t//16*16+16,0].any(),'GPU U경계 tile')
     if flag&128 and t<16:need(not atlas[0,t*16:t*16+16].any(),'GPU V경계')
     gpu+=1
  row={'refs':ns,'old_tile_count':old_count,'tile_count':count,'raw_sha256':sha(nr),'head_template':head_choice,'parts':{str(n):{str(pb):len(assign[j*5+k])for k,pb in enumerate(PBS)}for j,n in enumerate(ns)}};packed.append(row);print(json.dumps(row),flush=True)
 nc=a.c;slack={};methods={}
 for pb in PBS:
  try:nc,slack[pb]=repack_parts(nc,pb,changes[pb]);methods[pb]='existing_exact_sequences'
  except ValueError:nc,slack[pb],methods[pb]=lossless_parts(nc,pb,changes[pb])
 ng,packing=repack_variable(a.g,replacements,counts);result=replace_entry(replace_entry(parent,2,ng),3,nc);b=Archive(result)
 need(bank_offsets(a.c)==bank_offsets(b.c),'조립은행경계');rc=nonraw=layers=nonlayers=parts=rgba=trgba=0
 for gb,bank in enumerate(a.banks):
  need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'그래픽은행경계')
  for q in bank['frames']:
   n=q['index'];new=gb==0 and n in REFS;need(raw(b,gb,n)==(replacements[n]if new else raw(a,gb,n)),f'raw{gb}/{n}');need(b.banks[gb]['frames'][n]['tile_count']==(counts[n]if new else q['tile_count']),'타일수');rc+=1;nonraw+=not new
 for n in range(237):
  if n in PLACEHOLDERS:continue
  for pb in PBS:
   need(np.array_equal(b.layer(n,pb)[0],target[n,pb]if n in REFS else a.layer(n,pb)[0]),f'층{n}/{pb}');layers+=1;nonlayers+=n not in REFS
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   if pb in PBS and n in REFS:continue
   need(records(a.c,pb,n)==records(b.c,pb,n),f'조립{pb}/{n}');parts+=1
 need(a.p==b.p,'팔레트')
 for e in psx_arc(parent):
  if int(e['type'],16)in(2,3):continue
  s=slice(e['offset'],e['offset']+e['size']);need(parent[s]==result[s],'다른항목')
 for n in(range(237)if all_rgba else REFS):
  if n in PLACEHOLDERS:continue
  for mask in range(16):
   for arm in(1,2):
    expected=comp(a,{pb:target[n,pb]for pb in PBS},mask,arm)if n in REFS else a.composite(n,mask,arm)[0]
    need(expected.tobytes()==b.composite(n,mask,arm)[0].tobytes(),f'RGBA{n}/{mask}/{arm}');rgba+=1;trgba+=n in REFS
 for ns in groups.values():need(len({b.banks[0]['frames'][n]['offset']for n in ns})==1,'원공유그룹')
 report={'passed':True,'parent_arc':PARENT.relative_to(ROOT).as_posix(),'before':BEFORE,'after':sha(result),'targets':sources,'refs':REFS,'packing':packing,'composition_slack':slack,'composition_methods':methods,'groups':packed,'raw_checked':rc,'nonselected_raw_exact':nonraw,'layers_checked':layers,'target_layers_exact':30,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':parts,'rgba_combinations':rgba,'target_rgba_combinations':trgba,'gpu_parts_safe':gpu,'frozen':False,'runtime_verified':False,'scope':'새213/215/217 세몸체×양의상6원화와214원외부124효과·216별칭·220몸+1효과파생.218/219완전보존.대상32타일/4096B내부수납,은행경계·비대상·원팔레트·EXE불변.'}
 write(out/'verification.json',report);(out/'PL00_U.ARC').write_bytes(result)
 for i in range(0,len(REFS),2):helper.grid([(str(n),[('base idle',b.composite(0)[0]),('old base',a.composite(n)[0]),('new base',b.composite(n)[0]),('old Fourth',a.composite(n,15)[0]),('new Fourth',b.composite(n,15)[0])])for n in REFS[i:i+2]],out/f'readback_{i//2+1}.png',5 if i<4 else 3)
 return report
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='packed_nova_probe_v1');ap.add_argument('--quick',action='store_true');args=ap.parse_args();out=(D/args.out).resolve();need(out.is_relative_to(D)and not out.exists(),'신규소유경로');out.mkdir()
 try:r=build(out,not args.quick)
 except Exception as e:write(out/'failure.json',{'error':str(e),'type':type(e).__name__});raise
 print(json.dumps({'after':r['after'],'slack':r['composition_slack'],'rgba':r['rgba_combinations']}))
if __name__=='__main__':main()
