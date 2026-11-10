"""나나 부분 포스 대기에서 고립된 베일 경계를 머리 파츠 소유로 옮긴다.

수용된 풀아머/기본형 그림은 픽셀 동일. 입력 BIN과 사용자 자료는 읽기만 한다.
"""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,TASK,OUT,SOURCES,sha,digest,write,need,relative,FONT,DiscReader,entry
from scripts.prepare_riko_ui import replace_entry
from scripts.prepare_shibuki_ultimate_production import repack_parts,records as native_records
from scripts.prepare_cliche_logo_v4 import old_records,pack_bank
from scripts.ultimate_costume_swap_ui import sprite_canvas
from scripts.verify_shibuki_save_icon import icon,rgba
from src.psx_player import graphics_bank,composition_frame,decode_stream,indexed_atlas,bank_offsets
from src.psx_ui_atlas import local_composition,aliased_composition,tile_pixels,write_tile
from src.psx_sprite_batch import pack_original_layout
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_static_effect import compose_static

D=TASK/'nana_parts_fix/prepared_v2'
REFS=(0,85,86,87,92,115,116,117,118,119)
SOURCE_ASSETS={'PL00_U.ARC':'3248f3c68bc86661ceb20ed19081b63d97df400f3bfa5dcec6d48afcd2b8e412','MOJIPAT.ARC':'d9ccef0c9539c9a29ae6c61aa7c5fbcc5a44af40076bf7ec8f269b84ead31bad','LOAD_U.ARC':'e16a2027dc38da4a62d74d551c870b448c8461b1cef713e2a4753a1be618d33b','SLUS_005.61':'1789ef719487b3e49571ccc2f419d6eb36c16f03709a16cb74f856d433f699ab'}

def spots(n):
 if n in (115,116,117,118):return [(11,-13),(11,-12),(12,-12)]
 if n==119:return [(11,-15),(11,-14)]
 return [(11,-14),(11,-13)]

