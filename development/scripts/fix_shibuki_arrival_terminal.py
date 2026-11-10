"""수용된 기본형의 idle+12잔광 규칙을 다른 시부키 폼의 등장141에 적용."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,TASK,SOURCES,sha,write,need,relative,FONT,read
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,decode_stream,indexed_atlas,bank_offsets
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank

D=TASK/'arrival141_history/prepared_v1'
INPUT_SHAS={'PL00_U.ARC':'075b03a71b6ce9df91e5db2de44f7e715c51c60b681284e7df24df6a225e50aa','PL02_U.ARC':'3228c2b8d1a339cac2256f2ba5229f5ece6a9de4e22608b31fbe14988be1323a'}

def patch_terminal(data,name,*,expected_input_sha):
 need(name in('PL00_U.ARC','PL02_U.ARC') and sha(data)==expected_input_sha,'지원하지 않는141 입력')
 before=Archive(data);g,c=before.g,before.c;bank=before.banks[0];f=bank['frames'][141];z=bank['frames'][0]
 need([p['index'] for p in bank['frames'] if p['offset']==f['offset']]==[141],'141압축 공유')
 raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;zero=decode_stream(g,z['offset'],z['limit'],z['tile_count']*128).data
 old_atlas,locations,_=indexed_atlas(raw,f['tile_count']);old_atlas=np.frombuffer(old_atlas,np.uint8).reshape(-1,256)
 za=np.frombuffer(indexed_atlas(zero,z['tile_count'])[0],np.uint8).reshape(-1,256)
 def tile(a,t):return a[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
 def write_tiles(values,initial):
  result=bytearray(initial)
  for t,im in values.items():
   for y in range(16):
    for x in range(16):
     at,shift=locations[(t//16*16+y)*256+t%16*16+x];result[at]=(result[at]&~(15<<shift))|(int(im[y,x])<<shift)
  return bytes(result)
 base141,_=before.layer(141);yy,xx=np.indices(base141.shape);fx=np.where((xx<160-18)|(xx>160+18),base141,0).astype(np.uint8)
 need(np.count_nonzero(fx)==12,'141의 외곽잔광이12픽셀이아님')
 cps={b:composition_frame(c,b,141) for b in(0,5,6,7,8)};src={b:composition_frame(c,b,0) for b in cps};newparts={};nr=raw
 if name=='PL00_U.ARC':
  source_tiles={p['tile'] for b in(5,6,7,8) for p in src[b]['parts']};base_tiles={p['tile'] for p in cps[0]['parts']};free=sorted(set(range(f['tile_count']))-base_tiles,key=lambda t:(t%16==0,t));need(len(free)>=len(source_tiles),'141아머 타일부족')
  mapping={s:t for s,t in zip(sorted(source_tiles),free)};nr=write_tiles({t:tile(za,s) for s,t in mapping.items()},raw)
  for b in(5,6,7,8):newparts[b]=[{**p,'tile':mapping[p['tile']]} for p in src[b]['parts']]
  na=np.frombuffer(indexed_atlas(nr,f['tile_count'])[0],np.uint8).reshape(-1,256)
  need(all(np.array_equal(tile(na,t),tile(old_atlas,t)) for t in base_tiles),'기본141 raw타일 변경')
 else:
  need(f['tile_count']==17 and z['tile_count']==15,'현재141/idle타일수 변경')
  values={t:tile(za,t) for t in range(z['tile_count'])};fxparts=[]
  for t,x,y in((15,-34,-10),(16,19,-8)):
   pix=fx[y+160:y+176,x+160:x+176].copy();values[t]=pix;fxparts.append({'flags':0,'tile':t,'x':x,'y':y})
  nr=write_tiles(values,bytes(len(raw)));newparts={b:[dict(p) for p in src[b]['parts']] for b in src};newparts[0]+=fxparts
 nc=bytearray(c);changed=set()
 if name=='PL02_U.ARC':
  # Several old141 armor records also belong to138 and unrelated blank layers.
  # The new raw reuses idle0 tile IDs, so alias only141's headers toidle0.
  offsets=bank_offsets(c)
  for b in(5,6,7,8):
   start=offsets[b];at=start+141*4;nc[at:at+4]=c[start:start+4];changed.update(range(at,at+4));del newparts[b]
 for b,parts in newparts.items():
  old=cps[b]['parts'];need(0<len(parts)<=len(old),f'141 조립칸 부족 bank{b}')
  slots={p['record_offset'] for p in old}
  for n in range(237):
   if n!=141:need(not slots&{p['record_offset'] for p in composition_frame(c,b,n)['parts']},'다른ref 조립공유')
  for i,op in enumerate(old):
   p=parts[min(i,len(parts)-1)];at=op['record_offset'];nc[at:at+4]=struct.pack('<BBbb',p['flags'],p['tile'],p['x'],p['y']);changed.update(range(at,at+4))
 nc=bytes(nc);need(all(a==b or i in changed for i,(a,b) in enumerate(zip(c,nc))),'비대상조립 변경')
 if name=='PL00_U.ARC':need(all(c[p['record_offset']:p['record_offset']+4]==nc[p['record_offset']:p['record_offset']+4] for p in cps[0]['parts']),'기본141 조립바이트 변경')
 code=encode_stream(nr)
 if len(code)<=f['limit']-f['offset']:ng,packing=replace_stream(g,f,nr,allocated_limit=f['limit'])
 else:ng,packing=repack_graphics_bank(g,0,{141:code})
 result=replace_entry(replace_entry(data,2,ng),3,nc);after=Archive(result)
 need(replace_entry(replace_entry(result,2,g),3,c)==data,'다른entry 변경');need(bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True),'bank경계 변경')
 raw_checks=0
 for bi,oldbank in enumerate(before.banks):
  for of,nf in zip(oldbank['frames'],after.banks[bi]['frames']):
   need(of['tile_count']==nf['tile_count'],'타일수 변경');ob=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data;nb=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
   need(nb==(nr if bi==0 and of['index']==141 else ob),'다른raw 변경');raw_checks+=1
 layers=0
 for n in range(237):
  if n in(105,*range(175,183)):continue
  for b in(0,5,6,7,8):
   want=before.layer(0 if n==141 else n,b)[0].copy()
   if n==141 and b==0:want=np.where(fx,fx,want).astype(np.uint8)
   need(np.array_equal(after.layer(n,b)[0],want),f'보호레이어 회귀{n}/{b}');layers+=1
 na=np.frombuffer(indexed_atlas(nr,f['tile_count'])[0],np.uint8).reshape(-1,256);gpu=0
 for b in((0,5,6,7,8) if name=='PL02_U.ARC' else(5,6,7,8)):
  for p in composition_frame(nc,b,141)['parts']:
   t=p['tile'];pix=tile(na,t);need(t%16!=0 or not pix[:,0].any(),'141새 GPU U 경계');need(not p['flip_y'] or t//16%16!=0 or not pix[0].any(),'141새 GPU V 경계');gpu+=1
 masks=0;fxrgba=before.rgba(fx)
 for arm in(1,2):
  for mask in range(16):
   goal=before.composite(0,mask,arm)[0];goal.alpha_composite(fxrgba);need(after.composite(141,mask,arm)[0].tobytes()==goal.tobytes(),'141부분마스크 회귀');masks+=1
 need(name!='PL00_U.ARC' or before.composite(141,0)[0].tobytes()==after.composite(141,0)[0].tobytes(),'기본141 그림변경')
 return result,{'input_sha256':sha(data),'output_sha256':sha(result),'raw_checks':raw_checks,'indexed_layer_checks':layers,'mask_checks':masks,'new_gpu_parts_checked':gpu,'fx_pixels':12,'fx_indexed_sha256':sha(fx.tobytes()),'original_141_was_distinct_pose':True,'adopted_accepted_PL00_idle_plus_sparks_rule':True,'base_PL00_raw_tiles_and_composition_exact':name=='PL00_U.ARC','refs126_140_142_and_other_refs_exact':True,'palette_timing_other_entries_exact':True,'packing':packing,'runtime_verified':False}

def main():
 source,assets,records=read('shibuki');inputs={'PL00_U.ARC':TASK/'shibuki_ladder_fix/combined_v1/PL00_U.ARC','PL02_U.ARC':TASK/'idle_return_fix/prepared_v1/shibuki/PL02_U.ARC'};need(not D.exists(),'동결출력 덮어쓰기 거부');outputs={};proof={}
 for name,path in inputs.items():data=path.read_bytes();outputs[name],proof[name]=patch_terminal(data,name,expected_input_sha=INPUT_SHAS[name])
 D.mkdir(parents=True);files={}
 for name,data in outputs.items():
  p=D/name;p.write_bytes(data);files[name]={'before':sha(assets[name]),'after':sha(data),'size':len(data),'path':relative(p),'record':records[name]}
 write(D/'proposal.json',{'project':SOURCES['shibuki'][0],'baseline':relative(source),'baseline_sha256':SOURCES['shibuki'][2],'files':files,'semantic_order':['full_detail6_PL00','142_idle_link','183_clothing_PL00','141_idle_plus_12_sparks'],'sources':{n:relative(p) for n,p in inputs.items()},'verification':proof,'runtime_verified':False})
 board=Image.new('RGB',(900,4*250),(32,37,49));draw=ImageDraw.Draw(board);row=0
 for name in inputs:
  old=Archive(inputs[name].read_bytes());new=Archive(outputs[name])
  for mask in(0,15):
   for i,(a,n,label) in enumerate(((old,141,'before141'),(new,141,'after141'),(new,0,'idle0'))):
    im=a.composite(n,mask)[0];box=(120,120,200,190);bb=im.getbbox();need(bb[0]>=box[0]and bb[1]>=box[1]and bb[2]<=box[2]and bb[3]<=box[3],'시트잘림');im=im.crop(box).resize((240,210),Image.Resampling.NEAREST);x,y=i*300,row*250;draw.text((x+4,y+2),f'{name[:4]} mask{mask} {label}',font=FONT,fill='white');board.paste(im,(x,y+30),im)
   row+=1
 board.save(D/'comparison.png');print(json.dumps({n:sha(d) for n,d in outputs.items()}))

if __name__=='__main__':main()
