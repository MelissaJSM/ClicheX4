"""Existing source art -> bounded native detail candidate. No BIN/pointer writes."""
from preview_restore import *
from src.psx_player import decode_stream,indexed_atlas,composition_frame,bank_offsets
from src.psx_ui_atlas import local_composition
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank
from scripts.prepare_riko_ui import replace_entry

EXPECTED_ARCS={'PL00_U.ARC':'18be60ea9e6745abf2309611cc9617e76acda4ebd984f7abf2995c457ec06908','PL02_U.ARC':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa'}
RESERVED={105,*range(175,183)}
REGISTRATION_SHA='369d84b35f3d667aea8b8867c3c8c7cb38dba1988a9c2d6dc8150161afc6d200'

def validate_registration(manifest_bytes=None,overrides=None):
 raw=(OUT/'registration_inputs.json').read_bytes()if manifest_bytes is None else manifest_bytes
 need(sha(raw)==REGISTRATION_SHA,'Unsupported registration manifest')
 for name,expected in json.loads(raw)['files'].items():
  actual=overrides[name]if overrides is not None and name in overrides else(OUT/name).read_bytes()
  need(sha(actual)==expected,'Registered source/target changed: '+name)

def build_candidate(original,name):
 need(name in EXPECTED_ARCS and sha(original)==EXPECTED_ARCS[name],'Unsupported ARC');validate_registration();a=Archive(original);targets,sources=requests(a,name);result,raw,counts,streams,repack=native_write(a,targets)
 return result,a,targets,raw,counts,streams,repack,sources

def mirror_world(v,total):
 r=np.zeros_like(v);y,x=np.nonzero(v);nx=total-(x-160)+160;need(np.all((nx>=0)&(nx<384)),'Mirror overflow');r[y,nx]=v[y,x];return r

def requests(a,name):
 targets={};proof=[]
 if name=='PL00_U.ARC':
  for q in json.loads((OUT/'fourth_registration_v1.json').read_text('utf8'))['changes']:
   n=q['ref'];old=a.layer(n,8)[0];target=np.array(Image.open(OUT/f'fourth_target_{n:03}.png'));need(np.array_equal(old>0,target>0),'Leg alpha changed');targets[n,8]=target
   alias,total={144:(145,-1),146:(147,0),149:(148,0),151:(152,0)}[n]
   need(np.array_equal(mirror_world(old,total),a.layer(alias,8)[0]),f'Mirror source drift {n}/{alias}');targets[alias,8]=mirror_world(target,total)
   if n==149:
    for extra in(150,155):
     need(np.array_equal(a.layer(extra,8)[0],old),f'Shooting leg source drift {extra}');targets[extra,8]=target.copy()
   proof.append({'canonical':n,'registered_changes':q['changed_pixels'],'source_sha256':q['source_sha256']})
 else:
  for q in json.loads((OUT/'ultimate_registration_v1.json').read_text('utf8'))['changes']:
   n=q['ref'];old=merged(a,n);new=np.array(Image.open(OUT/f'ultimate_target_{n:03}.png'));ys,xs=np.nonzero(new!=old);refs=[n,n+1]+([73,74]if n==71 else[])
   for ref in refs:
    same_visible=merged(a,ref)[ys,xs]==old[ys,xs]
    for pb in(0,5):
     arr=a.layer(ref,pb)[0];target=arr.copy();permitted=np.isin(arr,(5,6,7,8,9));sel=permitted[ys,xs]&same_visible;target[ys[sel],xs[sel]]=new[ys[sel],xs[sel]];targets[ref,pb]=target
   proof.append({'canonical':n,'refs':refs,'registered_changes':q['changed_pixels'],'source_sha256':q['source_sha256']})
 return targets,proof

def native_write(a,targets):
 bystream={};counts=[]
 for(n,pb),target in targets.items():
  old=a.layer(n,pb)[0];need(np.array_equal(old>0,target>0),'Layer alpha mutation');changed=np.argwhere(target!=old);f=a.banks[0]['frames'][n];off=f['offset']
  if off not in bystream:
   raw=decode_stream(a.g,off,f['limit'],f['tile_count']*128).data;bystream[off]={'frame':f,'raw':raw,'locations':indexed_atlas(raw,f['tile_count'])[1],'edits':{}}
  rec=bystream[off];raw,locations=rec['raw'],rec['locations'];cp=composition_frame(a.c,pb,n)
  if pb!=0:cp=local_composition(cp)
  for y,x in changed:
   wx,wy=int(x-160),int(y-160);visible=None
   for p in cp['parts']:
    dx,dy=wx-p['x'],wy-p['y']
    if not(0<=dx<16 and 0<=dy<16):continue
    if p['flip_x']:dx=15-dx
    if p['flip_y']:dy=15-dy
    t=p['tile'];at,shift=locations[(t//16*16+dy)*256+t%16*16+dx];v=raw[at]>>shift&15
    if v:visible=(at,shift,v)
   need(visible is not None and visible[2]==int(old[y,x]),f'Inverse texture lookup {n}/{pb}/{wx}/{wy}');at,shift,_=visible;k=(at,shift);v=int(target[y,x]);need(k not in rec['edits']or rec['edits'][k]==v,f'Native shared texel conflict {n}/{pb}/{k}');rec['edits'][k]=v
  counts.append({'ref':n,'parts_bank':pb,'changed_pixels':len(changed)})
 replacements={};expectedraw={};streamproof=[]
 for off,rec in bystream.items():
  raw=bytearray(rec['raw'])
  for(at,shift),v in rec['edits'].items():raw[at]=raw[at]&~(15<<shift)|v<<shift
  raw=bytes(raw);f=rec['frame'];code=encode_stream(raw);refs=[q['index']for q in a.banks[0]['frames']if q['offset']==off]
  for n in refs:
   need(any(k[0]==n for k in targets),f'Unselected stream alias {n}');replacements[n]=code;expectedraw[n]=raw
  streamproof.append({'refs':refs,'before':sha(rec['raw']),'after':sha(raw),'changed_texels':len(rec['edits']),'tile_count':f['tile_count'],'encoded_bytes':len(code)})
 # A single bounded repack keeps every alias and all other encoded streams.
 ng,repack=repack_graphics_bank(a.g,0,replacements);need(bank_offsets(ng,allow_aliases=True)==bank_offsets(a.g,allow_aliases=True),'Bank boundary changed')
 return replace_entry(a.data,2,ng),expectedraw,counts,streamproof,repack

def verify(a,b,targets,expectedraw):
 need(len(a.data)==len(b.data),'ARC length');need(replace_entry(b.data,2,a.g)==a.data,'Non-gfx entry changed')
 offsets=bank_offsets(a.g,allow_aliases=True);need(offsets==bank_offsets(b.g,allow_aliases=True),'Bank boundaries');need(a.g[offsets[1]:]==b.g[offsets[1]:],'Other graphics banks')
 rawchecks=0;layers=0;masks=0;visible=0;alpha=0;changedrefs=[]
 for bi,(ab,bb)in enumerate(zip(a.banks,b.banks)):
  for n,(af,bf)in enumerate(zip(ab['frames'],bb['frames'])):
   need(af['tile_count']==bf['tile_count']<=32 if bi==0 else af['tile_count']==bf['tile_count'],'Tile count')
   ar=decode_stream(a.g,af['offset'],af['limit'],af['tile_count']*128).data;br=decode_stream(b.g,bf['offset'],bf['limit'],bf['tile_count']*128).data
   expected=expectedraw.get(n,ar)if bi==0 else ar;need(expected==br,f'Raw regression {bi}/{n}');rawchecks+=1
 for n in range(237):
  if n in RESERVED:continue
  exp={}
  for pb in(0,5,6,7,8):
   old=a.layer(n,pb)[0];new=b.layer(n,pb)[0];expected=targets.get((n,pb),old);diff=np.argwhere(new!=expected)
   need(not len(diff),f'Layer regression {n}/{pb}: '+str(diff[:8].tolist()));need(np.array_equal(old>0,new>0),'Layer alpha');exp[pb]=expected;layers+=1
  nchanged=False
  for arm in(1,2):
   for mask in range(16):
    before=a.composite(n,mask,arm)[0];actual=b.composite(n,mask,arm)[0];expected=a.rgba(exp[0])
    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
     if mask&bit:expected.alpha_composite(a.rgba(exp[pb],32 if pb==7 and arm==2 else 16))
    need(actual.tobytes()==expected.tobytes(),f'Composition {n}/{mask}/{arm}');need(before.getchannel('A').tobytes()==actual.getchannel('A').tobytes(),'Full alpha');masks+=1;alpha+=1
    if before.tobytes()!=actual.tobytes():visible+=1;nchanged=True
  if nchanged:changedrefs.append(n)
 gpu=0;edges=[]
 for n in sorted(expectedraw):
  af,bf=a.banks[0]['frames'][n],b.banks[0]['frames'][n];ar=decode_stream(a.g,af['offset'],af['limit'],af['tile_count']*128).data;br=expectedraw[n]
  aa=np.frombuffer(indexed_atlas(ar,af['tile_count'])[0],np.uint8).reshape(-1,256);ba=np.frombuffer(indexed_atlas(br,bf['tile_count'])[0],np.uint8).reshape(-1,256)
  for pb in(0,5,6,7,8):
   for p in composition_frame(a.c,pb,n)['parts']:
    t=p['tile'];old=aa[t//16*16:t//16*16+16,t%16*16:t%16*16+16];new=ba[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    if t%16==0:need(np.array_equal(old[:,0],new[:,0]),f'GPU first column {n}/{pb}/{t}')
    if p['flip_y']and t//16%16==0:need(np.array_equal(old[0],new[0]),f'GPU flipY first row {n}/{pb}/{t}')
    gpu+=1
 return {'passed':True,'raw_references':rawchecks,'layers':layers,'mask_arm_combinations':masks,'changed_combinations':visible,'visible_refs':changedrefs,'full_alpha_checks':alpha,'gpu_parts':gpu,'palette_parts_audio_timing_exact':True,'all_unselected_raw_and_layers_exact':True,'tile_counts_and_bank_boundaries_exact':True,'runtime_verified':False}

def main():
 destination=OUT/'prepared_v1';need(not destination.exists(),'Fresh candidate directory required');assets,records=data();results={};proposal={'project':'ver_rin_nana','baseline':SOURCE.relative_to(ROOT).as_posix(),'baseline_sha256':EXPECTED,'files':{},'candidate_only':True,'runtime_verified':False,'new_art_generated':False}
 for name,original in assets.items():
  print('Preparing '+name,flush=True)
  result,a,targets,raw,counts,streams,repack,sources=build_candidate(original,name);b=Archive(result);report=verify(a,b,targets,raw);report.update(sources=sources,layers_changed=counts,streams=streams,repack=repack,before=sha(original),after=sha(result));results[name]=(result,report,a,b)
 destination.mkdir()
 for name,(result,report,a,b)in results.items():
  path=destination/name;path.write_bytes(result);write(destination/(name+'.verification.json'),report);proposal['files'][name]={'path':path.relative_to(ROOT).as_posix(),'before':sha(a.data),'after':sha(result),'size':len(result),'record':records[name]}
  refs=report['visible_refs'];lines=[]
  forms=[(15,'포스')]if name=='PL00_U.ARC'else[(15,'재킷'),(0,'수영복')]
  for mask,title in forms:
   for ref in refs:
    lines.append((f'{title} {ref}',[('idle',a.composite(0,mask)[0]),('현재',a.composite(ref,mask)[0]),('원화 복원 후보',b.composite(ref,mask)[0])]))
   for start in range(0,len(lines),6):helper.grid(lines[start:start+6],destination/f'{name}_{title}_{start//6:02}.png',4)
   lines=[]
 write(destination/'proposal.json',proposal);need(digest(SOURCE)==EXPECTED,'Parent changed');print(json.dumps({n:{'sha256':sha(r[0]),'checks':r[1]['mask_arm_combinations'],'refs':r[1]['visible_refs']}for n,r in results.items()}),flush=True)

if __name__=='__main__':main()
