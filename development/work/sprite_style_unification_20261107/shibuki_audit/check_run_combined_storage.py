"""읽기 후보들의 표시·고정 entry2 용량을 합산한다. ARC 출력 없음."""
from pathlib import Path
import json,sys,struct,numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from repack_part_records_lossless import repack as repack_global
from src.psx_player import decode_stream,indexed_atlas,composition_frame,bank_offsets
from src.psx_compress import encode_stream
from probe_run_occluded_tile_union import render,decode_parts

def main():
    p=H/'prepared_dash_base01/PL00_U.ARC';a=Archive(p.read_bytes());paths=[H/'base_run_compact_flip01/result.json',H/'base_run_alpha_compact_flip01/result.json',H/'base_run_idle_alias02/result.json'];js=[json.loads(v.read_text('utf8'))for v in paths];need(len(js[0]['groups'])==len(js[1]['groups'])==16,'Incomplete probes')
    choices=[]
    for x,y in zip(js[0]['groups'],js[1]['groups']):need(x['refs']==y['refs'],'Ref order');choices.append(min((x,y),key=lambda v:v['after']))
    choices=[js[2]['shot2']]+choices[1:];changes={b:{}for b in(0,5,6,7,8)};raws={};counts={};target_layers=0
    for v in choices:
        raw=bytes.fromhex(v['raw']);count=v['count'];at=np.frombuffer(indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256);tt=[np.zeros((16,16),np.uint8)for _ in range(32)]
        for t in range(count):tt[t]=at[t//16*16:t//16*16+16,t%16*16:t%16*16+16].copy()
        for n in v['refs']:
            need(count>=a.banks[0]['frames'][n]['tile_count'],'New upload writes fewer tiles than old reference')
            raws[n]=raw;counts[n]=count
            for b in changes:
                rr=v['parts'][str(b)][str(n)];changes[b][n]=bytes.fromhex(rr);got=render(tt,decode_parts(rr));want=np.array(Image.open(H/f'base_run_complete_targets01/{n:03}_bank{b}_indices.png'));need(np.array_equal(got,want),'Target mismatch');target_layers+=1
    idle=js[2]['idle_alias'];raws[1]=bytes.fromhex(idle['raw']);counts[1]=idle['tile_count']
    for b in changes:changes[b][1]=bytes.fromhex(idle['parts'][str(b)]);need(np.array_equal(a.layer(0,b)[0],np.array(Image.open(H/f'base_run_complete_targets01/001_bank{b}_indices.png'))),'Idle alias differs');target_layers+=1
    nc=a.c;slack={};methods={};errors={}
    for b,rr in changes.items():
        try:
            try:nc,slack[b]=repack_parts(nc,b,rr);methods[b]='existing'
            except ValueError:nc,slack[b],methods[b]=repack_global(nc,b,rr)
        except ValueError as ex:errors[b]=str(ex)
    if not errors:
        for b in range(len(bank_offsets(a.c))):
            for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
                want=changes[b][n]if b in changes and n in changes[b]else records(a.c,b,n)
                need(records(nc,b,n)==want,'Repacked sequence differs')
    cache={};banks=[];seen={};cursor=56
    for bi,ba in enumerate(a.banks):
        if ba['base']in seen:
            banks.append({'bank':bi,'alias':seen[ba['base']],'planned_start':next(x['planned_start']for x in banks if x['bank']==seen[ba['base']])});continue
        seen[ba['base']]=bi;uniq={}
        for f in ba['frames']:
            if bi==0 and f['index']in raws:r=raws[f['index']];count=counts[f['index']]
            else:r=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;count=f['tile_count']
            key=(r,count)
            if key not in cache:cache[key]=encode_stream(r)
            uniq[key]=len(cache[key])
        header=len(ba['frames'])*4;needspan=header+sum(uniq.values());aligned=(needspan+3)//4*4;oldspan=ba['end']-ba['base']
        banks.append({'bank':bi,'old_start':ba['base'],'old_end':ba['end'],'old_span':oldspan,'header':header,'unique_streams':len(uniq),'payload':sum(uniq.values()),'required_unaligned':needspan,'required_aligned':aligned,'planned_start':cursor,'planned_end':cursor+aligned,'fixed_bank_slack':oldspan-needspan});cursor+=aligned
    minimal=[];pos=56;seen_min={}
    for bi,ba in enumerate(a.banks):
        if ba['base']in seen_min:minimal.append({'bank':bi,'alias':seen_min[ba['base']],'planned_start':next(x['planned_start']for x in minimal if x['bank']==seen_min[ba['base']])});continue
        seen_min[ba['base']]=bi
        if bi==0:length=banks[0]['required_aligned'];policy='new_selected_art_exact_global_raw_sharing'
        elif bi<10:length=ba['end']-ba['base'];policy='entire_original_bank_block_exact'
        else:
            end=max(decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).end for f in ba['frames']);length=(end-ba['base']+3)//4*4;policy='all_original_header_and_compressed_streams_exact_tail_only'
        minimal.append({'bank':bi,'old_start':ba['base'],'old_span':ba['end']-ba['base'],'planned_start':pos,'planned_end':pos+length,'planned_span':length,'policy':policy});pos+=length
    report={'analysis_only':True,'resource_written':False,'source':{'path':str(p.relative_to(ROOT)),'sha256':sha(a.data)},'evidence':[{'path':v.relative_to(ROOT).as_posix(),'sha256':sha(v.read_bytes())}for v in paths],'target_lock_sha256':sha((H/'base_run_complete_targets01/LOCK.json').read_bytes()),'exact_target_layers':target_layers,'selected_refs':sorted(raws),'selected_tile_counts':counts,'idle1_reuses_original0_raw_without_changing0_or141_or142':True,'nonidle_target_upload_count_at_least_old':True,'part_slack':slack,'part_methods':methods,'part_errors':errors,'banks':banks,'fixed_entry2_length':len(a.g),'planned_used_length':cursor,'fixed_entry2_slack':len(a.g)-cursor,'minimal_other_bank_change_plan':{'banks':minimal,'used_length':pos,'entry2_slack':len(a.g)-pos,'other_banks_reencoded':False,'only_capsule_banks10_through13_tail_shortened':True},'all_non_target_raw_would_be_exact':True,'directory_move_applied':False,'limitations':['실제 ARC 미생성. 직접 원화층 재합성/길이 산정만 수행.','은행 시작 directory 이동은 별도 방식 판단 전이며 아직 적용 안 함.','선택32 외 모든 raw/count는 유지하며,ref1은 기존0과 raw 공유.','선택32 업로드 타일 배치는 달라진다. 원 MIPS 및 새 부팅의 실제 전환·이펙트 확인 필요.']}
    write(H/'base_run_combined_storage_audit.json',report);print(json.dumps({k:v for k,v in report.items()if k not in('banks','evidence','limitations','selected_tile_counts')}))
if __name__=='__main__':main()
