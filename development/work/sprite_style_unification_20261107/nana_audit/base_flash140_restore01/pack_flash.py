"""140만 현재idle의부분추가알파를13빛색으로연동.10타일·원46FX·다른참조보존."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(W/'shibuki_audit')]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw,PLACEHOLDERS
from src.psx_player import indexed_atlas,composition_frame,bank_offsets
from scripts.prepare_shibuki_ultimate_production import records,repack_parts
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import replace_entry
from scripts.discover_inputs import psx_arc
PBS=(0,5,6,7,8);P=N/'base_nova_repaint/packed_nova_candidate_v1/PL00_U.ARC';BEFORE='94cf560530c87ac11a03c029a9b6e98be44c06ea6d30d6c5ce66204c8a8e3cb3';FROZEN='5c4d4b84c531b1dc5fba89f37557048ec5245a569471bc0ea82379178cb13d5e'
def compose(a,ls,mask,arm=2):
 im=a.rgba(ls[0])
 for pb,bit in((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def build(parent,all_rgba=True):
 need(sha(parent)==BEFORE and digest(P.with_name('FROZEN.json'))==FROZEN,'동결부모');a=Archive(parent);base=a.layer(140)[0];idle=a.layer(0)[0];fx=(base>0)&(idle==0)
 need(np.all(base[base>0]==13)and int(fx.sum())==46 and np.all(base[idle>0]==13),'기본실루엣/46원효과');need(a.words[13]==a.words[29]==a.words[45],'빛색동일')
 target={0:base.copy(),**{pb:np.where((a.layer(0,pb)[0]>0)&(idle==0),13,0).astype(np.uint8)for pb in PBS[1:]}};need([int((target[pb]>0).sum())for pb in PBS[1:]]==[72,3,1,73],'추가149셀')
 frame=a.banks[0]['frames'][140];need(frame['tile_count']==10 and[q['index']for q in a.banks[0]['frames']if q['offset']==frame['offset']]==[140],'독립10타일');old=raw(a,0,140);oldat=np.frombuffer(indexed_atlas(old,10)[0],np.uint8).reshape(-1,256);out=bytearray(old);_,locations,_=indexed_atlas(old,10)
 def get(t):return oldat[t//16*16:t//16*16+16,t%16*16:t%16*16+16].copy()
 def put(t,z):
  need(z.shape==(16,16)and z.max()<16,'tile형식')
  for y in range(16):
   for x in range(16):pos,sh=locations[(t//16*16+y)*256+t%16*16+x];out[pos]=(out[pos]&~(15<<sh))|(int(z[y,x])<<sh)
 # 조립공유를in-place수정하지않는다.140의새기록만기존tile1->미소비6을참조한다.
 used={q['tile']for q in composition_frame(a.c,0,140)['parts']};need(used=={1,2,3,4,5,8},'기본소비타일');put(6,get(1));head_record=bytes.fromhex('0001fce9');need(any(head_record in records(a.c,5,n)for n in range(237)),'기존head기록');_,ht,hx,hy=struct.unpack('<BBbb',head_record);head=target[5][hy+160:hy+176,hx+160:hx+176];need(np.count_nonzero(head)==72,'head범위');put(ht,head)
 point=np.zeros((16,16),np.uint8);point[0,1]=13;put(0,point);changes={pb:{}for pb in PBS};changes[0][140]=b''.join(struct.pack('<BBbb',q['flags'],6 if q['tile']==1 else q['tile'],q['x'],q['y'])for q in composition_frame(a.c,0,140)['parts']);changes[5][140]=head_record
 for pb in(6,7):changes[pb][140]=b''.join(struct.pack('<BBbb',0,0,int(x-161),int(y-160))for y,x in np.argwhere(target[pb]>0))
 remain=target[8].copy();leg_records=[]
 for t,x,y in((7,-2,-2),(9,0,-15)):
  z=remain[y+160:y+176,x+160:x+176].copy();remain[y+160:y+176,x+160:x+176]=0;put(t,z);leg_records.append(struct.pack('<BBbb',0,t,x,y))
 need(int((remain>0).sum())==1 and remain[169,157]==13,'leg잔여한점');leg_records += [struct.pack('<BBbb',0,0,int(x-161),int(y-160))for y,x in np.argwhere(remain>0)];changes[8][140]=b''.join(leg_records)
 nr=bytes(out);at=np.frombuffer(indexed_atlas(nr,10)[0],np.uint8).reshape(-1,256);need(np.array_equal(at[:,128:144],oldat[:,128:144]),'원FXtile8전체');need(np.array_equal(at[:,96:112],get(1)),'bodytile1->6전체');need(not at[:,0].any(),'tile0 U경계')
 nc=a.c;slack={}
 for pb in PBS:nc,slack[pb]=repack_parts(nc,pb,changes[pb])
 ng,packing=repack_variable(a.g,{140:nr},{140:10});result=replace_entry(replace_entry(parent,2,ng),3,nc);b=Archive(result);need(bank_offsets(a.c)==bank_offsets(b.c),'조립은행경계');rc=nonraw=layers=nonlayers=parts=rgba=targetrgba=gpu=0
 for gb,bank in enumerate(a.banks):
  need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'그래픽은행경계')
  for q in bank['frames']:
   n=q['index'];changed=gb==0 and n==140;need(raw(b,gb,n)==(nr if changed else raw(a,gb,n)),f'raw{gb}/{n}');need(b.banks[gb]['frames'][n]['tile_count']==q['tile_count'],'원타일수');rc+=1;nonraw+=not changed
 for n in range(237):
  if n in PLACEHOLDERS:continue
  for pb in PBS:need(np.array_equal(b.layer(n,pb)[0],target[pb]if n==140 else a.layer(n,pb)[0]),f'층{n}/{pb}');layers+=1;nonlayers+=n!=140
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   if pb in PBS and n==140:continue
   need(records(a.c,pb,n)==records(b.c,pb,n),f'비대상조립{pb}/{n}');parts+=1
 for n in(range(237)if all_rgba else(140,)):
  if n in PLACEHOLDERS:continue
  for mask in range(16):
   for arm in(1,2):
    expected=compose(a,target,mask,arm)if n==140 else a.composite(n,mask,arm)[0];actual=b.composite(n,mask,arm)[0];need(actual.tobytes()==expected.tobytes(),f'RGBA{n}/{mask}/{arm}');rgba+=1;targetrgba+=n==140
    if n==140:
     silhouette=np.where((np.array(a.composite(0,mask,arm)[0])[:,:,3]>0)|fx,13,0).astype(np.uint8);need(actual.tobytes()==a.rgba(silhouette).tobytes(),'실제idle부분알파+46exact')
 for pb in PBS:
  for q in composition_frame(b.c,pb,140)['parts']:
   t=q['tile'];tile=at[t//16*16:t//16*16+16,t%16*16:t%16*16+16];need(t<10,'GPU tile정원')
   if t%16==0:need(not tile[:,0].any(),'GPU U')
   if q['flip_y']and t<16 and tile[0].any():need((q['flags'],t,q['x'],q['y'])in[(z['flags'],z['tile'],z['x'],z['y'])for z in composition_frame(a.c,pb,140)['parts']]and np.array_equal(tile,get(t)),'기존FX경계보존')
   gpu+=1
 need(a.p==b.p,'팔레트');entries=[]
 for e in psx_arc(parent):
  if int(e['type'],16)in(2,3):continue
  s=slice(e['offset'],e['offset']+e['size']);need(parent[s]==result[s],'외부항목');entries.append(e['type'])
 return result,target,{'passed':True,'parent_arc':P.relative_to(ROOT).as_posix(),'before':BEFORE,'after':sha(result),'refs':[140],'extra_alpha_by_layer':{'5':72,'6':3,'7':1,'8':73},'base140_RGBA_unchanged':True,'effect46_world_exact':True,'effect_tile8_all256_indices_exact':True,'original_tile_count':10,'raw_single_owner':[140],'raw_checked':rc,'nonselected_raw_exact':nonraw,'target_layers_exact':5,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':parts,'RGBA_checked':rgba,'target_partial_RGBA':targetrgba,'GPU_parts':gpu,'original_base_records_only_tile1_to6':True,'new_armor_parts':{str(pb):len(changes[pb][140])//4 for pb in PBS[1:]},'new_point_tile0_first_column_zero':True,'head_template_record':head_record.hex(),'leg_rectangles':[[7,-2,-2],[9,0,-15]],'leg_remainder_point':[-3,9],'composition_slack':slack,'packing':packing,'protected_entries':entries,'all_208_212_raw_records_layers_exact':True,'native_CPU_pending':True,'runtime_verified':False,'frozen':False}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='packed_flash_candidate_v1');ap.add_argument('--quick',action='store_true');args=ap.parse_args();out=(D/args.out).resolve();need(out.is_relative_to(D)and not out.exists(),'새소유출력');result,target,r=build(P.read_bytes(),not args.quick);out.mkdir();(out/'PL00_U.ARC').write_bytes(result);write(out/'verification.json',r)
 for pb,z in target.items():Image.fromarray(z).save(out/f'layer{pb}_140.png')
 a=Archive(P.read_bytes());b=Archive(result);helper.grid([('140',[('base idle',a.composite(0)[0]),('base unchanged',b.composite(140)[0]),('Fourth idle',a.composite(0,15)[0]),('old shared flash',a.composite(140,15)[0]),('new Fourth flash',b.composite(140,15)[0])])],out/'readback.png',6)
 helper.grid([(f'mask{m}',[('current idle',a.composite(0,m)[0]),('new flash',b.composite(140,m)[0])])for m in(1,2,4,8,10,15)],out/'partial.png',5);print(json.dumps({'after':r['after'],'parts':r['new_armor_parts'],'slack':r['composition_slack'],'raw':r['raw_checked'],'rgba':r['RGBA_checked']}))
if __name__=='__main__':main()
