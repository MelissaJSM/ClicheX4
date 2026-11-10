"""Ultimate 호버10의 고정 원화·독립·원코드·최종 열람 근거를 결속한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent; ROOT=H.parents[2]; sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
FINAL='3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba'
def read(p):return json.loads(p.read_text('utf8'))
def check(files,base=ROOT):
    if isinstance(files,list):
        images(files); return
    for name,h in files.items():need(sha((base/name).read_bytes())==h,'고정 파일 변경 '+name)
def images(rows):
    for row in rows:need(sha((ROOT/row['path']).read_bytes())==row['sha256'],'열람 이미지 변경 '+row['path'])
def main():
    d=H/'prepared_hover_ultimate01'; need(not(d/'FROZEN.json').exists(),'기존 동결 보호')
    need(sha((d/'PL02_U.ARC').read_bytes())==FINAL,'후보 변경')
    il=read(d/'INPUT_LOCK.json'); pl=read(d/'PREPARED_LOCK.json'); check(il['files']); check(pl['files'],d); check(pl['source_scripts'],H)
    a=H.parent/'zero_audit/shibuki_ultimate_hover10_independent01'; peer=H.parent/'nana_audit/shibuki_ultimate_hover_body_source_independent01'
    need(sha((a/'report.json').read_bytes())=='ddfcaa28f2871a663275d5990e6f26685bf8eff7cc02484c0135cd87549f0b3f','독립 보고 변경')
    need(sha((a/'conclusions.json').read_bytes())=='2f2443a4ca7b26a371fd9ab95abc1eda579220c788fd5a28a030c10bfbe3b75c','독립 결론 변경')
    check(read(a/'READER_LOCK.json')['files']); check(read(peer/'READER_LOCK.json')['files'])
    ind=read(a/'report.json'); con=read(a/'conclusions.json'); vis=read(a/'visual_review.json'); body=read(peer/'report.json')
    need(all(v['passed'] and v['candidate_sha256']==FINAL and v['parent_sha256']==il['parent_sha256'] for v in (ind,con,body)),'독립 후보 불일치')
    expected={'raw_checked':512,'non_target_raw_exact':502,'non_target_layers_exact':1090,'target_layers_exact':50,'non_target_compositions_exact':1741,'GPU_parts':97,'target_partial_RGBA_exact':320,'canonical_RGBA_conditions':160}
    need(ind['counts']==expected,'독립 수치'); need(len(ind['generated_shot_fixed_cells_direct_requantized'])==6 and len(body['final_layers'])==5 and con['peer_reconstructed25_to_final_targets_checked_here'],'원화 직접 재구성')
    for k in ('empty678_preserved','body_shot_lower5_pair_exact','original_jet_6fulltiles_30parts_exact','original_lemon7_fulltiles_records_exact','entry_bank_boundaries_palette_audio_exact','native_producer10_raw_hashes_bound'):need(ind[k],k)
    need(ind['actual_mask']==15 and vis['actually_viewed'] and len(vis['directly_viewed_final_boards'])==11 and len(vis['directly_viewed_generated_shot_sources'])==3,'독립 실제 열람')
    images(vis['directly_viewed_final_boards']); images(vis['directly_viewed_generated_shot_sources']); images([vis['body_source_review_by_peer']])
    rp=H.parent/'root_review_checkpoint159.json'; need(sha(rp.read_bytes())=='dfc3880517e7b984859bfec47d5aab926aa8b785fdd4f7a056f225348f287e26','Root 검토 변경'); rr=read(rp)
    need(rr['candidate_sha256']==FINAL and len(rr['actually_viewed_files'])==11,'Root 최종11판'); images(rr['actually_viewed_files'])
    vr=read(d/'verification.json'); need(vr['passed'] and vr['candidate_sha256']==FINAL and vr['total_identical_builds']==3 and vr['rejected_count']==18 and not vr['pixel_reduction'],'재현/거부')
    np=H/'hover_ultimate_components_native_checks.json'; native=read(np); nr=native['resources']['PL02_U.ARC']; cc=[v for b in nr['banks'] for v in b['native_decoder_checks']]
    need(native['passed'] and nr['candidate_sha256']==FINAL and len(cc)==10 and all(v['buffer_outside_and_unused_tail_preserved'] for v in cc),'원MIPS10')
    seq=H/'hover_ultimate_sequence01'; sr=read(seq/'report.json'); br=read(seq/'browser_verification.json')
    need(sr['candidate_sha256']==FINAL and sr['native_table_bytes_verified'] and sr['original_player_step_count']==34 and sr['original_jet_step_count']==15 and br['passed'] and br['calls']==1500 and br['canvas_checks']==3000 and not br['errors'] and not br['external_requests'],'원순서')
    need(all(v==15 for k,v in sr['effective_masks'].items() if 221<=int(k)<=230),'실제 mask15')
    check(read(d/'post_lock_evidence.json')['evidence']); av=read(d/'author_visual_review.json'); need(av['actually_viewed'] and av['actual_images']==22 and not av['new_confirmed_defect'],'제작자 열람'); images(av['images'])
    ev=[d/n for n in ('INPUT_LOCK.json','PREPARED_LOCK.json','verification.json','post_lock_evidence.json','author_visual_review.json')]+[a/n for n in ('report.json','visual_review.json','conclusions.json','READER_LOCK.json')]+[peer/n for n in ('report.json','visual_review.json','READER_LOCK.json')]+[np,rp,seq/'report.json',seq/'browser_verification.json',seq/'REVIEW.html',Path(__file__)]
    write(d/'final_verification.json',{'passed':True,'candidate_sha256':FINAL,'parent_arc_sha256':il['parent_sha256'],'selected_refs':list(range(221,231)),'source_files_checked':len(il['files']),'counts':expected,'new_unique_bodies':5,'new_firing_arms':5,'source_fixed_cells_with_corrections':13,'total_identical_builds':3,'rejected_inputs':18,'root_actual_images':11,'independent_final_boards':11,'independent_generated_shot_sources':3,'independent_body_source_peer_separate':True,'author_actual_images':22,'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in ev},'original_MIPS_changed_refs':10,'all_bank_entry_boundaries_palette_audio_preserved':True,'actual_engine_mask':15,'actual_body_costume':'accepted Ultimate after','supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'limits':['비사격5몸/221국소2와 사격5팔/222국소1의 합13고정셀을 두 독립 reader가 직접 재양자화했다. 원화13장이나 고유포즈13개라는 뜻은 아니다.','원MIPS10은 graphics 포인터를 공급한 디코더/업로드 검사다. 전체 로더·실제 GPU 래스터화·게임 실행은 별도다.','실제 Ultimate 호버는 mask15이다. 320부분RGBA는 회귀 진단이고 mask0 반쪽 그림을 실제 결함으로 세지 않는다.','원래 제트15위상/6전체타일·탄환7·발사점5좌표를 보존한다. 중립색 효과 합성은 실제 CLUT/반투명/동시 타이밍의 실기 증거가 아니다.','원표12+제트5의1500호출/3000canvas는 독립적인 오프라인 분기 검사다. 호버 입력조건·물리·탄환 이동·60Hz 실행을 재현하지 않았다.','221 높은 손의 원외곽 대비1px 차이는 유지한다. Root159의222/228 손목 확인을 포함해 정적 후보를 수용했으며 전체 미술·사용자 최종수용을 뜻하지 않는다.','기술 report의 actually_viewed=false와 초기 pending 표시는 작성 당시 기록으로 보존하고 별도 최종 visual/conclusions 및 이 파일에서 완료한 검토만 결속한다.']})
    write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes()) for p in sorted(d.iterdir()) if p.is_file() and p.name!='FROZEN.json'},'candidate_sha256':FINAL,'parent_arc_sha256':il['parent_sha256'],'selected_refs':list(range(221,231)),'native_and_independent_passed':True,'root_packed_ownership_and_order_reviewed':True,'root_valid_actual_plates':11,'all_bank_boundaries_preserved':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False})
    print(json.dumps({'candidate':FINAL,'frozen':sha((d/'FROZEN.json').read_bytes()),'final':sha((d/'final_verification.json').read_bytes())}))
if __name__=='__main__':main()
