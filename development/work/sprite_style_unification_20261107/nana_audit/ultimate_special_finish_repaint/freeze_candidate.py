"""Ultimate95/96/98/99의 원화·원순서·독립 검증을 동결한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_special_candidate_v1'
FINAL='56a3aeb489229d85bb72205bd14f866b4444ff5daa8e1bc7f91c82e9b3c46fc0';PARENT='ce61617f541fd59a5a3ab0b26bba6ce88cc7740bf5f9d4719c9acb129783c8d0'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));rel=lambda p:p.relative_to(ROOT).as_posix()
def main():
 out=P/'FROZEN.json';assert not out.exists();assert sha(P/'PL02_U.ARC')==FINAL
 proposal=read(P/'proposal.json');assert proposal['parent_arc_sha256']==PARENT and proposal['files']['PL02_U.ARC']['after']==FINAL
 ip=N.parent/'zero_audit/nana_ultimate_special4_independent01/report.json';iv=ip.parent/'visual_review.json';assert sha(ip)=='5fec453d68e7d0726b1d1fc4f577bf56c27ecf0327d82f88296386b82be8585d';assert sha(iv)=='5761d4af9ee4552a2da68fde696d41923669441d7fd4c1a53bef166818318da0';ij=read(ip);assert ij['passed']and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
 lockp=P/'INPUT_FROZEN.json';assert sha(lockp)==ij['input_frozen_sha256'];lock=read(lockp)
 for q in lock['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
 cp=N.parent/'root_review_checkpoint133.json';assert sha(cp)=='d3d5bd4e026970303b78c7f0598fcc23bc275bbbd84e8947462525d71084d5b9';cj=read(cp);assert cj['candidate_sha256']==FINAL
 sheets=[P/f'readback_{i}.png'for i in(1,2)]+[D/f'native_cycle_v1/timeline_{n}.png'for n in(95,96,97,104,105)]
 for p in sheets:assert any(q['path']==rel(p)and q['sha256']==sha(p)for q in cj['actually_viewed_files'])
 proofs=[P/'verification.json',P/'reproduction.json',D/'targets_v1/source_reconstruction.json',D/'native_components_v1_native_checks.json',D/'native_cycle_v1/verification.json',ip]
 for p in proofs:assert read(p)['passed'],rel(p)
 assert read(P/'verification.json')['after']==FINAL and read(P/'reproduction.json')['candidate_sha256']==FINAL
 assert read(D/'native_components_v1_native_checks.json')['resources']['PL02_U.ARC']['candidate_sha256']==FINAL and read(D/'native_cycle_v1/verification.json')['candidate_arc_sha256']==FINAL
 files=list(dict.fromkeys([P/'PL02_U.ARC',P/'proposal.json',lockp,D/'targets_v1/manifest.json',*proofs,iv,cp,*sheets,P/'producer_visual_review.json',D/'native_components_v1.json',D/'native_cycle_v1/manifest.json',D/'native_cycle_v1/REVIEW.html',D/'verify_reproduction.py',D/'make_native_cycle.py',D/'verify_native_cycle.py',D/'record_review.py',Path(__file__).resolve()]))
 result={'frozen':True,'status':'나나 Ultimate 특수95/96/98/99 네참조의 새 상세와 검증 동결. 전체 미술 완료는 아니다.','character':'nana','forms':['ultimate_before','ultimate_after'],'refs':[95,96,98,99],'new_authored_body_keys':[95,98],'new_authored_body_form_pairs':4,'derived_translation_refs':[96,99],'derived_translation_form_pairs':4,'derived_effect_refs':[],'derived_effect_form_pairs':0,'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL02_U.ARC']['before'],'files':[{'path':rel(p),'sha256':sha(p)}for p in files],'input_files_verified_unchanged':len(lock['files']),'independent_counts':ij['counts'],'root_art_review_checkpoints':[rel(cp)],'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,'source_provenance':'제작자는12생성셀을 전체고정격자로 다시 양자화하고 실제채택한95머리/몸체와98새손·53의상경계·1공통손 표본→20층을 재구성했다. 독립reader는 고정등록 이후 출처와목표/실제ARC를 별도재구성했다. 12셀은 미채택 초기원화/국소원화를 포함하며 고유몸체완료수가 아니다.','weapon_policy':'95는 새원화의 사선권총/손 표본이며 정본20texel의 회전으로 간주하지 않는다.98은 정본85의20texel을 X−3,Y+1로 옮겨 실제새손피부2셀 가림을 유지한다. 새로운 발사원점 코드를 실행해 증명한 것이 아니다.','translation_policy':'96은95,99는98을 모든5층에서 X+1한다. 원US/현재before의 관계를 새전후폼 공통정책으로 적용했으며 옛after의118/117셀차이까지 복원했다고 주장하지 않는다.','packing_policy':'원95/96·98/99 두 공유stream,은행/항목 경계·13기타그래픽은행·팔레트·비대상조립 보존. 원32tile 한도,60GPU파트 확인.','reproduction':'별도프로세스 바이트동일 재현1회와 잘못된8입력 거부. 최초7296전체RGBA·목표직접256조건(32마스크×2팔×4참조)·패킹/독립128조건(16×2×4)을 구분한다.','limits':['원표95/96/97/104/105의48canvas·상대스텝과 오프라인기계재생·정지순서판 열람이다. 실제게임 물리/입력/효과/복제체caller와 인간실시간관찰은 별도다.','차량/hover 등 전체 잔여는 별도로 계속한다.','사다리 보류148/149/150/151/152/153/155는 부모 그대로 유지하며 이번 입력으로 사용하지 않았다.'],'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'asset':FINAL,'frozen_sha256':sha(out),'files':len(files)}))
if __name__=='__main__':main()
