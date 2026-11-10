"""未참조 타일을 0으로 가정했을 때의 정원만 조사. 자원 출력/적용 금지."""
from pathlib import Path
import sys,json
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,write,need
from scripts.export_x_consistency import Archive
from src.psx_player import bank_offsets,composition_frame,indexed_atlas,decode_stream
from src.psx_compress import encode_stream

def main():
    a=Archive((H/'prepared_dash_base01/PL00_U.ARC').read_bytes());q=json.loads((H/'base_run_complete_pack05/progress.json').read_text('utf8'));selected={int(n):bytes.fromhex(r)for n,r in q['raws'].items()};groups={}
    for f in a.banks[0]['frames']:groups.setdefault(f['offset'],[]).append(f)
    counts={b:composition_frame(a.c,b,0)['bank_frame_count']for b in range(len(bank_offsets(a.c)))};results={}
    for profile,banks in [('main_known',[0,5,6,7,8]),('all_composition_banks_same_frame',list(counts))]:
        rows=[];originaltotal=cleartotal=0;originaldedup={};cleardedup={}
        for off,frames in groups.items():
            f=frames[0];dec=decode_stream(a.g,off,f['limit'],f['tile_count']*128);raw=dec.data;oldcode=encode_stream(raw);used=set();consumers=[];unsupported=[]
            for ff in frames:
                n=ff['index']
                for b in banks:
                    if n>=counts[b]:continue
                    cp=composition_frame(a.c,b,n)
                    for part in cp['parts']:
                        t=part['tile']
                        if part['page'] or t>=f['tile_count']:unsupported.append({'ref':n,'bank':b,'tile':t,'page':part['page']});continue
                        used.add(t);consumers.append({'ref':n,'bank':b,'tile':t})
            atlas,loc,_=indexed_atlas(raw,f['tile_count']);atlas=np.frombuffer(atlas,np.uint8).reshape(-1,256);nr=bytearray(raw);cleared=[]
            for t in sorted(set(range(f['tile_count']))-used):
                tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16];nonzero=int((tile>0).sum())
                if not nonzero:continue
                cleared.append({'tile':t,'nonzero_texels':nonzero,'tile_sha256':sha(tile.tobytes())})
                for y in range(16):
                    for x in range(16):
                        pos,shift=loc[(t//16*16+y)*256+t%16*16+x];nr[pos]&=~(15<<shift)
            nr=bytes(nr);code=encode_stream(nr);need(decode_stream(code,0,len(code),len(nr)).data==nr,'Roundtrip changed')
            target=f['index']in selected;chosen=selected[f['index']]if target else raw;clearchosen=selected[f['index']]if target else nr
            oldlen=len(encode_stream(chosen));newlen=len(encode_stream(clearchosen));originaltotal+=oldlen;cleartotal+=newlen;originaldedup.setdefault((sha(chosen),len(chosen)),oldlen);cleardedup.setdefault((sha(clearchosen),len(clearchosen)),newlen)
            if cleared or target:rows.append({'refs':[v['index']for v in frames],'target':target,'before_raw_sha256':sha(raw),'hypothetical_raw_sha256':sha(nr),'used_tiles':sorted(used),'cleared_tiles':cleared,'before_bytes':len(oldcode),'after_bytes':len(code),'bank_budget_saving':0 if target else len(oldcode)-len(code),'consumer_records':consumers,'other_bank_or_page_records':unsupported})
        bank=a.banks[0];capacity=bank['end']-bank['base']-len(bank['frames'])*4
        results[profile]={'rows':rows,'same_frame_banks':banks,'target32_raw_unchanged':True,'untarget_recompressed_total':originaltotal,'hypothetical_total':cleartotal,'saving':originaltotal-cleartotal,'all_exact_stream_dedup_bytes':sum(cleardedup.values()),'remaining_slack_with_dedup':capacity-sum(cleardedup.values()),'unproven_assumption':'gfx0와 다른parts은행의 frame이 항상 같은지 및 직접GPU소비/부분업로드 계승은 코드감사 후 확정 필요. 이 보고서는 적용 허가/안전 증명이 아니다.'}
    write(H/'base_run_unused_tile_probe.json',{'parent_sha256':sha(a.data),'source_new_raw_report_sha256':sha((H/'base_run_complete_pack05/progress.json').read_bytes()),'composition_bank_frame_counts':counts,'profiles':results,'analysis_only':True,'resource_written':False,'proven_safe_to_apply':False})
    print(json.dumps({k:{kk:vv for kk,vv in v.items()if kk!='rows'}for k,v in results.items()},ensure_ascii=False))
if __name__=='__main__':main()
