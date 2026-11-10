"""PL00 그래픽 entry2의 실제 은행별 디렉터리·압축종료·후미 여유 읽기 조사."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,write
from scripts.export_x_consistency import Archive
from src.psx_player import decode_stream,bank_offsets
def main():
    p=H/'prepared_dash_base01/PL00_U.ARC';a=Archive(p.read_bytes());rows=[];seen={};total=0
    for bi,b in enumerate(a.banks):
        if b['base']in seen:
            rows.append({'bank':bi,'aliases_physical_bank':seen[b['base']],'start':b['base'],'end':b['end']});continue
        seen[b['base']]=bi;groups={}
        for f in b['frames']:groups.setdefault(f['offset'],[]).append(f)
        ranges=[]
        for off,fs in sorted(groups.items()):
            f=fs[0];r=decode_stream(a.g,off,f['limit'],f['tile_count']*128)
            ranges.append({'start':off,'end':r.end,'length':r.end-off,'refs':[v['index']for v in fs],'tile_count':f['tile_count'],'raw_sha256':sha(r.data),'compressed_sha256':sha(a.g[off:r.end])})
        header=len(b['frames'])*4;used=header+sum(v['length']for v in ranges);span=b['end']-b['base'];slack=span-used;tail=b['end']-max(v['end']for v in ranges);tailbytes=a.g[b['end']-tail:b['end']]
        row={'bank':bi,'start':b['base'],'end':b['end'],'span':span,'frame_count':len(b['frames']),'header_bytes':header,'unique_streams':len(ranges),'minimal_unchanged_compressed_span':used,'trailing_padding_bytes':tail,'trailing_nonzero_bytes':sum(v!=0 for v in tailbytes),'internal_unconsumed_gap_bytes':slack-tail,'total_unconsumed_span':slack,'streams':ranges}
        rows.append(row)
        if bi:total+=slack
    report={'analysis_only':True,'source_path':p.relative_to(ROOT).as_posix(),'source_sha256':sha(a.data),'entry2_length':len(a.g),'entry2_sha256':sha(a.g),'directory_bytes':bank_offsets(a.g,allow_aliases=True)[0],'banks':rows,'non_main_unused_span_total':total,'all_bank_payloads_decoded':True,'direct_pointer_reference_audit_complete':False,'resource_written':False,'difference_from_approved_current_repack':'기존방식은 gfx은행 디렉터리·시작/끝 동일. 향후안은 entry2총길이/ARC경계는 고정하되 후미미소비 공간을 합쳐 은행 디렉터리 상대offset을 바꾸므로 별도 방식 판단 필요. 이 도구는 제안량 조사만 하며 적용하지 않음.','required_followup':['최신 EXE의 SP_PLAYER_GFX bank table 읽기 및 직접절대주소 소비 감사','동일 길이 entry2 후보의 모든 gfx raw·comp records·palette·audio exact와 whole entry guards','원래 MIPS decoder/업로드 및 모든 bank선택에 대한 native주소 검증','새부팅 실제검증. 옛 F1의RAM캐시를 새자원 증거로 사용하지 않음']}
    write(H/'pl00_graphics_slack_audit.json',report);print(json.dumps({'entry2_bytes':len(a.g),'physical_banks':len(seen),'other_bank_unused_span':total,'banks':[{k:v for k,v in r.items()if k!='streams'}for r in rows]}))
if __name__=='__main__':main()
