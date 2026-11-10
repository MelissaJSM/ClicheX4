"""New hurt/low-HP bodies; separately preserve sparks and regenerate body-shaped flash."""
from pathlib import Path
import sys,json,struct,hashlib,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
D=Path(__file__).parent
sys.path.insert(0,str(D))
import pack_rin_keys as native
from scripts.prepare_shibuki_ultimate_production import records,repack_parts,fast_fit
from scripts.solve_sprite_cover import cover
from scripts.export_x_consistency import page

P=D/'rin_extension/prepared_movement_finish_v1/PL01_U.ARC'
SHA='72d04d36dde42379a144dc4688b09c582e4c0f867bc70d5742c33bb65b75b42a'
ART=D/'rin_extension/hurt_registered_v2'
OUT=D/'rin_extension/prepared_hurt_lowhp_v1'
CACHE=D/'rin_extension/hurt_pack_cache_v1'
ART_HASH={135:'e0f103a55a24bf4d7a6c7f133cba305b34fae8723471d9efb382b1420549323a',139:'2ebe80f7d0451d3d3b12a4d07739481c53dacabf908cf5e070c008e28a5d98e6',149:'d4e216703487a0a2ab9e621a412bd90466301f0439d4475348048a57053207a5',152:'b1f1a363552695a3e660a269dc0fa7ef6faa746eca5c3b8b90913966caab006d'}
SELECTED=set(range(135,146))|set(range(149,155))
LIGHT=np.array([0,7,8,9,8,9,10,9,10,11,11,11,13,14,11,11],np.uint8)

