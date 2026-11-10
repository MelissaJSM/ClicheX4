"""Pack the current approved-registration targets into a bounded Zero ARC copy."""
from pathlib import Path
from collections import defaultdict
import sys,struct,json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;A=D/'rear_registered_v1';OUT=D/'prepared_rear_v1'
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas,bank_offsets
from src.psx_frame_edit import frame_coverage,read_indexed_png
from src.psx_compress import encode_stream
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def edit_visible_set(raw,count,edits):
 writes={};_,locations,_=indexed_atlas(raw,count);forbidden=set()
 for cp,_,_ in edits:
  for p in cp['parts']:
   t=p['tile'];oy,ox=t//16*16,t%16*16
   if t%16==0:
    for yy in range(16):forbidden.add(locations[(oy+yy)*256+ox])
   if p['flip_y']and t//16%16==0:
    for xx in range(16):forbidden.add(locations[oy*256+ox+xx])
 for cp,want,size in edits:
  actual,oldsize,_,_=compose_indices(raw,count,cp);need(tuple(size)==oldsize,'Composition size');cov,_,_=frame_coverage(raw,count,cp)
  for index,(oldvalue,newvalue)in enumerate(zip(actual,want)):
   if oldvalue==newvalue:continue
   sources=list(dict.fromkeys(cov[index]));need(bool(sources),'No texture coverage');visible=[s for s in sources if(raw[s[0]]>>s[1])&15]
   if newvalue==0:chosen=visible
   elif visible:chosen=[visible[-1]]
   else:
    allowed=[s for s in sources if s not in forbidden];need(bool(allowed),'Only forbidden GPU source for new alpha');chosen=[allowed[-1]]
   for s in chosen:need(s not in writes or writes[s]==newvalue,'Shared visible texel conflict');writes[s]=newvalue
 result=bytearray(raw)
 for(pos,shift),value in writes.items():result[pos]=(result[pos]&~(15<<shift))|(value<<shift)
 result=bytes(result)
 for cp,want,size in edits:
  got,sz,_,_=compose_indices(result,count,cp);need(got==want and sz==tuple(size),'Visible edit readback conflict')
 return result
def repack_raw(g,b,replacements):
 bank=graphics_bank(g,b);groups=defaultdict(list)
 for f in bank['frames']:groups[f['offset']].append(f)
 codes={};keys={};expected={};splits=[];old_size=0
 for off,frames in groups.items():
  f=frames[0];d=decode_stream(g,off,f['limit'],f['tile_count']*128);old_size+=d.end-off;variants=set()
  for r in frames:
   raw=replacements.get(r['index'],d.data);need(len(raw)==r['tile_count']*128,'Size drift');key=(off,sha(raw));keys[r['index']]=key;expected[r['index']]=raw;variants.add(key)
   if key not in codes:codes[key]=bytes(g[off:d.end])if raw==d.data else encode_stream(raw)
  if len(variants)>1:splits.append({'refs':[r['index']for r in frames],'variants':len(variants)})
 cursor=bank['base']+4*len(bank['frames']);locations={}
 for key,code in sorted(codes.items()):locations[key]=cursor;cursor+=len(code)
 need(cursor<=bank['end'],'Bank capacity');need(locations[keys[0]]==bank['base']+4*len(bank['frames']),'Sentinel drift');result=bytearray(g)
 for key,code in codes.items():pos=locations[key];result[pos:pos+len(code)]=code
 for f in bank['frames']:struct.pack_into('<I',result,bank['base']+f['index']*4,f['tile_count']<<20|locations[keys[f['index']]]-bank['base'])
 result=bytes(result);need(result[:bank['base']]==g[:bank['base']]and result[bank['end']:]==g[bank['end']:],'Bank escaped')
 for f in graphics_bank(result,b)['frames']:need(decode_stream(result,f['offset'],f['limit'],f['tile_count']*128).data==expected[f['index']],'Repacked stream differs')
 return result,{'bank':b,'old_slack':bank['end']-bank['base']-4*len(bank['frames'])-old_size,'remaining_slack':bank['end']-cursor,'split_groups':splits,'bank_boundaries_exact':True}
