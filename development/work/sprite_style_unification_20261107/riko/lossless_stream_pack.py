"""같은 길이·해제 바이트만 공유하고 픽셀 손실 없는 재압축만 수행한다."""
import struct,json,hashlib
from pathlib import Path
from src.psx_player import graphics_bank,decode_stream
from src.psx_compress import encode_stream
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,message):
    if not v:raise ValueError(message)
def repack(g,bank_id,replacements):
    bank=graphics_bank(g,bank_id);codes={};keys={};raws={};contents={};old_offsets=set();old_used=0
    for f in bank['frames']:
        decoded=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128)
        raw=replacements.get(f['index'],decoded.data);need(len(raw)==f['tile_count']*128,'Decoded length changed')
        key=(len(raw),sha(raw));keys[f['index']]=key;raws[f['index']]=raw;contents[key]=raw
        code=g[f['offset']:decoded.end]if raw==decoded.data else encode_stream(raw)
        if key not in codes or len(code)<len(codes[key]):codes[key]=code
        if f['offset']not in old_offsets:old_used+=decoded.end-f['offset'];old_offsets.add(f['offset'])
    budget=bank['end']-bank['base']-4*len(bank['frames']);total=sum(map(len,codes.values()));gains=[]
    cache=Path(__file__).resolve().parent/'lossless_compression_cache';cache.mkdir(exist_ok=True)
    for key in sorted(codes,key=lambda k:len(codes[k]),reverse=True):
        if total<=budget:break
        path=cache/(key[1]+'.bin');code=path.read_bytes()if path.exists()else encode_stream(contents[key])
        need(decode_stream(code,0,len(code),key[0]).data==contents[key],'Lossless decode mismatch')
        if not path.exists():path.write_bytes(code)
        saved=len(codes[key])-len(code)
        if saved>0:codes[key]=code;total-=saved;gains.append(dict(raw_sha256=key[1],saved_bytes=saved))
    diagnosis=dict(bank=bank_id,budget=budget,used=total,excess=max(0,total-budget),recompressed=gains,
                   variants=[dict(refs=[n for n in keys if keys[n]==k],code_size=len(v))for k,v in codes.items()if any(n in replacements for n in keys if keys[n]==k)])
    if total>budget:
        (cache/f'last_capacity_bank{bank_id}.json').write_text(json.dumps(diagnosis,indent=2)+'\n','utf8')
    need(total<=budget,f'Bank capacity after byte-exact sharing: excess {total-budget}')
    locations={};cursor=bank['base']+4*len(bank['frames']);out=bytearray(g)
    for key,code in codes.items():locations[key]=cursor;out[cursor:cursor+len(code)]=code;cursor+=len(code)
    need(locations[keys[0]]==bank['base']+4*len(bank['frames']),'Sentinel drift')
    for f in bank['frames']:struct.pack_into('<I',out,bank['base']+f['index']*4,f['tile_count']<<20|locations[keys[f['index']]]-bank['base'])
    out=bytes(out);need(out[:bank['base']]==g[:bank['base']]and out[bank['end']:]==g[bank['end']:],'Bank boundary changed')
    for f in graphics_bank(out,bank_id)['frames']:need(decode_stream(out,f['offset'],f['limit'],f['tile_count']*128).data==raws[f['index']],'Repacked raw changed')
    return out,dict(bank=bank_id,remaining_slack=budget-total,old_slack=budget-old_used,exact_raw_sharing_only=True,lossless_recompressed=gains,bank_boundaries_exact=True)
