"""기타 그래픽 은행의 동일 raw 재압축 절감량만 읽기 조사한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,write
from scripts.export_x_consistency import Archive
from src.psx_player import decode_stream
from src.psx_compress import encode_stream

def main():
    p=H/'prepared_dash_base01/PL00_U.ARC';a=Archive(p.read_bytes());seen=set();rows=[];cache={}
    for bi,b in enumerate(a.banks):
        if bi==0 or b['base'] in seen:continue
        seen.add(b['base']);groups={};sizes=[];unique={}
        for f in b['frames']:groups.setdefault(f['offset'],[]).append(f)
        for off,fs in sorted(groups.items()):
            f=fs[0];r=decode_stream(a.g,off,f['limit'],f['tile_count']*128);raw=r.data
            if raw not in cache:cache[raw]=encode_stream(raw)
            code=cache[raw];k=sha(raw);unique[k]=len(code)
            sizes.append({'refs':[v['index'] for v in fs],'tile_count':f['tile_count'],'raw_sha256':k,'original_bytes':r.end-off,'optimal_bytes':len(code),'saved':r.end-off-len(code)})
        header=len(b['frames'])*4;old=sum(v['original_bytes']for v in sizes);new=sum(v['optimal_bytes']for v in sizes);span=b['end']-b['base']
        rows.append({'bank':bi,'span':span,'header':header,'old_payload':old,'new_payload':new,'reencode_saving':old-new,'duplicate_raw_saving':new-sum(unique.values()),'unused_after_reencode_and_dedup':span-header-sum(unique.values()),'streams':sizes})
        print(json.dumps({k:v for k,v in rows[-1].items()if k!='streams'}),flush=True)
    report={'source_sha256':sha(a.data),'analysis_only':True,'resource_written':False,'banks':rows,'all_other_bank_slack_after_reencode_and_dedup':sum(v['unused_after_reencode_and_dedup']for v in rows),'all_other_bank_reencode_saving':sum(v['reencode_saving']for v in rows),'all_other_bank_raw_dedup_saving':sum(v['duplicate_raw_saving']for v in rows)}
    write(H/'pl00_other_bank_reencode_audit.json',report)
    print(json.dumps({k:v for k,v in report.items()if k!='banks'}))

if __name__=='__main__':main()
