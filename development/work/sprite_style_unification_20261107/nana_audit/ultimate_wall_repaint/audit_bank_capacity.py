"""그림·게임을 쓰지 않고 동일 raw 스트림 중복과 무손실 재압축 여유 조사."""
from pathlib import Path
import sys,json,collections
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,digest,sha,need
from src.psx_player import decode_stream
from src.psx_compress import encode_stream
def main():
 src=N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC';need(digest(src)=='122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18','Source SHA');a=Archive(src.read_bytes());b=a.banks[0];groups=collections.defaultdict(list)
 for f in b['frames']:groups[f['offset']].append(f)
 records=[];byraw=collections.defaultdict(list)
 for off,fs in groups.items():
  f=fs[0];dec=decode_stream(a.g,off,f['limit'],f['tile_count']*128);code=encode_stream(dec.data);need(decode_stream(code,0,len(code),len(dec.data)).data==dec.data,'Roundtrip');rec={'offset':off,'refs':[f['index']for f in fs],'tile_count':f['tile_count'],'raw_sha256':sha(dec.data),'original_bytes':dec.end-off,'reencoded_bytes':len(code)};records.append(rec);byraw[(f['tile_count'],sha(dec.data))].append(rec)
 original=sum(r['original_bytes']for r in records);dedup=sum(min(r['original_bytes']for r in rs)for rs in byraw.values());encoded=sum(min(r['original_bytes'],r['reencoded_bytes'])for r in records);both=sum(min(min(r['original_bytes'],r['reencoded_bytes'])for r in rs)for rs in byraw.values());capacity=b['end']-b['base']-len(b['frames'])*4
 report={'source_path':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'read_only':True,'bank':0,'bank_base':b['base'],'bank_end':b['end'],'frames':len(b['frames']),'unique_offsets':len(records),'unique_same_count_raws':len(byraw),'original_stream_bytes':original,'original_slack':capacity-original,'possible_raw_identity_dedup_gain':original-dedup,'possible_exact_reencode_gain':original-encoded,'combined_upper_bound_gain':original-both,'same_count_duplicate_groups':[rs for rs in byraw.values()if len(rs)>1],'all_streams':records,'new_wall_packing_attempted':False,'not_a_runtime_verification':True}
 out=D/'bank_capacity_v1';out.mkdir(exist_ok=False);write(out/'report.json',report);print(json.dumps({k:v for k,v in report.items()if k not in('all_streams','same_count_duplicate_groups')}))
if __name__=='__main__':main()
