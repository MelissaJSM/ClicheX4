"""허용 사다리5몸체+2반전만 독립·미술·원MIPS 근거와 동결한다."""
from pathlib import Path
import hashlib,json,sys
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_first7_diagnostic_v1'
FINAL='dcaf1343747fabeab3054c59fc384c3bbd598209eccb6c5a37ac84c1d340d339'
PARENT='493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()
def main():
 out=P/'FROZEN.json';assert not out.exists(),'동결 덮기 거부'
 assert sha(P/'PL02_U.ARC')==FINAL
 proposal=read(P/'proposal.json');assert proposal['parent_arc_sha256']==PARENT and proposal['files']['PL02_U.ARC']['after']==FINAL
 ip=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_ladder_first7_independent01/report.json';iv=ip.parent/'visual_review.json'
 assert sha(ip)=='d232b998b34cccfaa0069b88a243aa436ac09dbc39b51fff9cc1202bc61258ab'
 assert sha(iv)=='9e312ccdb9e089d7a8f7c314ab23363c5c8796a4665c64cfaa0a5768dc21d542'
 ij=read(ip);assert ij['passed'] and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
 lockp=P/'INPUT_FROZEN.json';assert sha(lockp)==ij['input_lock_sha256'];lock=read(lockp)
 for q in lock['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
 cp=Path(sys.argv[1]).resolve();assert sha(cp)==sys.argv[2];cj=read(cp)
 assert FINAL in json.dumps(cj),'미술 검토의 최종 자원 결속 필요'
 expected=[P/f'readback_{i}.png' for i in range(1,4)]
 for f in expected:
  assert rel(f) in json.dumps(cj) and sha(f) in json.dumps(cj),'최종 재추출3판 실제열람 결속 필요'
 proofs=[P/'verification.json',P/'reproduction.json',D/'a_layers_probe_v1/source_reconstruction.json',D/'first7_targets_v1/source_reconstruction.json',D/'native_first7_components_v1_native_checks.json',D/'first7_native_cycle_v1/verification.json',ip]
 for f in proofs:assert read(f)['passed'],rel(f)
 assert read(P/'verification.json')['after']==FINAL
 assert read(P/'reproduction.json')['candidate_sha256']==FINAL
 assert read(D/'native_first7_components_v1_native_checks.json')['resources']['PL02_U.ARC']['candidate_sha256']==FINAL
 assert read(D/'first7_native_cycle_v1/verification.json')['candidate_arc_sha256']==FINAL
 sheets=expected+[D/'first7_native_cycle_v1'/f'timeline_{n}.png' for n in range(27,33)]
 files=list(dict.fromkeys([P/'PL02_U.ARC',P/'proposal.json',lockp,D/'first7_targets_v1/manifest.json',*proofs,iv,cp,*sheets,D/'native_first7_components_v1.json',D/'first7_native_cycle_v1/manifest.json',D/'first7_native_cycle_v1/REVIEW.html',D/'verify_first7_reproduction.py',D/'make_first7_cycle.py',D/'verify_first7_cycle.py',Path(__file__).resolve()]))
 result={'frozen':True,'status':'나나 Ultimate 허용 사다리7참조만 동결. 나머지7참조는 보류·부모 보존. 사다리14 전체완료가 아니다.',
 'character':'nana','forms':['ultimate_before','ultimate_after'],'refs':[143,144,145,146,147,154,183],
 'new_authored_body_keys':[143,144,146,154,183],'new_authored_body_form_pairs':10,'mirrored_refs':[145,147],'mirrored_form_pairs':4,
 'remaining_unmodified_refs':[148,149,150,151,152,153,155],
 'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL02_U.ARC']['before'],
 'files':[{'path':rel(f),'sha256':sha(f)} for f in files],'input_files_verified_unchanged':len(lock['files']),'independent_counts':ij['counts'],
 'root_art_review_checkpoints':[rel(cp)],'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,
 'source_provenance':'고정셀13개를 제작자 검증에서 재양자화했다. 첫3은 새전신6+맨팔3, 마지막2는 별개 새전신4다. 독립 감사는 등록원화/실제 손6·2셀→35층→자원을 재구성했으며 생성13셀 재양자화를 수행했다는 주장은 하지 않는다.',
 'mirror_policy':'145는 새144 x=-x-1,147은 새146 x=-x. 부모 재킷 관계에 따른 새 양폼 공통화 정책이다. 기존 후폼의159/244셀 차이를 원래5층exact라 부르지 않는다.',
 'packing_policy':'원5공유그룹·은행/항목 경계·13기타그래픽은행·팔레트·소리·비대상 조립을 유지했다. 각그룹 원디코더32tile 이내이며 최대 실제소비17tile,89GPU파트 안전경계를 검증했다.',
 'reproduction':'별도 프로세스 byteexact 재현1회와 잘못된입력8종 거부. 제작자 전체7296RGBA, 목표224RGBA 및 독립의 보류7참조224RGBA 대조는 각각 구분한다.',
 'blocked_correction':{'refs':[149,151,153],'failure_path':rel(D/'b_costume_inputs_v1/generation_failure.json'),'failure_sha256':sha(D/'b_costume_inputs_v1/generation_failure.json'),'retry_performed':False,'bypass_performed':False,'affected_linked_refs':[148,150,152,155]},
 'limits':['원표27..32와78canvas의 기계 재생/정지 및 원순서6판의 제작자 정적 열람이다. 실제 게임 입력/물리/이벤트 실행이나 실시간 인간 관찰을 대신하지 않는다.','사격150/155는 기존 총/몸체가 보존되어 있으며 새 팔 제작·통과로 집계하지 않는다.','보류149/151/153 의상 교정 및 연결148/150/152/155는 미완료다. 이 동결은 재요청/우회 보정 없이 독립적으로 허용된 참조만 포함한다.','전체 나나 미술 통일·최종 사용자 수용은 미완료다.'],
 'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'all_ladder_complete':False,'game_BIN_pointer_save_written':False}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'asset':FINAL,'frozen_sha256':sha(out),'bound_files':len(files)}))
if __name__=='__main__':main()
