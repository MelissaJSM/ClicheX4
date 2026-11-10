"""특수88/89/97만 원화·원효과·원MIPS·독립·루트 미술 근거와 동결한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_standing_candidate_v1'
FINAL='0e69e9e3823c95bfce5b10746f77c587cd6f9e177cdd69b04938e868f3b77331';PARENT='dcaf1343747fabeab3054c59fc384c3bbd598209eccb6c5a37ac84c1d340d339'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));rel=lambda p:p.relative_to(ROOT).as_posix()
def main():
 out=P/'FROZEN.json';assert not out.exists();assert sha(P/'PL02_U.ARC')==FINAL
 proposal=read(P/'proposal.json');assert proposal['parent_arc_sha256']==PARENT and proposal['files']['PL02_U.ARC']['after']==FINAL
 ip=N.parent/'zero_audit/nana_ultimate_standing3_independent01/report.json';iv=ip.parent/'visual_review.json';assert sha(ip)=='d59467a9a07824ce58de22fe307cff1ba2047b54c3d3e41d31af758b2322fbc6';assert sha(iv)=='eeecceec721e801e591f8ad3afd562b33b356a8961c0efd17d3825eb0b6c8943'
 ij=read(ip);assert ij['passed']and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
 lockp=P/'INPUT_FROZEN.json';assert sha(lockp)==ij['input_frozen_sha256'];lock=read(lockp)
 for q in lock['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
 cp=N.parent/'root_review_checkpoint128.json';assert sha(cp)=='afeaa4b49079926b60a6a75993fbce635306f983dbfceb2c77008b3b5cda4d95';cj=read(cp);assert cj['candidate_sha256']==FINAL
 sheets=[P/f'readback_{i}.png'for i in(1,2)]+[D/'native_cycle_v2'/f'timeline_{i}.png'for i in(91,104,105)]
 for p in sheets:assert any(q['path']==rel(p)and q['sha256']==sha(p)for q in cj['root_actually_viewed'])
 proofs=[P/'verification.json',P/'reproduction.json',D/'targets_probe_v2/source_reconstruction.json',D/'native_components_v2_native_checks.json',D/'native_cycle_v2/verification.json',ip]
 for p in proofs:assert read(p)['passed'],rel(p)
 assert read(P/'verification.json')['after']==FINAL and read(P/'reproduction.json')['candidate_sha256']==FINAL
 assert read(D/'native_components_v2_native_checks.json')['resources']['PL02_U.ARC']['candidate_sha256']==FINAL
 assert read(D/'native_cycle_v2/verification.json')['candidate_arc_sha256']==FINAL
 files=list(dict.fromkeys([P/'PL02_U.ARC',P/'proposal.json',lockp,D/'targets_probe_v2/manifest.json',*proofs,iv,cp,*sheets,P/'producer_visual_review.json',D/'native_components_v2.json',D/'native_cycle_v2/manifest.json',D/'native_cycle_v2/REVIEW.html',D/'verify_reproduction.py',D/'make_native_cycle.py',D/'verify_native_cycle.py',D/'record_review.py',Path(__file__).resolve()]))
 result={'frozen':True,'status':'나나 Ultimate 새89/97 두 자세와 원효과 파생88만 동결. 다음90/91·95/96·98/99 및전체미술은별도 잔여.','character':'nana','forms':['ultimate_before','ultimate_after'],'refs':[88,89,97],'new_authored_body_keys':[89,97],'new_authored_body_form_pairs':4,'derived_effect_refs':[88],'derived_effect_form_pairs':2,'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL02_U.ARC']['before'],'files':[{'path':rel(p),'sha256':sha(p)}for p in files],'input_files_verified_unchanged':len(lock['files']),'independent_counts':ij['counts'],'root_art_review_checkpoints':[rel(cp)],'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,'source_provenance':'제작자 검증은 고정4생성셀을 재양자화하고 홍채4·팔레트15 얼굴2·커프경계8·실제의상/공통손을 재구성했다. 독립 reader는 등록원화부터15층과 실제ARC를 재구성했으며 전체생성 재양자화를 했다고 주장하지 않는다.','effect_policy':'88은 새89의 X−1,Y불변 몸체 위에 원US83texel의 world형상·색·위치를 복원했다. 현재after의 효과밖105셀은 복사하지 않는 새공통정책이다. 원tile7/8 자체주소·바이트보존을 주장하지 않고 새타일에 재패킹한다.','weapon_policy':'89/97 비사격 사선권총은 새 생성원화의 실제권총·손 의미영역을 양폼에 공유한다. 정본85를 회전한20texel모듈이라고 표현하지 않는다.','packing_policy':'기존88/89 물리공유와97 독립, 은행/항목 경계·13기타그래픽은행·팔레트·비대상 조립을 보존.32tile 제한과41GPU파트 경계를 확인했다.','reproduction':'별도프로세스 바이트일치 재현1회·잘못된입력8종 거부. 제작자 전체7296RGBA와 대상96RGBA 재현, 독립96부분RGBA/효과32조건을 구분한다.','limits':['원표91/104/105 및66canvas의 오프라인 기계재생과 정지순서5판 열람이다. 인간실시간 관찰이나 실제 게임 입력/물리/이벤트 검증을 대신하지 않는다.','90/91·98/99는 원표에 포함되지만 이전그림이다. 다음90/91 원화4셀은 별도 후보로 진행 중이다.','사다리 보류148/149/150/151/152/153/155는 부모상태를 그대로 유지하며 이번작업에 사용하지 않았다.','전체 나나 미술통일·최종사용자 수용은 미완료다.'],'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'asset':FINAL,'frozen_sha256':sha(out),'files':len(files)}))
if __name__=='__main__':main()
