"""동일 타일 수·동일 raw만 공유하여 고정 그래픽은행 안에 패킹한다."""
import struct,hashlib
from src.psx_player import graphics_bank,decode_stream
from src.psx_compress import encode_stream
def repack_identical(g,replacements,counts):
 bank=graphics_bank(g,0,allow_bank_aliases=True);oldgroups={};streams={};keys={};expected={};newcounts={};oldbytes=0
 for f in bank['frames']:oldgroups.setdefault(f['offset'],[]).append(f)
 for off,fs in oldgroups.items():
  f=fs[0];old=decode_stream(g,off,f['limit'],f['tile_count']*128);oldbytes+=old.end-off;selected=[q for q in fs if q['index']in replacements]
  if selected and len(selected)!=len(fs):raise ValueError('Incomplete original shared group')
  for q in fs:
   n=q['index'];count=counts[n]if selected else q['tile_count'];raw=replacements[n]if selected else old.data
   if not 0<count<=32 or len(raw)!=count*128:raise ValueError('Native buffer')
   key=(count,hashlib.sha256(raw).hexdigest());code=encode_stream(raw)if selected else g[off:old.end]
   if decode_stream(code,0,len(code),len(raw)).data!=raw:raise ValueError('Encode exact')
   if key in streams:
    if streams[key]['raw']!=raw:raise ValueError('Raw digest collision')
    if len(code)<len(streams[key]['code']):streams[key]['code']=code
   else:streams[key]={'raw':raw,'code':code,'refs':[],'old_offsets':set()}
   streams[key]['refs'].append(n);streams[key]['old_offsets'].add(off);keys[n]=key;expected[n]=raw;newcounts[n]=count
 cursor=bank['base']+len(bank['frames'])*4;loc={};ordered=sorted(streams,key=lambda k:min(streams[k]['refs']))
 for k in ordered:loc[k]=cursor;cursor+=len(streams[k]['code'])
 if cursor>bank['end']:raise ValueError(f'Exact raw dedup still exceeds capacity by {cursor-bank["end"]}')
 out=bytearray(g)
 for k in ordered:out[loc[k]:loc[k]+len(streams[k]['code'])]=streams[k]['code']
 for f in bank['frames']:n=f['index'];struct.pack_into('<I',out,bank['base']+n*4,newcounts[n]<<20|loc[keys[n]]-bank['base'])
 out=bytes(out)
 if out[:bank['base']]!=g[:bank['base']]or out[bank['end']:]!=g[bank['end']:]:raise ValueError('Other bank bytes')
 for f in graphics_bank(out,0,allow_bank_aliases=True)['frames']:
  n=f['index']
  if f['tile_count']!=newcounts[n]or decode_stream(out,f['offset'],f['limit'],f['tile_count']*128).data!=expected[n]:raise ValueError('Raw/tile readback')
 return out,{'bank':0,'bank_boundaries_preserved':True,'original_slack':bank['end']-bank['base']-len(bank['frames'])*4-oldbytes,'remaining_slack':bank['end']-cursor,'max_tiles':max(newcounts.values()),'buffer_bytes':4096,'exact_raw_identity_dedup':True,'deduplicated_groups':[{'refs':v['refs'],'old_offsets':sorted(v['old_offsets']),'tile_count':k[0],'raw_sha256':k[1],'encoded_bytes':len(v['code'])}for k,v in streams.items()if len(v['old_offsets'])>1],'changed_tile_counts':{n:c for n,c in newcounts.items()if c!=bank['frames'][n]['tile_count']}}
