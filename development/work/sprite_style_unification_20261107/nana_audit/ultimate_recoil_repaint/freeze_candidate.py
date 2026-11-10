"""Ultimate90/91의 최종 근거를 동결하며 이전 확정 자원은 변경하지 않는다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_recoil_candidate_v1'
FINAL='ce61617f541fd59a5a3ab0b26bba6ce88cc7740bf5f9d4719c9acb129783c8d0';PARENT='0e69e9e3823c95bfce5b10746f77c587cd6f9e177cdd69b04938e868f3b77331'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));rel=lambda p:p.relative_to(ROOT).as_posix()
def main():
 out=P/'FROZEN.json';assert not out.exists();assert sha(P/'PL02_U.ARC')==FINAL
 proposal=read(P/'proposal.json');assert proposal['parent_arc_sha256']==PARENT and proposal['files']['PL02_U.ARC']['after']==FINAL
 ip=N.parent/'zero_audit/nana_ultimate_recoil2_independent01/report.json';iv=ip.parent/'visual_review.json';assert sha(ip)=='23f3e3ac616af0cd41b1518c5d0f9826e76791d729729878ca7cad1b73f8aea9';assert sha(iv)=='672262917d0a3e1711603c4b7e322a066345e95057091ddaec9e92be23f3bfc7'
 ij=read(ip);assert ij['passed'] and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
 lockp=P/'INPUT_FROZEN.json';assert sha(lockp)==ij['input_frozen_sha256'];lock=read(lockp)
 for q in lock['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
 cp=N.parent/'root_review_checkpoint130.json';assert sha(cp)=='3b92b8832e2e5717172fff9789eb9ce98b13807729f61c3f4a210dcef586462d';cj=read(cp);assert cj['candidate_sha256']==FINAL
 sheets=[P/'readback_1.png',D/'native_cycle_v1/timeline_91.png']
 for p in sheets:assert any(q['path']==rel(p) and q['sha256']==sha(p) for q in cj['root_actually_viewed'])
 proofs=[P/'verification.json',P/'reproduction.json',D/'targets_v1/source_reconstruction.json',D/'native_components_v1_native_checks.json',D/'native_cycle_v1/verification.json',ip]
 for p in proofs:assert read(p)['passed'],rel(p)
 assert read(P/'verification.json')['after']==FINAL and read(P/'reproduction.json')['candidate_sha256']==FINAL
 assert read(D/'native_components_v1_native_checks.json')['resources']['PL02_U.ARC']['candidate_sha256']==FINAL
 assert read(D/'native_cycle_v1/verification.json')['candidate_arc_sha256']==FINAL
 files=list(dict.fromkeys([P/'PL02_U.ARC',P/'proposal.json',lockp,D/'targets_v1/manifest.json',*proofs,iv,cp,*sheets,P/'producer_visual_review.json',D/'native_components_v1.json',D/'native_cycle_v1/manifest.json',D/'native_cycle_v1/REVIEW.html',D/'verify_reproduction.py',D/'make_native_cycle.py',D/'verify_native_cycle.py',D/'record_review.py',Path(__file__).resolve()]))
 result={'frozen':True,'status':'나나 Ultimate90/91 두 연결자세의 새 원화와 검증 동결. 전체 미술 완료는 아님.','character':'nana','forms':['ultimate_before','ultimate_after'],'refs':[90,91],'new_authored_body_keys':[90,91],'new_authored_body_form_pairs':4,'derived_effect_refs':[],'derived_effect_form_pairs':0,'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL02_U.ARC']['before'],'files':[{'path':rel(p),'sha256':sha(p)}for p in files],'input_files_verified_unchanged':len(lock['files']),'independent_counts':ij['counts'],'root_art_review_checkpoints':[rel(cp)],'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,'source_provenance':'고정4생성셀 재양자화→홍채2·팔레트15 실제표본1·의상경계19셀→권총/공통피부→10층을 제작자와 독립 reader가 각각 재구성했다.','weapon_policy':'90 사선권총은 새 원화의 총과 손을 공유한다.91은 수용된 정본85의20texel을 X−2,Y불변으로 옮겨 실제 피부 가림을 보존한다.91 단독 발사발생·원US 총구좌표를 증명한 것이 아니다.','source_policy_clarification':'고정 common_probe_v2 manifest의 실제원91총구위치라는 과한 표현은 targets_v1/manifest와 이 최종기록의 정본모듈 정합 정책으로 제한한다. 과거 증거 파일 자체는 변경하지 않았다.','packing_policy':'90/91 원 독립stream·은행과 항목 경계·13기타그래픽은행·팔레트·비대상 조립을 보존. 원32tile 한도와27GPU파트 확인.','reproduction':'별도프로세스 바이트일치 재현1회 및 잘못된 입력8종 거부. 최초전체7296RGBA와 대상64RGBA 재현·독립64조건을 구분한다.','limits':['원표91의42canvas·상대스텝과 오프라인 기계재생 및 정지순서판 열람이다. 인간실시간 관찰이나 실제 게임 입력/물리/이벤트 검증이 아니다.','다음95/96·98/99와 차량 등 전체 잔여는 별도다.','사다리 보류148/149/150/151/152/153/155는 부모 그대로 유지하며 입력으로도 사용하지 않았다.'],'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'asset':FINAL,'frozen_sha256':sha(out),'files':len(files)}))
if __name__=='__main__':main()
