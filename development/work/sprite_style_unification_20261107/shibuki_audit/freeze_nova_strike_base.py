"""기본/포스 노바 돌진2: 원화·실제 원코드·독립·루트 검토를 동결한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
FINAL='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
def read(p):return json.loads(p.read_text('utf8'))
def check(files,base=ROOT):
    for name,h in files.items():need(sha((base/name).read_bytes())==h,'고정 파일 변경 '+name)
def images(rows):
    for r in rows:need(sha((ROOT/r['path']).read_bytes())==r['sha256'],'열람판 변경')
def main():
    d=H/'prepared_nova_strike_base01';need(not(d/'FROZEN.json').exists(),'기존 동결 보호');need(sha((d/'PL00_U.ARC').read_bytes())==FINAL,'후보 변경')
    lock=read(d/'INPUT_LOCK.json');pl=read(d/'PREPARED_LOCK.json');check(lock['files']);check(pl['files'],d);check(pl['source_scripts'],H)
    audit=H.parent/'zero_audit/shibuki_nova_strike2_independent02';ind=read(audit/'report.json');vis=read(audit/'visual_review.json');check(read(audit/'READER_LOCK.json')['files'])
    need(sha((audit/'report.json').read_bytes())=='5adddc829a9bc7531e2f474b2069f8d25e78530ff0eba7d60d01d54dbc732713','독립 결과 변경');need(ind['passed'] and ind['candidate_sha256']==FINAL,'독립 실패')
    counts=ind['counts'];want={'raw_checked':508,'non_target_raw_exact':500,'target_layers_exact':10,'non_art_layers_exact':1130,'non_target_compositions_exact':1747,'storage_full256_tiles_inverse_exact':64,'original_effect_full256_tiles_exact':18,'target_partial_RGBA_exact':64,'storage_partial_RGBA_exact':192,'GPU_target_parts':52,'GPU_storage_parts':113}
    for k,v in want.items():need(counts[k]==v,'독립 수치 '+k)
    need(ind['effects218_219_raw_layers_records_exact'] and ind['effect220']['original_US_prefix_24_records_exact'] and ind['effect220']['new_body_suffix_7_parts_exact'],'원효과/앞뒤 보존')
    need(vis['actually_viewed'] and vis['actual_images']==5 and not vis['new_confirmed_defect'],'독립 미술');images(vis['images'])
    paths=[H.parent/'zero_audit/shibuki_nova_strike2_directory_native01/report.json',H.parent/'zero_audit/shibuki_nova_strike2_renderer_native02/report.json',H.parent/'zero_audit/shibuki_nova_strike2_renderer_native02/conclusions.json',H.parent/'zero_audit/shibuki_nova_strike2_renderer_native02/LOCK.json']
    nd=read(paths[0]);nr=read(paths[1]);need(nd['passed'] and nd['candidate_sha256']==FINAL and nd['stats']['references']==508 and nd['stats']['native_decode_calls']==1016 and not nd['python_bank_pointer_injection'],'원로더 508');need(nr['passed'] and nr['candidate_sha256']==FINAL and nr['actual_calls']==136 and nr['near_capacity_fixtures']==8 and not nr['python_graphics_or_composition_pointer_injection'],'원 renderer 136/경계8')
    paths[3]=paths[3].with_name('READER_LOCK.json');check(read(paths[3])['files'])
    rp=H.parent/'root_review_checkpoint152.json';need(sha(rp.read_bytes())=='163e31d5bad5f99e21df7ecbd58584234c0b39938e5d99df66e5b614412c2bcb','루트152변경');root=read(rp);need(root['candidate_sha256']==FINAL and len(root['actually_viewed_files'])==8,'루트8판');images(root['actually_viewed_files'])
    vr=read(d/'verification.json');need(vr['passed'] and vr['total_identical_builds']==3 and vr['rejected_count']==17,'재현3/거부17')
    seq=H/'nova_strike_base_sequence01';sr=read(seq/'report.json');br=read(seq/'browser_verification.json');need(sr['original_steps']==13 and sr['new_art_steps']==5 and sr['native_table_bytes_verified'] and br['passed'] and br['canvas_form_checks']==200,'원표/브라우저')
    own=H/'nova_strike_base_components_native_checks.json';need(read(own)['passed'],'제작자 원MIPS')
    evidence=[d/'INPUT_LOCK.json',d/'PREPARED_LOCK.json',d/'verification.json',d/'author_visual_review.json',d/'post_lock_evidence.json',*[audit/n for n in('report.json','visual_review.json','evidence.json','READER_LOCK.json')],*paths,rp,own,seq/'report.json',seq/'browser_verification.json',seq/'REVIEW.html',Path(__file__)]
    write(d/'final_verification.json',{'passed':True,'candidate_sha256':FINAL,'parent_arc_sha256':lock['parent_sha256'],'selected_refs':[217,220],'storage_only_refs':[45,46,71,72,73,74],'source_files_checked':len(lock['files']),'counts':counts,'total_identical_builds':3,'rejected_inputs':17,'root_actual_images':8,'independent_actual_images':5,'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in evidence},'original_directory_refs':508,'original_renderer_conditions':136,'native_capacity_fixtures':8,'all_bank_entry_boundaries_preserved':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'GPU_rasterization_executed':False,'user_accepted':False,'full_project_complete':False,'limits':['원로더/본체·아머 renderer는 격리 RAM fixture이며 실제 전체장면·GPU래스터화·게임은 별도다.','31본체+7파츠의 packet1520/304B 및1000/1024 경계조건을 확인했으나 모든 장면의 다른 객체 사용량을 증명한 것은 아니다.','218/219는 부모 효과를 그대로 유지했다.220은 원24파트/18전체타일 뒤에 새몸7을 그리므로 가림이 새몸에 맞게 달라진다.','기본 무아머의 실제 노바 발동 가능성을 주장하지 않는다.','메모리훅 진단6182e769는7파트에서도 나타난 명령중복으로 별도 보존했으며 내부원인 미확정이다. 최종 원renderer136조건은 메모리훅 없이2회 동일 결과다.']})
    write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':FINAL,'parent_arc_sha256':lock['parent_sha256'],'selected_refs':[217,220],'storage_only_refs':[45,46,71,72,73,74],'native_and_independent_passed':True,'root_packed_partial_and_order_reviewed':True,'root_valid_actual_plates':8,'all_bank_boundaries_preserved':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False})
    print(json.dumps({'candidate':FINAL,'frozen':sha((d/'FROZEN.json').read_bytes()),'final':sha((d/'final_verification.json').read_bytes())}))
if __name__=='__main__':main()