def patch_player(data):
 need(sha(data)==SOURCE_ASSETS['PL00_U.ARC'],'지원하지 않는 플레이어 ARC 또는 이미 교정한 입력')
 before=Archive(data);g,c=before.g,before.c;groups={};head_records={};raw_targets={};proof=[]
 for f in before.banks[0]['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
 for offset,refs in groups.items():
  if not set(refs)&set(REFS):continue
  need(set(refs)<=set(REFS),'미선택 압축 별칭');f=before.banks[0]['frames'][refs[0]];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data
  used={p['tile'] for n in refs for b in(0,5,6,7,8) for p in composition_frame(c,b,n)['parts']};free=sorted(set(range(f['tile_count']))-used);need(free,'새 머리 경계용 미참조 타일 없음');tile=free[0]
  old_atlas,locations,_=indexed_atlas(raw,f['tile_count']);new=raw;newtile=None
  for n in refs:
   leg,_=before.layer(n,8);head,_=before.layer(n,5);target=leg.copy();points=spots(n)
   need(all(leg[y+160,x+160]==1 and head[y+160,x+160]==0 for x,y in points),'예상 검은 경계가 아님')
   for x,y in points:target[y+160,x+160]=0
   cp=local_composition(composition_frame(c,8,n));tiles={p['tile'] for p in cp['parts']}
   need(not tiles&{p['tile'] for other in refs for b in(0,5,6,7) for p in composition_frame(c,b,other)['parts']},'다리 타일이 보호 파츠와 공유됨')
   new=pack_original_layout(new,f['tile_count'],target,cp,tiles,origin=(160,160))
   left=min(x for x,y in points);top=min(y for x,y in points);pix=np.zeros((16,16),np.uint8);pad=1 if tile%16==0 else 0
   for x,y in points:pix[y-top,x-left+pad]=1
   need(newtile is None or np.array_equal(newtile,pix),'별칭 프레임의 경계 형상 충돌');newtile=pix
   head_records[n]=native_records(c,5,n)+struct.pack('<BBbb',0,tile,left-pad,top)
   proof.append({'ref':n,'points_world':points,'from_bank':8,'to_bank':5,'new_tile':tile,'gpu_left_padding':pad,'new_part_x':left-pad,'old_stream_offset':offset,'old_head_parts':len(composition_frame(c,5,n)['parts']),'new_head_parts':len(composition_frame(c,5,n)['parts'])+1})
  nr=bytearray(new)
  for y in range(16):
   for x in range(16):
    pos=(tile//16*16+y)*256+tile%16*16+x;at,shift=locations[pos];nr[at]=(nr[at]&~(15<<shift))|(int(newtile[y,x])<<shift)
  for n in refs:raw_targets[n]=bytes(nr)
 nc,slack=repack_parts(c,5,head_records);codes={n:encode_stream(r) for n,r in raw_targets.items()};ng=g;compression=[]
 if all(len(codes[n])<=before.banks[0]['frames'][n]['limit']-before.banks[0]['frames'][n]['offset'] for n in codes):
  for offset,refs in groups.items():
   if refs[0] in raw_targets:ng,info=replace_stream(ng,before.banks[0]['frames'][refs[0]],raw_targets[refs[0]],allocated_limit=before.banks[0]['frames'][refs[0]]['limit']);compression.append(info)
 else:ng,info=repack_graphics_bank(g,0,codes);compression.append(info)
 result=replace_entry(replace_entry(data,2,ng),3,nc);after=Archive(result)
 # Explicit original bank dimensions; all animation/palette/other entries exact.
 need(replace_entry(replace_entry(result,2,g),3,c)==data,'다른 ARC entry 변경')
 need(bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True) and bank_offsets(c)==bank_offsets(nc),'뱅크 경계 변경')
 gs=bank_offsets(g,allow_aliases=True);need(g[gs[1]:]==ng[gs[1]:],'다른 그래픽 뱅크 변경')
 cs=bank_offsets(c);need(c[:cs[5]]==nc[:cs[5]] and c[cs[6]:]==nc[cs[6]:],'머리 외 조립 뱅크 변경')
 gpu_checks=0;preserved_native_edges=[]
 for n in REFS:
  f=after.banks[0]['frames'][n];nr=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data
  of=before.banks[0]['frames'][n];oldraw=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data
  oa=np.frombuffer(indexed_atlas(oldraw,f['tile_count'])[0],np.uint8).reshape(-1,256)
  na=np.frombuffer(indexed_atlas(nr,f['tile_count'])[0],np.uint8).reshape(-1,256)
  for b in(0,5,6,7,8):
   for p in composition_frame(nc,b,n)['parts']:
    t=p['tile'];patch=na[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    bad=(t%16==0 and patch[:,0].any()) or(p['flip_y'] and t//16%16==0 and patch[0].any())
    if bad:
     oldpatch=oa[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
     need(np.array_equal(patch,oldpatch) and any(all(p[k]==q[k] for k in('flags','tile','x','y')) for q in composition_frame(c,b,n)['parts']),'새 GPU U/V 경계 위반')
     preserved_native_edges.append({'ref':n,'bank':b,'tile':t})
    gpu_checks+=1
  added=composition_frame(nc,5,n)['parts'][-1];t=added['tile']
  need(t%16!=0 or not na[t//16*16:t//16*16+16,0].any(),'새 머리 타일 col0이 비투명')
 rendered_checks=0;unchanged_checks=0
 for n in range(237):
  if n in (105,*range(175,183)):continue
  for b in (0,5,6,7,8):
   old,_=before.layer(n,b);actual,_=after.layer(n,b);expected=old.copy()
   if n in REFS and b in (5,8):
    for x,y in spots(n):expected[y+160,x+160]=1 if b==5 else 0
   need(np.array_equal(actual,expected),f'파츠 픽셀 불일치 {n}/{b}')
  for arm in(1,2):
   for mask in range(16):
    old,_=before.composite(n,mask,arm);new,_=after.composite(n,mask,arm);expected=np.array(old)
    if n in REFS:
     for x,y in spots(n):
      if mask&1:expected[y+160,x+160]=np.array(before.rgba(np.array([[1]],np.uint8),16))[0,0]
      elif mask&8:expected[y+160,x+160]=0
    need(np.array_equal(np.array(new),expected),f'마스크 회귀 {n}/{mask}/{arm}')
    if mask in (0,15):need(new.tobytes()==old.tobytes(),'기본/풀파츠 변경')
    rendered_checks+=1;unchanged_checks+=new.tobytes()==old.tobytes()
 return result,{'transfers':proof,'head_bank_remaining_slack':slack,'compression':compression,'gpu_parts_checked':gpu_checks,'preserved_native_edge_exceptions':preserved_native_edges,'added_head_tile_col0_transparent':True,'rendered_mask_checks':rendered_checks,'unchanged_mask_checks':unchanged_checks,'base_and_full_exact':True,'other_entries_and_banks_exact':True,'palette_animation_geometry_fixed':True,'geometry_note':'기존파츠 좌표 그대로; 이전 경계점 표시용 머리 part만 하나 추가','runtime_verified':False}

def patch_save(menu,load,exe):
 need(all(sha(data)==SOURCE_ASSETS[name] for name,data in [('MOJIPAT.ARC',menu),('LOAD_U.ARC',load),('SLUS_005.61',exe)]),'지원하지 않는 저장 UI 자원 조합')
 texture=entry(load,0x10008);records=old_records(menu,2);need(len(records)==54,'최신 54 frame UI 필요');cp=aliased_composition(menu,2,48)
 # The selected native leg tile is exclusive to frame48. Use only a proven
 # unused bottom-right cell, outside the native 208px-wide background UV.
 sources={};used=set()
 for b in(0,2,3):
  for n in range(aliased_composition(menu,b,0)['bank_frame_count']):
   for p in aliased_composition(menu,b,n)['parts']:sources.setdefault(p['page']*256+p['tile'],set()).add((b,n));used.add(p['page']*256+p['tile'])
 direct={y*16+x for y in range(13,16) for x in range(13)};table=0xDED04
 for row in range(9):
  x,y,t,w,h,clut=struct.unpack_from('<hhBBBB',exe,table+row*8);starts=list(exe[table+72:table+84]) if row==6 else[t]
  direct.update(start+dy*16+dx for start in starts for dy in range(h) for dx in range(w))
 slot=255;need(slot not in used|direct,'검증된 미참조 UI 타일255 아님')
 # This cell contains stale sprite texels, but all composed consumers and
 # the native direct-UV loading/background paths exclude it. Do not infer
 # that a nonblank cell is free; the exhaustive ownership check above is required.
 stale_slot_sha=sha(tile_pixels(texture,slot))
 nt=bytearray(texture);changed_tiles=set();points=spots(0)
 for p in cp['parts']:
  tile=p['page']*256+p['tile'];pix=np.frombuffer(tile_pixels(texture,tile),np.uint8).reshape(16,16).copy();changed=False
  for x,y in points:
   if p['x']<=x<p['x']+16 and p['y']<=y<p['y']+16:
    need(not p['flip_x'] and not p['flip_y'] and p['page']==0,'예상 외 UI 방향/페이지');need(pix[y-p['y'],x-p['x']]==1,'UI경계 인덱스 불일치');pix[y-p['y'],x-p['x']]=0;changed=True
  if changed:
   need(sources[tile]=={(2,48)} and tile not in direct,'UI다리타일 공유/직접UV');write_tile(nt,tile,pix.tobytes());changed_tiles.add(tile)
 pix=np.zeros((16,16),np.uint8);pix[0:2,0]=1;write_tile(nt,slot,pix.tobytes());changed_tiles.add(slot)
 records[45].append(struct.pack('<BBbb',4,slot,11,-14));offsets=bank_offsets(menu);bank,packing=pack_bank(records,offsets[3]-offsets[2]);nm=menu[:offsets[2]]+bank+menu[offsets[3]:]
 need(nm[:offsets[2]]==menu[:offsets[2]] and nm[offsets[3]:]==menu[offsets[3]:],'메뉴의 다른 bank 변경')
 for b in(0,2,3):
  for n in range(aliased_composition(menu,b,0)['bank_frame_count']):
   old=sprite_canvas(compose_static(texture,local_composition(aliased_composition(menu,b,n))));new=sprite_canvas(compose_static(bytes(nt),local_composition(aliased_composition(nm,b,n))));expected=old.copy()
   if b==2 and n in (45,48):
    for x,y in points:expected[y+80,x+80]=1 if n==45 else 0
   need(np.array_equal(new,expected),f'다른 UI raster 변경 {b}/{n}')
 for t in range(len(texture)//128):
  if t not in changed_tiles:need(tile_pixels(texture,t)==tile_pixels(nt,t),'비대상 UI 타일 변경')
 for arm in(1,2):
  for mask in range(16):
   old=icon(menu,texture,mask,arm);new=icon(nm,bytes(nt),mask,arm);expected=old.copy();po=struct.unpack_from('<I',menu,4)[0];color=struct.unpack_from('<H',menu,po+9*32+2)[0]
   for x,y in points:
    if mask&1:expected[y+80,x+80]=color
    elif mask&8:expected[y+80,x+80]=0
   need(np.array_equal(new,expected),'저장 UI 마스크 회귀')
 return nm,replace_entry(load,0x10008,bytes(nt)),{'frame45_head_appended':True,'frame48_leg_only_two_pixels_removed':True,'new_tile':slot,'new_tile_previous_unreferenced_pixels_sha256':stale_slot_sha,'direct_uv_tiles':sorted(direct),'changed_tiles':sorted(changed_tiles),'menu_bank_packing':packing,'mask_checks':32,'all_other_frames_tiles_palette_exact':True}

def main():
 project,stem,expected=SOURCES['nana'];source=ROOT/f'out/{project}/ultimate_costumes_swapped_20261105_v1/{stem}.bin';need(digest(source)==expected,'지원하지 않는 BIN')
 need(not D.exists(),'새 준비 디렉터리만 허용')
 with source.open('rb') as f:
  disc=DiscReader(f,source.stat().st_size);records={q['name'].split(';')[0]:q for q in disc.inspect()['files']};assets={n:disc.read(records[n]['lba'],records[n]['size']) for n in('PL00_U.ARC','MOJIPAT.ARC','LOAD_U.ARC','SLUS_005.61')}
 modified,gameproof=patch_player(assets['PL00_U.ARC']);menu,load,uiproof=patch_save(assets['MOJIPAT.ARC'],assets['LOAD_U.ARC'],assets['SLUS_005.61']);changed={'PL00_U.ARC':modified,'MOJIPAT.ARC':menu,'LOAD_U.ARC':load}
 D.mkdir(parents=True);proposal={'project':project,'baseline':relative(source),'baseline_sha256':expected,'files':{},'game_checks':gameproof,'save_checks':uiproof,'runtime_verified':False}
 for name,new in changed.items():
  p=D/name;p.write_bytes(new);proposal['files'][name]={'before':sha(assets[name]),'after':sha(new),'size':len(new),'path':relative(p),'record':records[name],'changed_bytes':sum(a!=b for a,b in zip(assets[name],new))}
 oldarc,newarc=Archive(assets['PL00_U.ARC']),Archive(modified);rows=[]
 for n in(0,115,119):
  for mask in(1,8,12,15):rows.append((n,mask,oldarc.composite(n,mask)[0],newarc.composite(n,mask)[0]))
 board=Image.new('RGB',(4*400,3*280),'#b9c6c9');dr=ImageDraw.Draw(board)
 for i,(n,mask,old,new) in enumerate(rows):
  x=i%4*400;y=i//4*280;dr.text((x+4,y+2),f'ref{n} mask{mask:X} | before / after',font=FONT,fill='black')
  for j,im in enumerate((old,new)):
   im=im.crop((136,130,186,194)).resize((200,256),Image.Resampling.NEAREST);board.paste(im,(x+j*200,y+24),im)
 board.save(D/'comparison.png');write(D/'proposal.json',proposal);need(digest(source)==expected,'원본 입력 변경');print(json.dumps({'path':relative(D/'proposal.json'),'checks':gameproof['rendered_mask_checks'],'files':{n:q['after'] for n,q in proposal['files'].items()}},ensure_ascii=False))

if __name__=='__main__':main()