def compose(raw,count,cp):
 pixels,size,bb,_=native.compose_indices(raw,count,cp,allowed_cluts={0,2})
 v=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0])
 a=np.zeros((384,384),np.uint8)
 a[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=v
 return a

def dilation(mask,r,manhattan=False):
 pad=np.pad(mask,r)
 a=np.zeros_like(mask)
 for dy in range(-r,r+1):
  for dx in range(-r,r+1):
   if manhattan and abs(dx)+abs(dy)>r:continue
   a|=pad[r+dy:r+dy+384,r+dx:r+dx+384]
 return a

def flash(body):
 m=body>0
 return np.where(dilation(m,1),np.where(m&(body!=11),10,11),0).astype(np.uint8)

def derive(arc):
 native.need(native.sha(arc)==SHA,'Wrong source ARC')
 masters={}
 for n,h in ART_HASH.items():
  path=ART/f'b0_{n:03}_indices.png'
  native.need(native.sha(path.read_bytes())==h,'Changed registered native art')
  a=np.array(Image.open(path))
  native.need(a.shape==(384,384) and a.dtype==np.uint8 and a.max()<=15,'Invalid native pixels')
  masters[n]=a
 g,c=native.entry(arc,2),native.entry(arc,3)
 bank=native.graphics_bank(g,0)
 targets={n:a.copy() for n,a in masters.items()}
 effects={}
 for master,refs in ((135,(136,137)),(139,(140,141))):
  for n in refs:
   f=bank['frames'][n]
   raw=native.decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
   cp=native.composition_frame(c,0,n)
   native.need(records(c,0,n)[:40]==records(c,0,master),'Body and effect sharing changed')
   effects[n]=compose(raw,f['tile_count'],{**cp,'parts':cp['parts'][10:]})
   targets[n]=np.where(effects[n]%16!=0,effects[n],masters[master])
 targets[138]=flash(masters[135])
 targets[142]=flash(masters[139])
 m=masters[139]>0
 inside=m.copy()
 for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
  inside&=np.roll(np.roll(m,dx,1),dy,0)
 targets[143]=np.where(m,np.where(inside,47,37),0).astype(np.uint8)
 targets[144]=LIGHT[masters[139]]
 near=dilation(m,1,True)&~m
 far=dilation(m,2,True)&~m&~near
 effects[145]=np.where(near,37,np.where(far,38,0)).astype(np.uint8)
 targets[145]=np.where(effects[145]>0,effects[145],targets[144])
 for master,refs in ((149,(149,150,151)),(152,(152,153,154))):
  old=native.render(arc,0,0,master)[0]
  for n in refs:
   native.need(np.array_equal(native.render(arc,0,0,n)[0],old),'LowHP alias no longer identical')
   targets[n]=masters[master].copy()
 native.need(set(targets)==SELECTED,'Wrong target set')
 return targets,effects

def pack_layer(raw,count,target,pool,part_count,clut,label):
 native.need(target.max()<=15,'Layer must be local 4-bit')
 # Eight-tile151 needs its existing tile0. Assign it only a window whose
 # entire first column is transparent, then independently check GPU edges.
 allow_zero=(label=='lowhp151')
 pool=[t for t in pool if t%16!=0 or (t==0 and allow_zero)]
 limit=min(len(pool),part_count)
 digest=native.sha(target.tobytes()+bytes(pool)+bytes([part_count]))
 CACHE.mkdir(exist_ok=True)
 cache=CACHE/f'{label}_{digest}.json'
 if cache.exists():rects=json.loads(cache.read_text('utf8'))['rects']
 else:
  rects=fast_fit(target>0,limit)
  if rects is None:
   result=cover(target>0,limit,30)
   native.need(result['fits'],f'Cannot cover {label} within safe tile/part count {limit}')
   rects=result['rects']
  cache.write_text(json.dumps({'rects':rects,'count':len(rects),'limit':limit},indent=2)+'\n','utf8')
 if allow_zero:
  clear=[i for i,(x,y)in enumerate(rects) if not np.any(target[y:y+16,x])]
  native.need(bool(clear),'No transparent first-column rectangle for tile0')
  j=clear[0]
  rects=[rects[j]]+rects[:j]+rects[j+1:]
 rec=b''.join(bytes((clut*4,t,(x-160)&255,(y-160)&255)) for t,(x,y) in zip(pool,rects))
 while len(rec)<part_count*4:rec+=rec[-4:]
 parts=[]
 for i in range(0,len(rec),4):
  flags,t,x,y=rec[i:i+4]
  parts.append({'index':i//4,'tile':t,'x':x if x<128 else x-256,'y':y if y<128 else y-256,'flags':0,'clut':0,'page':0,'unknown_flags':0,'flip_x':False,'flip_y':False})
 cp={'bank':0,'frame':0,'parts':parts}
 _,size,bb,_=native.compose_indices(raw,count,cp)
 crop=target[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
 nr=native.packer.edit_visible_set(raw,count,[(cp,crop.tobytes(),size)])
 native.need(np.array_equal(compose(nr,count,cp),target),'Layer readback differs')
 return nr,rec,{'label':label,'rectangles':rects,'tiles':pool[:len(rects)],'part_count':part_count,'clut':clut,'safe_page_edges':True,'no_global_hidden_cleanup':True}

def build(arc,targets,effects):
 expected,expected_fx=derive(arc)
 native.need(set(targets)==SELECTED and set(effects)==set(expected_fx),'Wrong supplied references')
 for n in targets:native.need(np.array_equal(targets[n],expected[n]),f'Art differs at {n}')
 for n in effects:native.need(np.array_equal(effects[n],expected_fx[n]),f'Effect differs at {n}')
 g,c=native.entry(arc,2),native.entry(arc,3)
 bank=native.graphics_bank(g,0)
 raws={};part_changes={};methods=[]
 def old(n):
  f=bank['frames'][n]
  return native.decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data,f['tile_count']
 for master,refs in ((135,(135,136,137)),(139,(139,140,141))):
  raw,count=old(master)
  nr,rec,method=pack_layer(raw,count,targets[master],range(10),10,0,f'body{master}')
  methods.append(method)
  # These original effect-only tiles and exact records are disjoint from new body tiles.
  atlas,_,_=native.indexed_atlas(raw,count)
  after,_,_=native.indexed_atlas(nr,count)
  aa=np.frombuffer(atlas,np.uint8).reshape(-1,256)
  zz=np.frombuffer(after,np.uint8).reshape(-1,256)
  for t in range(10,count):
   y,x=t//16*16,t%16*16
   native.need(np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16]),'Original spark/lightning tile changed')
  for n in refs:
   native.need(bank['frames'][n]['offset']==bank['frames'][master]['offset'],'Lost body sharing')
   raws[n]=nr
   part_changes[n]=rec+records(c,0,n)[40:]
 for n in (138,142,143):
  raw,count=old(n)
  clut=2 if n==143 else 0
  target=(targets[n]%16).astype(np.uint8)
  nr,rec,method=pack_layer(raw,count,target,range(count),len(records(c,0,n))//4,clut,f'flash{n}')
  raws[n]=nr;part_changes[n]=rec;methods.append(method)
 raw,count=old(144)
 nr,body_rec,method=pack_layer(raw,count,targets[144],range(11),11,0,'light_body144')
 methods.append(method)
 nr,ring_rec,method=pack_layer(nr,count,(effects[145]%16).astype(np.uint8),range(11,count),15,2,'aura145')
 methods.append(method)
 raws[144]=raws[145]=nr
 part_changes[144]=body_rec;part_changes[145]=body_rec+ring_rec
 for master,refs in ((149,(149,150)),(151,(151,)),(152,(152,153,154))):
  raw,count=old(master)
  nr,rec,method=pack_layer(raw,count,targets[master],range(count),8,0,f'lowhp{master}')
  methods.append(method)
  for n in refs:
   raws[n]=nr;part_changes[n]=rec
 native.need(set(raws)==SELECTED,'Incomplete prepared references')
 for n,rec in part_changes.items():native.need(len(rec)==len(records(c,0,n)),'Part count changed')
 nc,parts_slack=repack_parts(c,0,part_changes)
 ng,layout=native.packer.repack_raw(g,0,raws)
 out=native.replace_entry(native.replace_entry(arc,2,ng),3,nc)
 native.need(native.replace_entry(native.replace_entry(out,2,g),3,c)==arc,'Other ARC entry changed')
 native.need(native.bank_offsets(g,allow_aliases=True)==native.bank_offsets(ng,allow_aliases=True),'Graphics bank boundaries changed')
 native.need(native.bank_offsets(c)==native.bank_offsets(nc),'Composition bank boundaries changed')
 totals={'raw':0,'display':0,'non_target_raw_exact':0,'non_target_display_exact':0}
 changes=[]
 for b in (0,1):
  ob,nb=native.graphics_bank(g,b),native.graphics_bank(ng,b)
  for of,nf in zip(ob['frames'],nb['frames']):
   n=of['index'];chosen=b==0 and n in SELECTED
   native.need(of['tile_count']==nf['tile_count']<=32,'Tile count changed')
   ar=native.decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data
   br=native.decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
   totals['raw']+=1
   if not chosen:
    native.need(ar==br,'Non-target raw changed')
    native.need(records(c,b*5,n)==records(nc,b*5,n),'Non-target parts changed')
    totals['non_target_raw_exact']+=1
   else:
    aa=np.frombuffer(native.indexed_atlas(ar,of['tile_count'])[0],np.uint8).reshape(-1,256)
    zz=np.frombuffer(native.indexed_atlas(br,nf['tile_count'])[0],np.uint8).reshape(-1,256)
    for p in native.composition_frame(nc,b*5,n)['parts']:
     t=p['tile'];y,x=t//16*16,t%16*16
     if t%16==0:native.need(not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]>0)),'New reflected U=0 alpha')
     if p['flip_y'] and t//16%16==0:native.need(not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]>0)),'New flipped V=0 alpha')
   if b==1 and 42<=n<=49:continue
   before=native.render(arc,b,b*5,n)[0];after=native.render(out,b,b*5,n)[0]
   native.need(np.array_equal(after,targets[n] if chosen else before),f'Readback differs {b}:{n}')
   totals['display']+=1
   if not chosen:totals['non_target_display_exact']+=1
   else:changes.append({'bank':b,'ref':n,'changed_pixels':int(np.count_nonzero(before!=after))})
 for n in (136,137,140,141):
  f=native.graphics_bank(ng,0)['frames'][n]
  nr=native.decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data
  cp=native.composition_frame(nc,0,n)
  native.need(records(nc,0,n)[40:]==records(c,0,n)[40:],'Original effect record changed')
  native.need(np.array_equal(compose(nr,f['tile_count'],{**cp,'parts':cp['parts'][10:]}),effects[n]),'Original effect pixels changed')
 return out,{'counts':totals,'changes':changes,'layout':layout,'parts_slack':parts_slack,'methods':methods,'part_counts_preserved':True,'tile_counts_preserved':True,'original_spark_lightning_tiles_records_exact':True,'new_gpu_boundary_alpha':0,'non_target_entries_palette_audio_timing_exact':True,'hidden_global_cleanup':False,'authored_registered_pixels_exact':True}

