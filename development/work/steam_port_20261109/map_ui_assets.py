"""Exact original-data correspondence for static TEX, COL and PAT resources."""
from collections import defaultdict,Counter
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from src.steam_arc import SteamArc,pat_from_ps1
from src.steam_player import unpack_indices

WORK=Path(__file__).resolve().parent
inventory=json.loads((ROOT/'work/steam_port_research_20261109/inventory.json').read_text(encoding='utf-8'))
exact=defaultdict(list);textures=defaultdict(list);lengths=set();source_entries=[]
def sha(b):return hashlib.sha256(b).hexdigest()
source_arcs={};excluded=[]
with Path(inventory['ps1_original']['path']).open('rb') as f:
    reader=DiscReader(f,Path(inventory['ps1_original']['path']).stat().st_size)
    for record in reader.inspect()['files']:
        name=record['name'].split(';')[0]
        if record['directory'] or not name.endswith('.ARC'):continue
        data=reader.read(record['lba'],record['size']);source_arcs[name]=data
        try:entries=psx_arc(data)
        except ValueError as error:
            excluded.append({'arc':name,'reason':str(error)});continue
        for e in entries:
            raw=data[e['offset']:e['offset']+e['size']]
            meta={'arc':name,'index':e['index'],'type':e['type'],'size':len(raw),'sha256':sha(raw)}
            source_entries.append(meta)
            exact[('COL',sha(raw))].append(meta)
            if len(raw)>=8:
                first=struct.unpack_from('<I',raw)[0]
                if first%4==0 and 4<=first<=256:
                    try:pat=pat_from_ps1(raw)
                    except (ValueError,struct.error,IndexError):pass
                    else:exact[('PAT',sha(pat))].append(meta)
            kind=int(e['type'],16)
            if kind&0xf0000==0x10000 and len(raw)<=2*1024*1024:
                pixels=unpack_indices(raw)
                textures[(len(pixels),sha(pixels))].append(meta);lengths.add(len(pixels))
mapped=[];unmapped=[]
for name,info in inventory['archives'].items():
    arc=SteamArc((WORK/'original/nativeDX10/X4/romPC'/name).read_bytes(),info['sha256'])
    for e in arc.entries:
        data=e.payload;kind=data[:4];matches=[];prefix=None
        if kind==b'COL\0':matches=exact.get(('COL',sha(data[12:])),[])
        elif kind==b'PAT\0':matches=exact.get(('PAT',sha(data)),[])
        elif kind==b'TEX\0' and len(data)>=20 and data[13]==0x12:
            start=struct.unpack_from('<I',data,16)[0];pixels=data[start:]
            candidates=[]
            for length in sorted(lengths,reverse=True):
                if length>len(pixels):continue
                found=textures.get((length,sha(pixels[:length])),[])
                if found:candidates.append((length,found))
            if candidates:prefix,matches=candidates[0]
        else:continue
        row={'steam_arc':name,'name':e.name,'type':e.kind,'magic':kind.decode('ascii').rstrip('\0'),
             'steam_sha256':sha(data),'steam_size':len(data),'pixel_prefix':prefix,'ps1_sources':matches}
        (mapped if matches else unmapped).append(row)
result={'mapped':mapped,'unmapped':unmapped,'excluded_sources':excluded,'summary':{'ps1_arcs':len(source_arcs),'ps1_entries':len(source_entries),
        'mapped_by_type':dict(Counter(r['magic'] for r in mapped)),'unmapped_by_type':dict(Counter(r['magic'] for r in unmapped))}}
(WORK/'ui_correspondence.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['summary'])
for row in mapped:
    if row['steam_arc'] in ('load_eng.arc','st0e_00_eng.arc','st0e_01_eng.arc','st0f_0x_eng.arc','st0f_0z_eng.arc'):
        print(row['steam_arc'],row['name'],row['magic'],[(s['arc'],s['type']) for s in row['ps1_sources']][:5])