def build(arc,targets,reg):
 need(sha(arc)=='118f04c93c716a36138f903c32d260be2ffa3c6c951cf4993ea93b1f48d249da','Parent ARC');need(set(targets)=={r['id']for r in reg['frames']},'Target references');g,c=entry(arc,2),entry(arc,3);ng=g;reports=[];edges=[]
 pal=struct.unpack_from('<16H',entry(arc,9));pixels,size=read_indexed_png(A/'head_registered.png',pal);need(size==(32,32),'Native head dimensions');head=np.frombuffer(pixels,np.uint8).reshape(32,32);metadata=json.loads((D/'rear_head_inputs/inputs.json').read_text('utf8'));old=np.array(Image.open(ROOT/'work/ver_buki_riko/art_pilot/ladder_v1/rear_head_indexed.png'));mask=np.zeros_like(old,bool)
 for y,(x0,x1)in metadata['rear_old_head_spans'].items():mask[int(y),x0:x1]=old[int(y),x0:x1]>0
 for r in reg['frames']:
  before=render(arc,r['bank'],r['parts_bank'],r['ref'])[0];mirror=r['view']=='rear_mirrored';x,y=r['old_template_origin_world'];ox,oy=r['new_grid_origin_world'];owned=np.zeros_like(before,bool);owned[160+y:160+y+19,160+x:160+x+23]=np.fliplr(mask)if mirror else mask;protected=(before>0)&~owned;fresh=np.zeros_like(before);fresh[160+oy:160+oy+32,160+ox:160+ox+32]=np.fliplr(head)if mirror else head;visible=(fresh>0)&~protected;expected=before.copy();expected[owned]=0;expected[visible]=fresh[visible];need(np.array_equal(expected,targets[r['id']]),'Target differs from authored head or protected body')
 for b in(0,1):
  bank=graphics_bank(g,b);groups=defaultdict(list);replacements={}
  for f in bank['frames']:groups[f['offset']].append(f)
  for off,refs in groups.items():
   selected=[r for r in refs if f'b{b}_{r["index"]:03d}'in targets]
   if not selected:continue
   f=refs[0];raw=decode_stream(g,off,f['limit'],f['tile_count']*128).data;edits=[]
   for q in selected:
    n=q['index'];cp=composition_frame(c,0 if b==0 else 5,n);_,size,bb,_=compose_indices(raw,q['tile_count'],cp);target=targets[f'b{b}_{n:03d}'];edit=target[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]];edits.append((cp,edit.tobytes(),size))
   new=edit_visible_set(raw,f['tile_count'],edits);oldatlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);newatlas=np.frombuffer(indexed_atlas(new,f['tile_count'])[0],np.uint8).reshape(-1,256)
   for q in selected:
    n=q['index'];cp=composition_frame(c,0 if b==0 else 5,n)
    for p in cp['parts']:
     tile=p['tile'];oy,ox=tile//16*16,tile%16*16;oldtile=oldatlas[oy:oy+16,ox:ox+16];newtile=newatlas[oy:oy+16,ox:ox+16]
     if tile%16==0:need(not np.any((oldtile[:,0]==0)&(newtile[:,0]>0)),f'New GPU first-column alpha {b}/{n}/{tile}')
     if p['flip_y']and tile//16%16==0:need(not np.any((oldtile[0]==0)&(newtile[0]>0)),f'New GPU flipped first-row alpha {b}/{n}/{tile}')
    replacements[n]=new
   edges.append({'bank':b,'selected':[q['index']for q in selected],'shared':[q['index']for q in refs],'native_changed_bytes':sum(x!=y for x,y in zip(raw,new))})
  ng,layout=repack_raw(ng,b,replacements);reports.append(layout)
 out=replace_entry(arc,2,ng);need(replace_entry(out,2,g)==arc,'Other entries');need(bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True),'Bank offsets');raws=displays=unchanged_raw=unchanged_display=0;changes=[]
 for b in(0,1):
  ob,nb=graphics_bank(g,b),graphics_bank(ng,b)
  for of,nf in zip(ob['frames'],nb['frames']):
   n=of['index'];key=f'b{b}_{n:03d}';need(of['tile_count']==nf['tile_count']<=32,'Tile count');ar=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data;br=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;raws+=1
   if key not in targets:need(ar==br,'Non-target raw '+key);unchanged_raw+=1
   if b==1 and 42<=n<=49:continue
   before=render(arc,b,0 if b==0 else 5,n)[0];after=render(out,b,0 if b==0 else 5,n)[0];want=targets.get(key,before);need(np.array_equal(after,want),'Display mismatch '+key);displays+=1;unchanged_display+=key not in targets
   if key in targets:changes.append({'id':key,'changed_pixels':int(np.count_nonzero(before!=after))})
 return out,{'all_raw_references':raws,'non_target_raw_exact':unchanged_raw,'displayed_references':displays,'non_target_display_exact':unchanged_display,'partial8_raw_exact':True,'existing_3rd_saber9_exact':True,'geometry_palette_audio_other_entries_exact':True,'new_gpu_boundary_alpha':0,'tile_counts_exact':True,'groups':edges,'banks':reports,'changes':changes}
def main():
 arc=(D/'prepared_v1/PL01_U.ARC').read_bytes();reg=json.loads((A/'registration.json').read_text('utf8'));need(sha((ROOT/reg['source_image']).read_bytes())==reg['source_sha256'],'Generated art changed');need(sha((A/'head_registered.png').read_bytes())==reg['indexed_head_sha256'],'Native head changed');need(sha((A/'targets.npz').read_bytes())==reg['targets_sha256'],'Target file changed');data=np.load(A/'targets.npz');targets={k:data[k]for k in data.files};out,proof=build(arc,targets,reg);again,_=build(arc,targets,reg);need(again==out,'Reproduction drift');rejected=[]
 for case in('parent','missing_reference','palette_index','body_pixel'):
  aa=arc;tt={k:v.copy()for k,v in targets.items()}
  if case=='parent':aa=bytes([arc[0]^1])+arc[1:]
  elif case=='missing_reference':tt.pop('b0_160')
  elif case=='palette_index':tt['b0_160'][144,148]=16
  else:tt['b0_160'][180,140]=15
  try:build(aa,tt,reg)
  except ValueError as exc:rejected.append({'case':case,'reason':str(exc)})
  else:raise ValueError('Rejected-input check accepted '+case)
 OUT.mkdir(exist_ok=True);(OUT/'PL01_U.ARC').write_bytes(out);report={'source_arc':str((D/'prepared_v1/PL01_U.ARC').relative_to(ROOT)),'source_arc_sha256':sha(arc),'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':sha(out),'registration':str((A/'registration.json').relative_to(ROOT)),'registration_sha256':sha((A/'registration.json').read_bytes()),'reproducible':True,'rejection_tests':rejected,'verification':proof,'new_art_rear_refs':28,'preserved_source_art_restore_refs':9,'game_bin_written':False,'runtime_verified':False,'visual_acceptance_required':True};(OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'arc_sha256':sha(out),'proof':{k:v for k,v in proof.items()if k not in('groups','changes')}}))
if __name__=='__main__':main()
