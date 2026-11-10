"""노바 준비4 두 자원의 고정 원화·독립·정정순서·루트 실제검토 결속."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
CFG={
 'base':{'arc':'PL00_U.ARC','final':'619032d0b81ffc50e5f5664ff1e3d0c077f226a7d5a8ccfac081be6a2126c6c5','parent':'3e11b7e6f6c58e6e175ba8a53278a8329440c160096bf89abdb9df334c3ef52d','source_count':169,'report':'240f06574fb1ee2d24e1ef40363de0e55f59ccc6ed9298f1fd5d1e2c0a3426e3','visual':'6f3c52fe367e0ff27c21bd65b653ba732ca70d49a86b2196ec6a4a2d869eaf23','evidence':'335a03566f147226c86a787975323ff583e7fd26494ad2c0780db4d26e2f74ba','reader':'45e3c5d7c1494781fef04a8276a1fff08462cb6770ab9dd771af14d819af677b','root':{147:'e0bd36d2df7b0f3bf392effe8d60b41637f48f8c5d5cec3c0a15195a5fa5a674',150:'4b398b2bd27b6a5956d0d96faf57d92fd69353175c88e78eea9df39d5ad24493'},'sequence':'nova_base_sequence02','rejects':16,'raw':508,'nonraw':494,'ownnative':14},
 'ultimate':{'arc':'PL02_U.ARC','final':'687fb27b10b9a7c13dd6d0c9fd6976dbb04f88f9b3b775f3d33482ebb7efb86f','parent':'2b8faa71d3a94bc6d52ac0e389c6121d530d6455e664ad852061c43c77789b5c','source_count':172,'report':'aedb08364c3c70fcf15e5ed61fa96e62f3a0a309cd917c2364d71af0676c9e8c','visual':'f4239f48ff11682ad78de3620766f635888dd1be81978b4ad27e94f4dbdad12d','evidence':'82e89b1853c6221b3abf045c420248519984b901383b74fe91ef70621d1e9837','reader':'b691c437072579acae43395fabb1d37922aa67ca5556302014a9528d57da8ca9','root':{149:'48f45b74504e9e7cf9a550e49af2bb609e96950bb88c2d9c9b9924219e4d41a1'},'sequence':'nova_ultimate_sequence01','rejects':14,'raw':512,'nonraw':508,'ownnative':4}}

def read(p):return json.loads(p.read_text('utf8'))
def check_files(files,base=ROOT):
    for name,h in files.items():need(sha((base/name).read_bytes())==h,'고정 파일 변경 '+name)
def check_images(items):
    for r in items:need(sha((ROOT/r['path']).read_bytes())==r['sha256'],'실제 검토판 변경 '+r['path'])

def run(kind):
    c=CFG[kind];d=H/f'prepared_nova_{kind}01';need(not(d/'FROZEN.json').exists(),'기존 동결 보호')
    need(sha((d/c['arc']).read_bytes())==c['final'],'후보 변경');need(sha((H/f'prepared_chaser_{kind}01'/c['arc']).read_bytes())==c['parent'],'부모 변경')
    source=read(d/'INPUT_LOCK.json');lock=read(d/'PREPARED_LOCK.json');check_files(source['files']);check_files(lock['files'],d);check_files(lock['source_scripts'],H);need(len(source['files'])==c['source_count'],'출처 범위')
    audit=H.parent/f'zero_audit/shibuki_nova_{kind}4_independent01';names={'report.json':'report','visual_review.json':'visual','evidence.json':'evidence','READER_LOCK.json':'reader'}
    for n,k in names.items():need(sha((audit/n).read_bytes())==c[k],'독립 근거 변경 '+n)
    ind=read(audit/'report.json');vis=read(audit/'visual_review.json');ev=read(audit/'evidence.json');rl=read(audit/'READER_LOCK.json');check_files(rl['files'])
    need(ind['passed'] and ind['candidate_sha256']==c['final'] and ind['parent_sha256']==c['parent'],'독립 후보/부모')
    need(ind['input_lock_sha256']==sha((d/'INPUT_LOCK.json').read_bytes()),'독립 원화 잠금')
    count=ind['counts'];need(count['raw_checked']==c['raw'] and count['non_target_raw_exact']==c['nonraw'] and count['target_layers_exact']==20 and count['non_art_layers_exact']==1120 and count['target_partial_RGBA_exact']==128,'독립 참조/층/부분')
    need(ind['all128_partial_single_component'] and ind['all_bank_entry_boundaries_palette_audio_exact'] and not ind['producer_functions_called'] and not ind['resources_modified'],'독립 보존/분리')
    need(vis['actually_viewed'] and vis['actual_images']==8,'독립 실제8판');check_images(vis['own_sheets']+vis['sequence_sheets'])
    need(ev['passed'] and ev['report_sha256']==c['report'] and ev['original_table106_pointer_13steps_byte_exact'] and ev['native_PNGs_reconstructed']==16,'독립 원표/16PNG')
    np=ROOT/ev['native']['path'];need(sha(np.read_bytes())==ev['native']['sha256'] and read(np)['passed'],'독립 새 원코드 검사')
    ownp=H/f'nova_{kind}_components_native_checks.json';own=read(ownp);native=own['resources'][c['arc']];checks=[z for b in native['banks']for z in b['native_decoder_checks']]
    need(own['passed'] and native['candidate_sha256']==c['final'] and len(checks)==c['ownnative'] and all(z['buffer_outside_and_unused_tail_preserved']for z in checks),'제작자 원MIPS 경계')
    vr=read(d/'verification.json');need(vr['passed'] and vr['total_identical_builds']==3 and vr['rejected_count']==c['rejects'] and not vr['pixel_reduction'],'3재현/거부')
    rootplates=[];rootpaths=[]
    for n,h in c['root'].items():
        rp=H.parent/f'root_review_checkpoint{n}.json';need(sha(rp.read_bytes())==h,'루트 검토 변경');r=read(rp);need(r['candidate_sha256']==c['final'],'루트 후보');check_images(r['actually_viewed_files']);rootpaths.append(rp)
        rootplates.extend([v for v in r['actually_viewed_files']if kind!='base' or n!=147 or '/nova_base_sequence01/'not in v['path']])
    need(len(rootplates)==8,'루트 유효 최종8판')
    seqp=H/c['sequence']/'report.json';webp=seqp.parent/'browser_verification.json';seq=read(seqp);web=read(webp)
    need(seq['native_table_bytes_verified'] and not seq['events_or_physics_reproduced'] and web['passed'] and web['calls']==100 and web['canvas_form_checks']==200 and web['native_table_report_sha256']==sha(seqp.read_bytes()),'원표/오프라인200폼')
    if kind=='base':
        need(ev['sequence_mask_correction']['old_sequence01_excluded'] and ev['sequence_mask_correction']['candidate_unchanged'],'순서 정정 분리')
        need(count['inverse_full256nibble_tiles_exact']==160 and count['storage_partial_RGBA_exact']==320 and count['GPU_target_parts']+count['GPU_storage_parts']==201,'저장 순열 전체 보존')
    else:need(count['GPU_target_parts']==64 and not ind['permutations'],'Ultimate GPU/비대상 순열 없음')
    evidence=[d/'INPUT_LOCK.json',d/'PREPARED_LOCK.json',d/'verification.json',d/'author_visual_review.json',d/'post_lock_evidence.json',*[audit/n for n in names],np,ownp,*rootpaths,seqp,webp,seqp.parent/'REVIEW.html',Path(__file__)]
    if kind=='base':evidence.append(d/'sequence_mask_correction.json')
    proof={'passed':True,'candidate_sha256':c['final'],'parent_arc_sha256':c['parent'],'selected_refs':[213,214,215,216],'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in evidence},'counts':count,'source_files_checked':len(source['files']),'independent_locked_files_checked':len(rl['files']),'total_identical_builds':3,'rejected_inputs':c['rejects'],'root_valid_actual_plates':rootplates,'independent_actual_plates':8,'original_MIPS_changed_refs':c['ownnative'],'independent_native_scope':ev['native'],'original_table_steps_exact':13,'offline_canvas_checks':200,'all_bank_entry_boundaries_palette_audio_preserved':True,'new_art_beyond216':False,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'limits':['213=214/215=216은 현재 수용 동형 제작 정책이며 원US의 서로 다른 몸체를 완전 복원했다는 의미가 아니다.','217..230의 기존몸/효과·호버는 이번 완료 범위 밖이다. 후속 원화가 생겨도 이 고정 후보에 혼합하지 않는다.','원표13단계와 오프라인100호출×2폼은 실제 게임·속도·충돌·발동조건·효과 이벤트·소리 검증이 아니다.','기본형 무아머로 노바를 정상 발동할 수 있다고 주장하지 않는다. 실제renderer는 PL00 player+A7, Ultimate217..230만 강제15다.','제작자가 기록한3재현/거부와 독립 reader의 결과 대조는 별도이며 독립 재패킹 실행으로 계산하지 않는다.']}
    if kind=='base':proof['sequence_correction']='root147 재추출/부분6판만 유효. 옛sequence01/옛browser는 잘못 강제한mask15 기대값이어서 순서 근거에서 제외하고 sequence02 및root150 두판으로 대체. ARC619032/새20층은 변경되지 않았다.'
    else:proof['native_limit']='독립 원MIPS4참조는 graphics pointer를 공급한 디코더/업로드 검사. 전체512 directory loader·실기와 구별한다.'
    write(d/'final_verification.json',proof)
    write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':c['final'],'parent_arc_sha256':c['parent'],'selected_refs':[213,214,215,216],'native_and_independent_passed':True,'root_packed_partial_and_corrected_order_reviewed':True,'root_valid_actual_plates':8,'all_bank_boundaries_preserved':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False})
    print(json.dumps({'kind':kind,'candidate':c['final'],'FROZEN':sha((d/'FROZEN.json').read_bytes()),'final_verification':sha((d/'final_verification.json').read_bytes())}))

if __name__=='__main__':run(sys.argv[1])
