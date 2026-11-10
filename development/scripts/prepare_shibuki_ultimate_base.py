"""얼티밋 획득 전 PL02 기본형을 수용된 PL00 Shibuki 픽셀로 복원한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D,load
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank

PILOT_SHA='6f19bd3fdec7cf2dfc4fdf2b4230878ff0a7ceaede16999a662268e634212526'
PLACEHOLDERS={105,*range(175,183)}
ARMOR_ONLY=set(range(217,231))
EXCLUDED=PLACEHOLDERS|ARMOR_ONLY

def prepare(out,audit=False):
    out=out.resolve()
    if not out.is_relative_to(D) or out.exists():raise ValueError('Fresh task output required')
    _,arcs=load();source=arcs['parent']['PL00_U.ARC'];pilot=(D/'pilot01/PL02_U.ARC').read_bytes()
    if sha256(pilot)!=PILOT_SHA:raise ValueError('Changed pilot')
    bg,bc,bp=[entry(source,k) for k in (2,3,9)];g,c,pal=[entry(pilot,k) for k in (2,3,9)]
    bank=graphics_bank(g,0,allow_bank_aliases=True);bb=graphics_bank(bg,0,allow_bank_aliases=True)
    groups={};nc=bytearray(c);targets={};reports=[];exact=0;part_records={}
    for f in bank['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
    for off,refs in groups.items():
        if set(refs)<=EXCLUDED:continue
        if set(refs)&EXCLUDED:raise ValueError('Excluded reference shares a replaced stream')
        f=bank['frames'][refs[0]];sf=bb['frames'][refs[0]]
        if len({bb['frames'][n]['offset'] for n in refs})!=1:raise ValueError('Source aliases differ')
        decoded=decode_stream(g,off,f['limit'],f['tile_count']*128);old=decoded.data
        sr=decode_stream(bg,sf['offset'],sf['limit'],sf['tile_count']*128).data
        sa,_,_=indexed_atlas(sr,sf['tile_count']);da,locations,_=indexed_atlas(old,f['tile_count'])
        sa=np.frombuffer(sa,np.uint8).reshape(-1,256);da=np.frombuffer(da,np.uint8).reshape(-1,256)
        def tile(atlas,t):return atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
        sids={q['tile'] for n in refs for q in composition_frame(bc,0,n)['parts']}
        protected={q['tile'] for n in refs for bi in (5,6,7,8) for q in composition_frame(c,bi,n)['parts'] if q['tile']<f['tile_count']}
        free=set(range(f['tile_count']))-protected;mapping={};domains={}
        for t in sorted(sids):
            flags={q['flags'] for n in refs for q in composition_frame(bc,0,n)['parts'] if q['tile']==t}
            patch=tile(sa,t)
            def safe(d):
                if not np.any(patch):return True
                if d==t and np.array_equal(patch>0,tile(da,d)>0):
                    old_flags={q['flags'] for n in refs for q in composition_frame(c,0,n)['parts'] if q['tile']==d}
                    if flags<=old_flags:return True # Identical inherited effect edges.
                return not (d%16==0 and (np.any(patch[:,0]) or any(v&64 for v in flags))) and not ((d//16)%16==0 and np.any(patch[0,:]) and any(v&128 for v in flags))
            choices=[d for d in range(f['tile_count']) if safe(d) and (d in free or np.array_equal(patch,tile(da,d)))]
            if not choices:raise ValueError(f'{refs}: insufficient safe base tiles')
            domains[t]=sorted(choices,key=lambda d:(d!=t,d in protected,d%16==0,d))
        from scipy.optimize import linear_sum_assignment
        ordered=sorted(sids);cost=np.full((len(ordered),f['tile_count']),1000000,dtype=np.int64)
        for i,t in enumerate(ordered):
            for d in domains[t]:cost[i,d]=(d!=t)*1000+(d in protected)*100+(d%16==0)*10+d
        rows,cols=linear_sum_assignment(cost)
        if len(rows)!=len(ordered) or any(cost[i,j]>=1000000 for i,j in zip(rows,cols)):raise ValueError(f'{refs}: no complete safe tile assignment')
        mapping={ordered[int(i)]:int(j) for i,j in zip(rows,cols)}
        raw=bytearray(old)
        for dst in free-set(mapping.values()):
            for y in range(16):
                for x in range(16):
                    pos,shift=locations[(dst//16*16+y)*256+dst%16*16+x];raw[pos]&=~(15<<shift)
        for src,dst in mapping.items():
            for y in range(16):
                for x in range(16):
                    pos,shift=locations[(dst//16*16+y)*256+dst%16*16+x]
                    raw[pos]=(raw[pos]&~(15<<shift))|(int(tile(sa,src)[y,x])<<shift)
        raw=bytes(raw)
        for n in refs:
            srcp=composition_frame(bc,0,n)['parts'];dstp=composition_frame(c,0,n)['parts']
            if len(srcp)!=len(dstp):raise ValueError(f'{n}: base part count differs')
            part_records[n]=b''.join(struct.pack('<BBbb',s['flags'],mapping[s['tile']],s['x'],s['y']) for s in srcp)
            expected=canvas_from_parts(sr,sf['tile_count'],composition_frame(bc,0,n))
            actual=canvas_from_parts(raw,f['tile_count'],{'parts':[{**s,'tile':mapping[s['tile']]} for s in srcp]})
            if not np.array_equal(actual,expected):raise ValueError(f'{n}: Shibuki pixels differ')
            for bi in (5,6,7,8):
                cp=local_composition(composition_frame(c,bi,n))
                if not np.array_equal(canvas_from_parts(old,f['tile_count'],cp),canvas_from_parts(raw,f['tile_count'],cp)):raise ValueError('Armor changed')
            targets[n]=raw;exact+=1
        code=encode_stream(raw);reports.append({'refs':refs,'mapping':mapping,'encoded_bytes':len(code),'old_encoded_bytes':decoded.end-off,'slot_capacity':f['limit']-off,'tile_count':f['tile_count']})
    starts=bank_offsets(c);cb,ce=starts[:2];count=len(bank['frames'])
    records=[part_records.get(n,b''.join(c[p['record_offset']:p['record_offset']+4] for p in composition_frame(c,0,n)['parts'])) for n in range(count)]
    packed=bytearray(records[0]);locations={0:0}
    for n in sorted(range(1,count),key=lambda n:(-len(records[n]),n)):
        rr=records[n];pos=next((i for i in range(0,len(packed)-len(rr)+1,4) if packed[i:i+len(rr)]==rr),None)
        if pos is None:
            overlap=next((i for i in range(min(len(packed),len(rr)),0,-4) if packed[-i:]==rr[:i]),0)
            pos=len(packed)-overlap;packed+=rr[overlap:]
        locations[n]=pos
    if count*4+len(packed)>ce-cb:raise ValueError(f'Composition bank needs {count*4+len(packed)}, capacity {ce-cb}')
    nc[cb+count*4:cb+count*4+len(packed)]=packed
    for n in range(count):struct.pack_into('<I',nc,cb+n*4,((count+locations[n]//4)<<16)|len(records[n])//4)
    for n,rr in enumerate(records):
        actual=b''.join(nc[p['record_offset']:p['record_offset']+4] for p in composition_frame(nc,0,n)['parts'])
        if actual!=rr:raise ValueError('Composition packing readback differs')
    report={'kind':'ultimate_pre_capsule_base_fix','source_arc_sha256':sha256(source),'pilot_arc_sha256':PILOT_SHA,'base_frames_exact':exact,'frames':sorted(targets),'excluded_original_placeholders':sorted(PLACEHOLDERS),'excluded_armor_only_nova_strike_and_hover':sorted(ARMOR_ONLY),'groups':reports,'composition_bank_remaining_bytes':ce-cb-count*4-len(packed),'composition_bank_bounds_preserved':True,'over_original_encoded_budget':[r['refs'] for r in reports if r['encoded_bytes']>r['old_encoded_bytes']],'over_slot_capacity':[r['refs'] for r in reports if r['encoded_bytes']>r['slot_capacity']]}
    excluded_bytes=sum(decode_stream(g,o,bank['frames'][ns[0]]['limit'],bank['frames'][ns[0]]['tile_count']*128).end-o for o,ns in groups.items() if set(ns)<=EXCLUDED)
    report['graphics_required_bytes']=len(bank['frames'])*4+excluded_bytes+sum(r['encoded_bytes'] for r in reports)
    report['graphics_capacity']=bank['end']-bank['base']
    out.mkdir()
    if audit:
        (out/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('groups','frames')}));return
    # Reuse the existing Fourth Armor bank compactor only if original slots fail.
    if report['over_original_encoded_budget']:
        ng,repack=repack_graphics_bank(g,0,{n:encode_stream(raw) for n,raw in targets.items()})
    else:
        ng=g;repack=None
        for r in reports:
            n=r['refs'][0];ng,_=replace_stream(ng,bank['frames'][n],targets[n])
    decoded_count=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        a=graphics_bank(g,bi,allow_bank_aliases=True);b=graphics_bank(ng,bi,allow_bank_aliases=True)
        if (a['base'],a['end'],len(a['frames']))!=(b['base'],b['end'],len(b['frames'])):raise ValueError('Bank dimensions changed')
        for x,y in zip(a['frames'],b['frames']):
            before=decode_stream(g,x['offset'],x['limit'],x['tile_count']*128).data;after=decode_stream(ng,y['offset'],y['limit'],y['tile_count']*128).data
            if x['tile_count']!=y['tile_count'] or after!=(targets.get(x['index'],before) if bi==0 else before):raise ValueError('Unexpected decoded data')
            decoded_count+=1
    others=0
    for bi,off in enumerate(bank_offsets(c)):
        for n in range(struct.unpack_from('<I',c,off)[0]>>16):
            if bi==0 and n in targets:continue
            cp=composition_frame(c,bi,n);np_=composition_frame(nc,bi,n)
            extract=lambda data,p:b''.join(data[q['record_offset']:q['record_offset']+4] for q in p['parts'])
            if extract(c,cp)!=extract(nc,np_):raise ValueError('Protected composition changed')
            others+=1
    if len(c)!=len(nc) or c[:cb]!=nc[:cb] or c[ce:]!=nc[ce:]:raise ValueError('Unexpected composition bytes')
    result=replace_entry(replace_entry(pilot,2,ng),3,bytes(nc))
    if len(result)!=len(pilot) or entry(result,9)!=pal:raise ValueError('Archive or palettes changed')
    report.update({'modified_arc_sha256':sha256(result),'decoded_references_checked':decoded_count,'protected_compositions':others,'repack':repack,'same_bank_compaction':repack is not None,'bank_boundaries_sizes_lbas_preserved':True,'all_armor_layers_preserved':True,'palette_preserved':True,'timing_logic_preserved':True,'runtime_verified':False})
    (out/'PL02_U.ARC').write_bytes(result);(out/'recipe.json').write_text(json.dumps(report,indent=2));print(json.dumps({'output':str(out),'sha256':sha256(result),'exact_base_frames':exact,'repack_slack':repack['remaining_slack'] if repack else None}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--audit',action='store_true');a=p.parse_args();prepare(a.output,a.audit)
