"""Apply source-authored calf material to Nana95/96 without new art or BIN writes."""
from frost_material import *
EXPECTED_ARC='f20b5921ae3b87d6fbd89e1fac0f7dd4141385b83df0ec632113537b23f5444b'
def need(ok,msg):
 if not ok:raise ValueError(msg)
def patch(data):
 need(sha(data)==EXPECTED_ARC,'Unsupported ARC')
 meta=json.loads((OUT/'frost/material_v2.json').read_text('utf8'));need(meta['parent_sha256']==SHA and meta['changed_count']==36,'Unsupported source registration')
 authored=np.array(Image.open(OUT/'frost/authored_095_indices.png'));need(sha(authored.tobytes())==meta['reused_authored_indexed_sha256'],'Authored source changed')
 before=Archive(data);g,c=before.g,before.c;f=before.banks[0]['frames'][95];need([q['index']for q in before.banks[0]['frames']if q['offset']==f['offset']]==[95,96],'Unexpected shared stream')
 need(np.all(before.words[10:14]==before.words[26:30]),'Flesh palettes differ')
 raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;new=raw;edits={};layerproof=[];texel_edits={};_,locations,_=indexed_atlas(raw,f['tile_count'])
 for n in(95,96):
  delta=n-95;edits[n]=[]
  for q in meta['changes']:
   x,y=q['world'];sx,sy=q['authored_world'];need(int(authored[sy+160,sx+160])==q['after']and q['after']in(10,11,12,13),'Missing authored shade')
   edits[n].append((x+delta,y,q['before'],q['after']))
  for b in(0,5):
   old,_=before.layer(n,b);target=old.copy();count=0
   for x,y,color0,color1 in edits[n]:
    current=int(old[y+160,x+160])
    if not current:need(b==5,'Base pixel missing');continue
    need(current in(1,2,3,4),'Material unexpectedly not dark');target[y+160,x+160]=color1;count+=1
   cp=local_composition(composition_frame(c,b,n))
   for x,y,_,color1 in edits[n]:
    if not old[y+160,x+160]:continue
    visible=None
    for part in cp['parts']:
     dx,dy=x-part['x'],y-part['y']
     if not(0<=dx<16 and 0<=dy<16):continue
     if part['flip_x']:dx=15-dx
     if part['flip_y']:dy=15-dy
     t=part['tile'];at,shift=locations[(t//16*16+dy)*256+t%16*16+dx];value=raw[at]>>shift&15
     if value:visible=(at,shift,value)
    need(visible is not None and visible[2]==old[y+160,x+160],'Visible texel mismatch');at,shift,_=visible;key=(at,shift)
    need(key not in texel_edits or texel_edits[key]==color1,'Shared texel material conflict');texel_edits[key]=color1
   layerproof.append({'ref':n,'bank':b,'changed_pixels':count})
 nr=bytearray(raw)
 for(at,shift),value in texel_edits.items():nr[at]=(nr[at]&~(15<<shift))|(value<<shift)
 new=bytes(nr)
 code=encode_stream(new)
 if len(code)<=f['limit']-f['offset']:ng,compression=replace_stream(g,f,new,allocated_limit=f['limit'])
 else:ng,compression=repack_graphics_bank(g,0,{95:code,96:code})
 result=replace_entry(data,2,ng);after=Archive(result)
 for n in(95,96):
  for b in(0,5):
   old=before.layer(n,b)[0];expected=old.copy()
   for x,y,_,color in edits[n]:
    if old[y+160,x+160]>0:expected[y+160,x+160]=color
   actual=after.layer(n,b)[0]
   need(np.array_equal(actual,expected),f'Early layer regression {n}/{b}: '+str([[int(x-160),int(y-160),int(expected[y,x]),int(actual[y,x])]for y,x in np.argwhere(actual!=expected)[:30]]))
 need(replace_entry(result,2,g)==data,'Other entry changed');need(bank_offsets(ng,allow_aliases=True)==bank_offsets(g,allow_aliases=True),'Graphics boundary changed');gs=bank_offsets(g,allow_aliases=True);need(ng[gs[1]:]==g[gs[1]:],'Other graphics bank changed')
 rawchecks=0
 for b,(ob,nb)in enumerate(zip(before.banks,after.banks)):
  for n,(of,nf)in enumerate(zip(ob['frames'],nb['frames'])):
   need(of['tile_count']==nf['tile_count'],'Tile count changed')
   oldraw=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data;newraw=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
   need(newraw==(new if b==0 and n in(95,96)else oldraw),f'Raw regression {b}/{n}');rawchecks+=1
 layerchecks=0;maskchecks=0;changedmask=0
 for n in range(237):
  if n in(105,*range(175,183)):continue
  for b in(0,5,6,7,8):
   old,_=before.layer(n,b);actual,_=after.layer(n,b);expected=old.copy()
   if n in edits and b in(0,5):
    for x,y,_,color in edits[n]:
     if old[y+160,x+160]>0:expected[y+160,x+160]=color
   need(np.array_equal(actual,expected),f'Layer regression {n}/{b}: '+str([[int(x-160),int(y-160),int(expected[y,x]),int(actual[y,x])]for y,x in np.argwhere(actual!=expected)[:20]]));need(np.array_equal(old>0,actual>0),'Layer alpha changed');layerchecks+=1
  for arm in(1,2):
   for mask in range(16):
    old=before.composite(n,mask,arm)[0];actual=after.composite(n,mask,arm)[0];expected=np.array(old)
    if n in edits:
     for x,y,_,color in edits[n]:expected[y+160,x+160]=np.asarray(before.rgba(np.array([[color]],np.uint8)))[0,0]
    need(np.array_equal(np.asarray(actual),expected),f'Mask regression {n}/{mask}/{arm}');maskchecks+=1;changedmask+=actual.tobytes()!=old.tobytes()
 gpu=0;preserved=[]
 for n in(95,96):
  of=before.banks[0]['frames'][n];nf=after.banks[0]['frames'][n];oa=np.frombuffer(indexed_atlas(decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data,of['tile_count'])[0],np.uint8).reshape(-1,256);na=np.frombuffer(indexed_atlas(new,nf['tile_count'])[0],np.uint8).reshape(-1,256)
  for b in(0,5,6,7,8):
   for p in composition_frame(c,b,n)['parts']:
    t=p['tile'];np_=na[t//16*16:t//16*16+16,t%16*16:t%16*16+16];op=oa[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    if(t%16==0 and np_[:,0].any())or(p['flip_y']and t//16%16==0 and np_[0].any()):need(np.array_equal(op,np_),'Changed GPU edge');preserved.append({'ref':n,'bank':b,'tile':t})
    gpu+=1
 return result,{'edits':edits,'source_manifest_sha256':digest(OUT/'frost/material_v2.json'),'source_indexed_sha256':sha(authored.tobytes()),'source_generated_sha256':meta['source_sha256'],'layers_changed':layerproof,'native_texels_changed':len(texel_edits),'native_write_method':'only final visible nonzero texel for selected world pixels; no full-tile repaint','raw_checks':rawchecks,'layer_checks':layerchecks,'mask_checks':maskchecks,'changed_mask_checks':changedmask,'alpha_and_coordinates_exact':True,'all_palettes_audio_compositions_exact':True,'other_frames_exact':True,'gpu_parts_checked':gpu,'existing_gpu_edges_preserved':preserved,'compression':compression,'runtime_verified':False,'new_art_generated':False}
def main():
 directory=OUT/'prepared_frost_v1';need(not directory.exists(),'New output only');need(digest(SOURCE)==SHA,'Unsupported BIN')
 with SOURCE.open('rb')as f:
  d=DiscReader(f,SOURCE.stat().st_size);r=next(r for r in d.inspect()['files']if r['name']=='PL02_U.ARC;1');data=d.read(r['lba'],r['size'])
 result,proof=patch(data);directory.mkdir();p=directory/'PL02_U.ARC';p.write_bytes(result);write(directory/'verification.json',proof)
 proposal={'project':'ver_rin_nana','baseline':SOURCE.relative_to(ROOT).as_posix(),'baseline_sha256':SHA,'files':{'PL02_U.ARC':{'path':p.relative_to(ROOT).as_posix(),'before':sha(data),'after':sha(result),'size':len(result),'record':r}},'runtime_verified':False};write(directory/'proposal.json',proposal)
 old,new=Archive(data),Archive(result);rows=[]
 for n in(95,96):
  for mask,label in((15,'jacket'),(0,'swimsuit')):rows.append((f'{label} ref{n}',[('idle',old.composite(0,mask)[0]),('before',old.composite(n,mask)[0]),('after',new.composite(n,mask)[0])]))
 grid(rows,directory/'comparison.png',5);need(digest(SOURCE)==SHA,'Source changed');print(json.dumps({'path':proposal['files']['PL02_U.ARC']['path'],'sha':sha(result),'mask_checks':proof['mask_checks']}),flush=True)
if __name__=='__main__':main()
