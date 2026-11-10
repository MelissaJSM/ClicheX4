"""Nana veil ownership correction, exact current parent only; never edits a BIN."""
from prepare_review import *
from scripts.prepare_riko_ui import replace_entry
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from src.psx_player import decode_stream,indexed_atlas,bank_offsets
from src.psx_sprite_batch import pack_original_layout
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank

EXPECTED_ARC='61b38674a3d82484092577bed4c8c0426e9c4f5a52b92f9dfeb0056157afde6b'
REFS=(120,121,122,123,124,125,141,142)
def need(v,m):
 if not v:raise ValueError(m)
def points(ref):
 if ref in(141,142):return [(11,-14),(11,-13)]
 top=-9-(ref-120)//2
 return [(x,y)for y in(top,top+1)for x in(10,11,12)]
def color(ref,x,y):
 if ref>=141:return 1
 return 3 if (x,y)==(11,-8-(ref-120)//2)else 2
def patch(data):
 need(sha(data)==EXPECTED_ARC,'Unsupported ARC parent')
 before=Archive(data);g,c=before.g,before.c;groups={};raw_targets={};head_records={};proof=[]
 for f in before.banks[0]['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
 for offset,refs in groups.items():
  if not set(refs)&set(REFS):continue
  need(set(refs)<=set(REFS),'Protected compressed alias')
  f=before.banks[0]['frames'][refs[0]];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data
  used={p['tile']for n in refs for b in(0,5,6,7,8)for p in composition_frame(c,b,n)['parts']}
  free=sorted(set(range(f['tile_count']))-used,key=lambda t:(t%16==0,t));need(free,'No unused native tile')
  tile=free[0];new=raw;newtile=None
  for n in refs:
   src=8 if n>=141 else 6;index=1 if n>=141 else 2;layer,_=before.layer(n,src);head,_=before.layer(n,5);target=layer.copy();pts=points(n)
   need(all(layer[y+160,x+160]==color(n,x,y)and head[y+160,x+160]==0 for x,y in pts),'Unexpected material pixels')
   for x,y in pts:target[y+160,x+160]=0
   cp=local_composition(composition_frame(c,src,n));tiles={p['tile']for p in cp['parts']}
   need(not tiles&{p['tile']for other in refs for b in(0,5,6,7,8)if b!=src for p in composition_frame(c,b,other)['parts']},'Source tile shared with another owner')
   new=pack_original_layout(new,f['tile_count'],target,cp,tiles,origin=(160,160))
   left=min(x for x,y in pts);top=min(y for x,y in pts);pad=1 if tile%16==0 else 0;pix=np.zeros((16,16),np.uint8)
   for x,y in pts:pix[y-top,x-left+pad]=color(n,x,y)
   need(newtile is None or np.array_equal(newtile,pix),'Aliased boundary shape differs');newtile=pix
   head_records[n]=records(c,5,n)+struct.pack('<BBbb',0,tile,left-pad,top)
   proof.append({'ref':n,'points_world':pts,'indices':[color(n,x,y)for x,y in pts],'from_bank':src,'to_bank':5,'new_tile':tile,'gpu_left_padding':pad,'new_part_x':left-pad,'new_part_y':top,'old_stream_offset':offset,'old_tile_count':f['tile_count'],'new_tile_count':f['tile_count']})
  _,locations,_=indexed_atlas(raw,f['tile_count']);nr=bytearray(new)
  for y in range(16):
   for x in range(16):
    p=(tile//16*16+y)*256+tile%16*16+x;at,shift=locations[p];nr[at]=(nr[at]&~(15<<shift))|(int(newtile[y,x])<<shift)
  for n in refs:raw_targets[n]=bytes(nr)
 nc,slack=repack_parts(c,5,head_records);codes={n:encode_stream(r)for n,r in raw_targets.items()};ng=g;compression=[]
 if all(len(code)<=before.banks[0]['frames'][n]['limit']-before.banks[0]['frames'][n]['offset']for n,code in codes.items()):
  for off,refs in groups.items():
   if refs[0]in raw_targets:ng,p=replace_stream(ng,before.banks[0]['frames'][refs[0]],raw_targets[refs[0]],allocated_limit=before.banks[0]['frames'][refs[0]]['limit']);compression.append(p)
 else:ng,p=repack_graphics_bank(g,0,codes);compression.append(p)
 result=replace_entry(replace_entry(data,2,ng),3,nc);after=Archive(result)
 need(replace_entry(replace_entry(result,2,g),3,c)==data,'Other ARC entry changed')
 need(bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)and bank_offsets(c)==bank_offsets(nc),'Bank boundaries changed')
 gs=bank_offsets(g,allow_aliases=True);cs=bank_offsets(c);need(g[gs[1]:]==ng[gs[1]:],'Other graphics bank changed');need(c[:cs[5]]==nc[:cs[5]]and c[cs[6]:]==nc[cs[6]:],'Other composition bank changed')
 rawchecks=0
 for bank,(oldbank,newbank)in enumerate(zip(before.banks,after.banks)):
  for n,(of,nf)in enumerate(zip(oldbank['frames'],newbank['frames'])):
   need(of['tile_count']==nf['tile_count'],'Tile count changed')
   if bank==0 and n in REFS:continue
   old=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data;new=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
   need(old==new,f'Other raw frame changed {bank}/{n}');rawchecks+=1
 gpu_checks=0;preserved_edges=[]
 for n in REFS:
  f=after.banks[0]['frames'][n];of=before.banks[0]['frames'][n]
  oa=np.frombuffer(indexed_atlas(decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data,f['tile_count'])[0],np.uint8).reshape(-1,256)
  na=np.frombuffer(indexed_atlas(decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data,f['tile_count'])[0],np.uint8).reshape(-1,256)
  for b in(0,5,6,7,8):
   for p in composition_frame(nc,b,n)['parts']:
    t=p['tile'];new=na[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    bad=(t%16==0 and new[:,0].any())or(p['flip_y']and t//16%16==0 and new[0].any())
    if bad:
     old=oa[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
     need(np.array_equal(old,new)and any(all(p[k]==q[k]for k in('flags','tile','x','y'))for q in composition_frame(c,b,n)['parts']),'New GPU boundary violation');preserved_edges.append({'ref':n,'bank':b,'tile':t})
    gpu_checks+=1
 masks=0;unchanged=0;layers=0;changed=[]
 for n in range(237):
  if n in(105,*range(175,183)):continue
  expected_layers={}
  for b in(0,5,6,7,8):
   old,_=before.layer(n,b);actual,_=after.layer(n,b);expected=old.copy()
   if n in REFS:
    src=8 if n>=141 else 6;index=1 if n>=141 else 2
    if b in(5,src):
     for x,y in points(n):expected[y+160,x+160]=color(n,x,y)if b==5 else 0
   need(np.array_equal(actual,expected),f'Layer regression {n}/{b}');expected_layers[b]=expected;layers+=1
  for arm in(1,2):
   for mask in range(16):
    old=before.composite(n,mask,arm)[0];new=after.composite(n,mask,arm)[0];expected=before.rgba(expected_layers[0])
    for bit,b in((8,8),(1,5),(4,7),(2,6)):
     if mask&bit:expected.alpha_composite(before.rgba(expected_layers[b],32 if b==7 and arm==2 else 16))
    need(new.tobytes()==expected.tobytes(),f'Composite regression {n}/{mask}/{arm}')
    if mask in(0,15):need(new.tobytes()==old.tobytes(),'Base/full image changed')
    same=old.tobytes()==new.tobytes();masks+=1;unchanged+=same
    if not same:changed.append({'ref':n,'mask':mask,'arm':arm,'pixel_count':int(np.any(np.asarray(old)!=np.asarray(new),axis=2).sum())})
 return result,{'transfers':proof,'head_bank_remaining_slack':slack,'compression':compression,'unchanged_other_raw_frames':rawchecks,'layer_checks':layers,'mask_checks':masks,'unchanged_mask_checks':unchanged,'changed_composites':changed,'gpu_parts_checked':gpu_checks,'preserved_native_edge_exceptions':preserved_edges,'base_and_full_exact':True,'palette_audio_and_other_entries_exact':True,'bank_boundaries_fixed':True,'tile_count_unchanged':True,'runtime_verified':False,'new_art_created':False}

def main():
 directory=OUT/'prepared_v1';need(not directory.exists(),'New output only');need(digest(SOURCE)==SHA,'Unsupported BIN')
 with SOURCE.open('rb')as f:
  d=DiscReader(f,SOURCE.stat().st_size);r=next(r for r in d.inspect()['files']if r['name']=='PL00_U.ARC;1');data=d.read(r['lba'],r['size'])
 result,verification=patch(data);directory.mkdir();p=directory/'PL00_U.ARC';p.write_bytes(result)
 proposal={'project':'ver_rin_nana','baseline':SOURCE.relative_to(ROOT).as_posix(),'baseline_sha256':SHA,'files':{'PL00_U.ARC':{'path':p.relative_to(ROOT).as_posix(),'before':sha(data),'after':sha(result),'size':len(result),'record':r,'changed_bytes':sum(x!=y for x,y in zip(data,result))}},'verification':'work/sprite_reaudit_20261106/nana/prepared_v1/verification.json','runtime_verified':False}
 write(directory/'proposal.json',proposal);write(directory/'verification.json',verification)
 before,after=Archive(data),Archive(result)
 rows=[]
 for ref,mask in((120,2),(124,2),(141,8),(142,8)):
  rows.append((f'ref {ref} mask {mask:X}',[('before',before.composite(ref,mask)[0]),('after',after.composite(ref,mask)[0]),('full before',before.composite(ref,15)[0]),('full after',after.composite(ref,15)[0])]))
 grid(rows,directory/'comparison.png',4);need(digest(SOURCE)==SHA,'Source changed');print(json.dumps({'path':proposal['files']['PL00_U.ARC']['path'],'sha':sha(result),'checks':verification['mask_checks'],'changed_composites':len(verification['changed_composites'])}),flush=True)
if __name__=='__main__':main()
