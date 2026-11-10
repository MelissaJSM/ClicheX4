"""Reviewable fixed-size ARC text expansion; preserves every decoded sprite."""
import struct
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import bank_offsets,graphics_bank,decode_stream
from src.psx_bank_repack import repack_graphics_bank

def compact_parts(parts,donate=2048):
    """Share identical part-record runs; retain every ordered native draw record."""
    from src.psx_ui_atlas import aliased_composition
    offsets=bank_offsets(parts,allow_aliases=True);banks={};details=[]
    for b,start in enumerate(offsets):
        if start in banks:continue
        count=aliased_composition(parts,b,0)['bank_frame_count'];records=[]
        for n in range(count):
            c=aliased_composition(parts,b,n)
            records.append(b''.join(parts[p['record_offset']:p['record_offset']+4] for p in c['parts']))
        data=bytearray(records[0]);starts=[count*4]
        for raw in records[1:]:
            pos=next((i for i in range(0,len(data)-len(raw)+1,4) if data[i:i+len(raw)]==raw),None)
            if pos is None:
                overlap=next((i for i in range(min(len(data),len(raw)),0,-4) if data[-i:]==raw[:i]),0)
                pos=len(data)-overlap;data+=raw[overlap:]
            starts.append(count*4+pos)
        headers=[(off//4)<<16|len(raw)//4 for off,raw in zip(starts,records)]
        if any(h>0xffffffff for h in headers):raise ValueError('Part offset overflow')
        banks[start]=struct.pack('<'+'I'*count,*headers)+data
        details.append({'bank':b,'frames':count,'bytes':len(banks[start])})
    out=bytearray(len(offsets)*4);positions={}
    for start,data in banks.items():positions[start]=len(out);out+=data
    limit=len(parts)-donate
    if donate<=0 or donate%4 or len(out)>limit:raise ValueError('Insufficient proven part-record space')
    out+=bytes(limit-len(out))
    for b,start in enumerate(offsets):struct.pack_into('<I',out,b*4,positions[start])
    checked=0
    for b in range(len(offsets)):
        for n in range(aliased_composition(parts,b,0)['bank_frame_count']):
            before=aliased_composition(parts,b,n);after=aliased_composition(out,b,n)
            extract=lambda data,c:b''.join(data[p['record_offset']:p['record_offset']+4] for p in c['parts'])
            if before['bank_frame_count']!=after['bank_frame_count'] or extract(parts,before)!=extract(out,after):raise ValueError('Part drawing records changed')
            checked+=1
    return bytes(out),{'checked_composition_frames':checked,'ordered_part_records_preserved':True,'remaining_slack':limit-sum(len(v) for v in banks.values())-len(offsets)*4,'banks':details}

def expand_dialogue_from_parts(archive,new_text):
    """Review-only alternative for a tight graphics bank (PL02 Ultimate UI)."""
    entries=psx_arc(archive);pm=next(e for e in entries if e['type']=='0x3');tm=entries[-1]
    if tm['type']!='0x15':raise ValueError('Expected last dialogue entry')
    donate=((len(new_text)+2047)//2048-(tm['size']+2047)//2048)*2048
    if donate!=2048:raise ValueError('Only reviewed one-sector text expansion is supported')
    block=lambda e:archive[e['offset']:e['offset']+e['size']]
    parts,report=compact_parts(block(pm),donate)
    out=bytearray(archive[:2048]);positions=[]
    for e in entries:
        data=parts if e['index']==pm['index'] else bytes(new_text) if e['index']==tm['index'] else block(e)
        struct.pack_into('<I',out,12+8*e['index'],len(data));pos=len(out);out+=data
        pad=(-len(data))%2048;oldpadding=archive[e['offset']+e['size']:e['offset']+((e['size']+2047)//2048)*2048]
        out+=(oldpadding+bytes(pad))[:pad]
        positions.append({'index':e['index'],'type':e['type'],'old_offset':e['offset'],'new_offset':pos,'old_size':e['size'],'new_size':len(data)})
    if len(out)!=len(archive):raise ValueError('Archive size change refused')
    for e,z in zip(entries,psx_arc(out)):
        if e['index'] not in (pm['index'],tm['index']) and block(e)!=out[z['offset']:z['offset']+z['size']]:raise ValueError('Protected resource changed')
    return bytes(out),{'donated_bytes':donate,'source_sha256':sha256(archive),'output_sha256':sha256(out),'archive_size_preserved':True,'graphics_bytes_preserved':True,'other_entry_contents_preserved':True,'exe_changed':False,'positions':positions,'parts_compaction':report}

def expand_dialogue(archive,new_text,*,recompress=False):
    entries=psx_arc(archive);gm=next(e for e in entries if e['type']=='0x2');tm=entries[-1]
    if tm['type']!='0x15':raise ValueError('Expected last dialogue entry')
    block=lambda e:archive[e['offset']:e['offset']+e['size']]
    g=block(gm);old_offsets=bank_offsets(g,allow_aliases=True);bank=graphics_bank(g,0,allow_bank_aliases=True)
    oldpad=(tm['size']+2047)//2048*2048;newpad=(len(new_text)+2047)//2048*2048;donate=newpad-oldpad
    if donate!=2048:raise ValueError('Only reviewed one-sector text expansion is supported')
    first=bank['frames'][0];raw=decode_stream(g,first['offset'],first['limit'],first['tile_count']*128)
    replacements={f['index']:g[f['offset']:raw.end] for f in bank['frames'] if f['offset']==first['offset']}
    compact,report=repack_graphics_bank(g,0,replacements)
    recoded=[]
    if report['remaining_slack']<donate and recompress:
        from src.psx_compress import encode_stream
        saved=0;grouped={}
        for f in bank['frames']:grouped.setdefault(f['offset'],[]).append(f)
        for start,refs in sorted(grouped.items()):
            f=refs[0];old=decode_stream(g,start,f['limit'],f['tile_count']*128);code=encode_stream(old.data)
            if len(code)<old.end-start:
                for ref in refs:replacements[ref['index']]=code
                saved+=old.end-start-len(code);recoded.append({'references':[v['index'] for v in refs],'before':old.end-start,'after':len(code)})
            if report['remaining_slack']+saved>=donate:break
        compact,report=repack_graphics_bank(g,0,replacements)
    if report['remaining_slack']<donate:raise ValueError('Insufficient proven graphics slack')
    cut=bank['end']-donate;newg=bytearray(compact[:cut]+compact[bank['end']:])
    for i,off in enumerate(old_offsets):struct.pack_into('<I',newg,i*4,off-donate if off>=bank['end'] else off)
    checked=0
    for b in range(len(old_offsets)):
        before=graphics_bank(g,b,allow_bank_aliases=True);after=graphics_bank(newg,b,allow_bank_aliases=True)
        if len(before['frames'])!=len(after['frames']):raise ValueError('Sprite frame directory changed')
        for a,z in zip(before['frames'],after['frames']):
            x=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128);y=decode_stream(newg,z['offset'],z['limit'],z['tile_count']*128)
            if a['tile_count']!=z['tile_count'] or x.data!=y.data:raise ValueError('Sprite data changed')
            checked+=1
    out=bytearray(archive[:2048]);positions=[]
    for e in entries:
        data=bytes(newg) if e['index']==gm['index'] else bytes(new_text) if e['index']==tm['index'] else block(e)
        struct.pack_into('<I',out,12+8*e['index'],len(data));pos=len(out);out+=data
        pad=(-len(data))%2048
        oldpadding=archive[e['offset']+e['size']:e['offset']+((e['size']+2047)//2048)*2048]
        out+=(oldpadding+bytes(pad))[:pad]
        positions.append({'index':e['index'],'type':e['type'],'old_offset':e['offset'],'new_offset':pos,'old_size':e['size'],'new_size':len(data)})
    if len(out)!=len(archive):raise ValueError('Archive size change refused')
    rebuilt=psx_arc(out)
    for e,z in zip(entries,rebuilt):
        if e['index'] not in (gm['index'],tm['index']) and block(e)!=out[z['offset']:z['offset']+z['size']]:raise ValueError('Other resource content changed')
    return bytes(out),{'donated_bytes':donate,'source_sha256':sha256(archive),'output_sha256':sha256(out),'checked_graphics_references':checked,'all_decoded_graphics_preserved':True,'other_entry_contents_preserved':True,'archive_size_preserved':True,'exe_changed':False,'positions':positions,'graphics_compaction':report,'losslessly_recompressed_streams':recoded}
