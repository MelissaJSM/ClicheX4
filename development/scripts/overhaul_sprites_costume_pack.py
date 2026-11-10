"""C03 base-only packing with immutable armor-tile reuse and exact checks."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import D,entry,render,sha,write
from scripts.overhaul_sprites_costume import full
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import graphics_bank,composition_frame,decode_stream,bank_offsets,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
import scripts.prepare_shibuki_ultimate_production as layout

def bounded_grid_fit(mask,count):
    """Bound the preview pack search instead of an unbounded rectangle solver."""
    y,x=np.nonzero(mask)
    if not len(x):return []
    if len(x)>count*256:return None
    best=None
    for dy in range(16):
        for dx in range(16):
            cells=sorted(set(zip(((x-dx)//16).tolist(),((y-dy)//16).tolist())))
            if len(cells)>count:continue
            rr=[[max(0,min(mask.shape[1]-16,tx*16+dx)),max(0,min(mask.shape[0]-16,ty*16+dy))]for tx,ty in cells]
            if best is None or len(rr)<len(best):best=rr
    return best

layout.fast_fit=layout.remaining.fit=layout.motion.fit=bounded_grid_fit

def resize_tile_storage(raw,old_count,new_count):
    if not 0<old_count<=32 or not 0<new_count<=32:raise ValueError('Player buffer is 32 tiles')
    if old_count==new_count:return raw
    atlas,_,_=indexed_atlas(raw,old_count);new=bytearray(new_count*128);_,mapping,_=indexed_atlas(bytes(new),new_count)
    for t in range(min(old_count,new_count)):
        for y in range(16):
            for x in range(16):
                i=(t//16*16+y)*256+t%16*16+x;pos,shift=mapping[i];new[pos]|=atlas[i]<<shift
    return bytes(new)

def repack_variable(g,replacements,counts):
    bank=graphics_bank(g,0,allow_bank_aliases=True);groups={};codes={};expected={};newcounts={};oldbytes=0;frame_keys={};splits=[]
    for f in bank['frames']:groups.setdefault(f['offset'],[]).append(f)
    for off,refs in groups.items():
        f=refs[0];old=decode_stream(g,off,f['limit'],f['tile_count']*128);selected=[q for q in refs if q['index']in replacements]
        if selected and len(selected)!=len(refs):raise ValueError('Incomplete stream selection')
        variants=set();oldbytes+=old.end-off
        for q in refs:
            count=counts[q['index']]if selected else q['tile_count'];raw=replacements[q['index']]if selected else old.data
            if not 0<count<=32:raise ValueError('Decompression buffer overflow')
            if len(raw)!=count*128:raise ValueError('Decoded stream length differs')
            key=(off,sha(raw),count);variants.add(key);frame_keys[q['index']]=key
            if key not in codes:
                code=encode_stream(raw)if selected else g[off:old.end];codes[key]=code
                if decode_stream(code,0,len(code),count*128).data!=raw:raise ValueError('Encoding differs')
            expected[q['index']]=raw;newcounts[q['index']]=count
        if len(variants)>1:splits.append({'old_offset':off,'frames':[q['index']for q in refs],'streams':len(variants)})
    cursor=bank['base']+len(bank['frames'])*4;locations={}
    for key,code in sorted(codes.items()):locations[key]=cursor;cursor+=len(code)
    if cursor>bank['end']:raise ValueError(f'Graphics bank exceeds capacity by {cursor-bank["end"]}')
    result=bytearray(g)
    for key,code in codes.items():start=locations[key];result[start:start+len(code)]=code
    for f in bank['frames']:struct.pack_into('<I',result,bank['base']+f['index']*4,newcounts[f['index']]<<20|locations[frame_keys[f['index']]]-bank['base'])
    result=bytes(result)
    if result[:bank['base']]!=g[:bank['base']]or result[bank['end']:]!=g[bank['end']:]:raise ValueError('Other graphics bank changed')
    for f in graphics_bank(result,0,allow_bank_aliases=True)['frames']:
        if f['tile_count']!=newcounts[f['index']]or decode_stream(result,f['offset'],f['limit'],f['tile_count']*128).data!=expected[f['index']]:raise ValueError('Variable packing readback differs')
    return result,{'bank':0,'original_slack':bank['end']-bank['base']-len(bank['frames'])*4-oldbytes,'remaining_slack':bank['end']-cursor,'changed_tile_counts':{n:count for n,count in newcounts.items()if count!=bank['frames'][n]['tile_count']},'split_streams':splits,'max_tiles':max(newcounts.values()),'buffer_bytes':4096,'bank_boundaries_preserved':True}

def immutable_parts(raw,count,c,n,target,ladder_background=False):
    options=[];seen=set()
    for b in(0,5,6,7,8):
        if b!=0 and not 184<=n<=203:continue
        composition=composition_frame(c,b,n)
        if b!=0:composition=local_composition(composition)
        for p in composition['parts']:
            ladder_head=ladder_background and b==0 and n in(148,149,150)and p['index']<3
            if b==0 and p['clut']==0 and not ((n in(73,74) and p['tile']==6)or ladder_head):continue
            k=(p['flags'],p['tile'],p['x'],p['y'])
            if k in seen:continue
            seen.add(k);part=canvas_from_parts(raw,count,{'parts':[p]});mask=part>0
            if np.any(mask)and(np.array_equal(part[mask],target[mask])or(ladder_head and not np.any(mask&(target==0)))):options.append((int(mask.sum()),p,part))
    covered=np.zeros_like(target,bool);fixed=[];background=np.zeros_like(target)
    for _,p,a in sorted(options,key=lambda q:-q[0]):
        added=(a>0)&~covered
        if int(added.sum())<4:continue
        fixed.append(p);covered|=a>0;background[a>0]=a[a>0]
    return fixed,np.where((background==target)&(background>0),0,target).astype(np.uint8)

def pack_planes(raw,count,images,pool,limits):
    result=raw;assignments=[[]for _ in images];free=set(pool)
    planes=sorted({int(v)//16 for image in images for v in np.unique(image)if v})
    for plane in planes:
        if plane not in(0,2):raise ValueError('Unexpected CLUT plane')
        layer=[np.where(image//16==plane,image%16,0).astype(np.uint8)for image in images]
        if not any(np.any(a)for a in layer):continue
        available=[max(1,limit-len(existing))for limit,existing in zip(limits,assignments)]
        result,records_=pack_shared(result,count,layer,free,available)
        for original,extra in zip(assignments,records_):
            original.extend((t,x,y,flag|(plane<<2))for t,x,y,flag in extra)
            free-={t for t,x,y,flag in extra}
    return result,assignments

def pack(project):
    folder=D/('nana_preultimate'if project=='ver_rin_nana'else'shibuki_preultimate');arc=(D/project/'baseline/PL02_U.ARC').read_bytes()
    g,c,pal=[entry(arc,k)for k in(2,3,9)];bank=graphics_bank(g,0,allow_bank_aliases=True)
    norm=folder/'normalized';meta=json.loads((norm/'normalization.json').read_text('utf8'))
    if sha(arc)!=meta['source_sha256']:raise ValueError('Baseline differs')
    targets={n:np.array(Image.open(norm/f'{n:03}.png'))for n in meta['frames']}
    state=folder/'state_overrides';post_targets={};shared=set()
    if (state/'state.json').exists():
        override=json.loads((state/'state.json').read_text('utf8'))
        if override['baseline_sha256']!=sha(arc):raise ValueError('State override baseline differs')
        for n in override['base_frames']:targets[n]=np.array(Image.open(state/f'base_{n:03}.png'))
        post_targets={n:np.array(Image.open(state/f'post_{n:03}.png'))for n in override['post_frames']}
        shared=set(override['shared_frames'])
    for n in(0,85):
        path=folder/f'pilot_{n:03}.png'
        if path.exists():targets[n]=np.array(Image.open(path))
    replacements={};new_counts={};changes={};post_changes={};reports=[];failures=[];groups={};applied={};cache=folder/'pack_cache_v5';cache.mkdir(exist_ok=True)
    for f in bank['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
    work_groups=[]
    for off,refs in groups.items():
        if project=='ver_buki_riko'and refs==[148,149,150]:work_groups.extend((off,[n])for n in refs)
        else:work_groups.append((off,refs))
    for off,refs in work_groups:
        if not set(refs)&set(targets):continue
        if set(refs)-set(targets):failures.append({'frames':refs,'reason':'artwork incomplete for shared stream'});continue
        f=bank['frames'][refs[0]];raw=decode_stream(g,off,f['limit'],f['tile_count']*128).data
        post_refs=[n for n in refs if n in post_targets]
        protected={q['tile']for n in refs for b in(5,6,7,8)if not(b==5 and n in post_refs)for q in composition_frame(c,b,n)['parts']};pool=set(range(f['tile_count']))-protected
        fixed=[];images=[];old_limits=[]
        for n in refs:
            t=targets[n][80:240,80:240];fs,rest=immutable_parts(raw,f['tile_count'],c,n,t,project=='ver_buki_riko');fixed.append(fs);images.append(rest);old_limits.append(len(composition_frame(c,0,n)['parts']))
        for n in post_refs:
            fixed.append([]);images.append(post_targets[n][80:240,80:240]);old_limits.append(max(6,len(composition_frame(c,0,n)['parts']),len(composition_frame(c,5,n)['parts'])))
        for fs in fixed:
            for p in fs:
                protected.add(p['tile'])
        pool=set(range(f['tile_count']))-protected
        key=sha(arc+np.stack([targets[n]for n in refs]+[post_targets[n]for n in post_refs]).tobytes()+(b'spark_tiles_protected_v6'if 71 in refs else b'')+(b'ladder_background_v1'if project=='ver_buki_riko'and 148 in refs else b''));cached=cache/f'{refs[0]:03}_{key}.json';failure=None
        if not any(np.any(t)for t in images):
            new=raw;count=f['tile_count'];assignments=[[]for _ in images]
        elif cached.exists():
            data=json.loads(cached.read_text('utf8'));count=data['count'];new=bytes.fromhex(data['raw']);assignments=data['assignments']
        else:
            count=32;expanded=resize_tile_storage(raw,f['tile_count'],count);available=set(range(count))-protected
            for extra in range(4):
                limits=[max(1,v+extra-len(fs))for v,fs in zip(old_limits,fixed)]
                try:new,assignments=pack_planes(expanded,count,images,available,limits);break
                except ValueError as error:failure=error
            else:
                failures.append({'frames':refs,'reason':str(failure),'old_parts':old_limits,'fixed_parts':list(map(len,fixed)),'pool':len(pool)});continue
            used=protected|{p['tile']for fs in fixed for p in fs}|{t for rr in assignments for t,x,y,flag in rr}
            cleared=bytearray(new);_,mapping,_=indexed_atlas(new,count)
            for t in set(range(count))-used:
                for y in range(16):
                    for x in range(16):
                        pos,shift=mapping[(t//16*16+y)*256+t%16*16+x];cleared[pos]&=~(15<<shift)
            required=max(f['tile_count'],max(used,default=0)+1);new=resize_tile_storage(bytes(cleared),count,required);count=required
            write(cached,{'count':count,'raw':new.hex(),'assignments':assignments})
        for n,fs,parts in zip(refs,fixed,assignments):
            rr=[(p['tile'],p['x']+80,p['y']+80,p['flags'])for p in fs]+parts
            if not rr:
                blank=next((p for p in composition_frame(c,0,n)['parts']if not np.any(canvas_from_parts(new,count,{'parts':[p]}))),None)
                if blank is None:raise ValueError('No preserved blank tile')
                rr=[(blank['tile'],blank['x']+80,blank['y']+80,blank['flags'])]
            changes[n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rr);replacements[n]=new;new_counts[n]=count;applied[n]=targets[n]
            cp={'parts':[{'index':i,'tile':t,'x':x-80,'y':y-80,'flags':fl,'flip_x':bool(fl&64),'flip_y':bool(fl&128),'clut':(fl>>2)&3,'page':fl&3,'unknown_flags':fl&0x30}for i,(t,x,y,fl)in enumerate(rr)]}
            if not np.array_equal(canvas_from_parts(new,count,cp),targets[n][80:240,80:240]):raise ValueError('Composed target differs')
            for b in(5,6,7,8):
                if b==5 and n in post_refs:continue
                cp=local_composition(composition_frame(c,b,n))
                if not np.array_equal(canvas_from_parts(raw,f['tile_count'],cp),canvas_from_parts(new,count,cp)):raise ValueError('Armor layer changed')
        for n,rr in zip(post_refs,assignments[len(refs):]):
            post_changes[n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rr)
        reports.append({'frames':refs,'fixed_parts':list(map(len,fixed)),'parts':[len(fs)+len(rr)for fs,rr in zip(fixed,assignments)],'original_parts':old_limits,'original_tile_count':f['tile_count'],'tile_count':count,'encoded_size':len(encode_stream(new))})
        print(json.dumps({'packed':refs}),flush=True)
    # Successful groups form an isolated review build; remaining failures never vanish from its manifest.
    nc,slack=repack_parts(c,0,changes);post_slack=None
    if post_changes:nc,post_slack=repack_parts(nc,5,post_changes)
    ng,rep=repack_variable(g,replacements,new_counts);result=replace_entry(replace_entry(arc,2,ng),3,nc)
    checked=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        aa=graphics_bank(g,bi,allow_bank_aliases=True);bb=graphics_bank(ng,bi,allow_bank_aliases=True)
        if (aa['base'],aa['end'],len(aa['frames']))!=(bb['base'],bb['end'],len(bb['frames'])):raise ValueError('Bank dimensions changed')
        for a,b in zip(aa['frames'],bb['frames']):
            old=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;new=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data
            if old!=new and not(bi==0 and a['index']in replacements and new==replacements[a['index']]):raise ValueError('Other graphics changed')
            checked+=1
    for bi in range(len(bank_offsets(c))):
        for n in range(composition_frame(c,bi,0)['bank_frame_count']):
            if (bi==0 and n in changes)or(bi==5 and n in post_changes):continue
            if records(c,bi,n)!=records(nc,bi,n):raise ValueError('Other part records changed')
    for n,want in applied.items():
        actual,_=render(result,0,0,n)
        if not np.array_equal(actual,want):raise ValueError('Readback base differs')
        expected=post_targets[n]if n in post_targets else want if n in shared else full(arc,n)[1]
        if not np.array_equal(expected,full(result,n)[1]):raise ValueError(f'Acquired final display differs: {n}')
    if entry(result,9)!=pal or len(arc)!=len(result):raise ValueError('Palette or ARC size changed')
    out=folder/'packed_progress';out.mkdir(exist_ok=True);(out/'PL02_U.ARC').write_bytes(result)
    report={'project':project,'before':sha(arc),'after':sha(result),'frames':sorted(applied),'remaining_art':sorted(set(range(237))-set(applied)),'failures':failures,'groups':reports,'graphics_repack':rep,'parts_slack':slack,'post_parts_slack':post_slack,'all_raw_references_checked':checked,'acquired_preserved_except':sorted(set(post_changes)|shared),'post_frames':sorted(post_changes),'shared_frames':sorted(shared),'production_complete':False,'runtime_verified':False}
    write(out/'packing.json',report);print(json.dumps({'applied':len(applied),'failures':failures,'parts_slack':slack,'graphics_slack':rep['remaining_slack']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project');pack(p.parse_args().project)
