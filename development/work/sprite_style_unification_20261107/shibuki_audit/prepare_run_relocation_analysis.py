"""새 그림을 줄이지 않는 최소 내부 directory 이동안을 문서화만 한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    c=H/'base_run_combined_storage_audit.json';j=json.loads(c.read_text('utf8'));s=H/'pl00_graphics_slack_audit.json';v=json.loads(s.read_text('utf8'));lookup={b['bank']:b for b in v['banks']};need(j['exact_target_layers']==160 and not j['part_errors'],'Target/parts not valid')
    grow=j['banks'][0]['required_aligned']-lookup[0]['span'];need(grow==944,'Unexpected plan size');trims={10:344,11:400,12:200};need(sum(trims.values())==grow,'No exact capacity balance');rows=[];pos=56
    for b in v['banks']:
        n=b['bank']
        if 'aliases_physical_bank'in b:rows.append({'bank':n,'alias':b['aliases_physical_bank'],'new_start':next(r['new_start']for r in rows if r['bank']==b['aliases_physical_bank'])});continue
        size=b['span']+grow if n==0 else b['span']-trims.get(n,0)
        if n in trims:need(size>=b['minimal_unchanged_compressed_span']and size%4==0,'Trim reaches live code or misaligns')
        rows.append({'bank':n,'old_start':b['start'],'new_start':pos,'old_end':b['end'],'new_end':pos+size,'old_span':b['span'],'new_span':size,'tail_trim':trims.get(n,0),'preserves_original_header_compressed_data':n!=0,'entire_original_bank_block_exact':n not in(0,10,11,12),'start_delta':pos-b['start']});pos+=size
    need(pos==j['fixed_entry2_length'],'Entry length changes');need(rows[13]['old_start']==rows[13]['new_start'],'Last bank moved')
    native=ROOT/'work/sprite_style_unification_20261107/zero_audit/pl00_bank_relocation_audit01/report.json'
    report={'status':'read_only_concrete_proposal_not_applied','parent_sha256':j['source']['sha256'],'target_lock_sha256':j['target_lock_sha256'],'entry2_length':pos,'entry2_outer_boundary_changes':False,'archive_size_lba_exe_palette_audio_changes':False,'new_art_texel_or_palette_reduction':False,'bank0_required_growth_aligned':grow,'bank0_actual_payload_spare_bytes':2,'layout':rows,'non_target_bank_reencode':False,'original_bank13_absolute_range_and_all_bytes_preserved':True,'original_bank1_through9_blocks_byte_preserved_at_new_start':True,'capsule10_through12_original_raw_count_headers_compressed_bytes_preserved':True,'capsule10_through12_only_after_end_token_tail_trimmed':trims,'already_checked':{'target_indexed_layers_exact':160,'composition_bank_boundaries_preserved':True,'part_slack':j['part_slack'],'all_other_composition_sequences_exact':True,'nonidle_target_tile_counts_not_smaller_than_parent':True,'idle1_direct_alias_to_original0':True},'evidence':[ev(c),ev(s),ev(native)],'not_yet_checked':['새 ARC 실제 조립/압축 디렉터리 readback508참조','원MIPS에서 directory 선택→모든508refs decode/upload와 main/clone/weapon/capsule bank 초기화','1024부분아머/원총열/0·141·142 및 모든 비대상 재추출','새 부팅에서 보행/사격 및 부분 업로드·무기/캡슐 회귀'],'approval_boundary':'현재승인된은행내재패킹과달리 entry2 디렉터리상대offset을 바꾼다. 이 파일은 계산과검증계획만이며 root 판단 전 자원/게임을 생성·적용하지 않았다.','artifact_generated':False,'candidate_arc_generated':False,'known_limit':'native 직접 SP+14 읽기30곳의directory사용을독립확인했으나 전프로그램간접포인터부재까지완전증명하지않았다. oldF1/실행중객체캐시를재배치검증에쓰지않는다.'}
    write(H/'base_run_relocation_readonly_proposal.json',report);print(json.dumps({'path':'base_run_relocation_readonly_proposal.json','sha256':sha((H/'base_run_relocation_readonly_proposal.json').read_bytes()),'grow':grow,'trim':trims,'entry2_length':pos}))
if __name__=='__main__':main()