def boards(arc,out):
 palette=native.entry(arc,9)
 normal=list(struct.unpack_from('<64H',palette))
 red=normal.copy();red[:16]=struct.unpack_from('<16H',palette,13*32)
 for form,words in (('normal',normal),('black',red)):
  for i,start in enumerate(range(0,len(SELECTED),4)):
   items=[]
   for n in sorted(SELECTED)[start:start+4]:
    items.extend([(f'{n} previous',native.rgba(native.render(arc,0,0,n)[0],words)),(f'{n} packed',native.rgba(native.render(out,0,0,n)[0],words))])
   page(items,native.rgba(native.render(arc,0,0,147)[0],words),OUT/f'{form}_readback_{i:02}.png',cols=2,scale=4)

def main():
 native.need(not OUT.exists(),'Use a new output directory')
 arc=P.read_bytes();targets,effects=derive(arc)
 out,proof=build(arc,targets,effects)
 again,_=build(arc,targets,effects)
 native.need(out==again,'Reproduction differs')
 OUT.mkdir()
 (OUT/'PL01_U.ARC').write_bytes(out)
 for n,a in targets.items():Image.fromarray(a).save(OUT/f'target_{n:03}.png')
 for f in ('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/f,OUT/f)
 recipe=json.loads((P.parent/'static_effects.json').read_text('utf8'))
 recipe['parts_sha256']=native.sha(native.entry(out,3))
 rp=OUT/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 proposal={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':native.sha(out),'new_art_refs':[f'b0_{n:03}' for n in sorted(SELECTED)],'shared_support_refs':[],'cumulative_main_refs':117,'previous_frozen_art_refs':100,'verification':proof,'static_body_patch':{'recipe':str(rp.relative_to(ROOT)),'sha256':native.sha(rp.read_bytes())},'reproducible':True,'registration':str((ART/'registration.json').relative_to(ROOT)),'scope':'새 피격135/139·저체력149/152 4키, 효과 파생9·동일저체력4를 포함한17참조. 원래 불꽃/번개4의 픽셀·위치·CLUT 및 기존100 보존.','authored_body_refs':[135,139,149,152],'derived_main_flash_refs':list(range(136,139))+list(range(140,146)),'game_changed':False,'gameplay_runtime_verified':False,'root_review_pending':True,'user_accepted':False,'ready_for_checkpoint_integration':False}
 (OUT/'proposal.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n','utf8')
 boards(arc,out)
 print(json.dumps({'sha256':native.sha(out),'counts':proof['counts'],'layout':proof['layout']}))

if __name__=='__main__':main()
