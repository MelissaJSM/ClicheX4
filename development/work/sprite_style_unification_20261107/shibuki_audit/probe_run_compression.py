"""현재 native raw를 바꾸지 않는 재압축/동일스트림 공유의 정원 조사."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,write,need
from scripts.export_x_consistency import Archive
from src.psx_player import decode_stream
from src.psx_compress import encode_stream
def main():
    a=Archive((H/'prepared_dash_base01/PL00_U.ARC').read_bytes());q=json.loads((H/'base_run_complete_pack03/progress.json').read_text('utf8'));new={int(n):bytes.fromhex(v)for n,v in q['raws'].items()};groups={};rows=[];dedup={};oldtotal=encodetotal=0
    for f in a.banks[0]['frames']:groups.setdefault(f['offset'],[]).append(f)
    for off,fs in groups.items():
        f=fs[0];raw=decode_stream(a.g,off,f['limit'],f['tile_count']*128);nr=new.get(f['index'],raw.data);code=encode_stream(nr);need(decode_stream(code,0,len(code),len(nr)).data==nr,'Recompression mismatch');oldbytes=raw.end-off;current=len(code)if f['index']in new else oldbytes;oldtotal+=current;encodetotal+=len(code);key=(sha(nr),len(nr));dedup.setdefault(key,len(code))
        rows.append({'refs':[v['index']for v in fs],'target':f['index']in new,'old_bytes':oldbytes,'current_bytes':current,'optimal_bytes':len(code),'same_raw_sha256':key[0]})
    b=a.banks[0];capacity=b['end']-b['base']-len(b['frames'])*4
    report={'parent_sha256':sha(a.data),'rows':rows,'capacity':capacity,'current_bytes':oldtotal,'recompressed_bytes':encodetotal,'deduplicated_bytes':sum(dedup.values()),'recompressed_saving':oldtotal-encodetotal,'dedup_extra_saving':encodetotal-sum(dedup.values()),'dedup_remaining_slack':capacity-sum(dedup.values()),'graphics_bank_unchanged':True,'resource_written':False}
    write(H/'base_run_compression_probe.json',report);print(json.dumps({k:v for k,v in report.items()if k!='rows'}))
if __name__=='__main__':main()
