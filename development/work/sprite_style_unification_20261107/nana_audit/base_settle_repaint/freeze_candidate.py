"""기본/포스138139의 출처·독립·원MIPS·최종미술근거를 동결한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_settle_candidate_v1'
FINAL='15d01f06aee14e3264d7ce41d1358a530147e4a3464d3ac949b64cde5085a775'
PARENT='87cc15efefedd475e0de972587995ad351d3ded1bd38a5c5096d5a3ab441748e'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()
def main():
 out=P/'FROZEN.json';assert not out.exists(),'동결 덮기거부';assert sha(P/'PL00_U.ARC')==FINAL
 proposal=read(P/'proposal.json');assert proposal['parent_arc_sha256']==PARENT and proposal['files']['PL00_U.ARC']['after']==FINAL
 ip=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_base_settle2_independent01/report.json';iv=ip.parent/'visual_review.json'
 assert sha(ip)=='bc5269ec1e23fb2823b254303da1a83b4b21724d33fa48c989c1e060d621489c';assert sha(iv)=='f6c67b2270092bdd06ad7a5c23aa563296b6a5f72df39c813792f0eee5ae6951'
 ij=read(ip);assert ij['passed'] and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
 lockp=P/'INPUT_FROZEN.json';assert sha(lockp)==ij['source_lock_sha256'];lock=read(lockp)
 for q in lock['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
 cp=ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint119.json';assert sha(cp)=='f54f75efce2e90b39c9bce14d7806c1fd8f77cec3de33c2b9b977b7ef5d86eb6';cj=read(cp);assert cj['arc_sha256']==FINAL
 viewed=[]
 for q in cj['root_actually_viewed']:
  f=ROOT/q['path'];assert sha(f)==q['sha256'];viewed.append(f)
 proofs=[P/'verification.json',P/'reproduction.json',D/'source_reconstruction_v2.json',D/'native_components_v1_native_checks.json',D/'native_cycle_v1/verification.json',ip]
 for f in proofs:assert read(f)['passed'],rel(f)
 assert read(P/'verification.json')['after']==FINAL
 assert read(P/'reproduction.json')['candidate_sha256']==FINAL
 assert read(D/'native_components_v1_native_checks.json')['resources']['PL00_U.ARC']['candidate_sha256']==FINAL
 assert read(D/'native_cycle_v1/verification.json')['candidate_arc_sha256']==FINAL
 files=list(dict.fromkeys([P/'PL00_U.ARC',P/'proposal.json',lockp,D/'joint_layers_probe_v3/manifest.json',*proofs,iv,cp,*viewed,D/'native_components_v1.json',D/'native_cycle_v1/manifest.json',D/'native_cycle_v1/REVIEW.html',D/'verify_reproduction.py',D/'make_native_cycle.py',D/'verify_native_cycle.py',Path(__file__).resolve()]))
 result={'frozen':True,'status':'나나 기본/포스138/139 준비본 동결. 새138 한 자세×2의상 및139 y−1 파생이며 실제게임의 새138139 관측은 별도.','character':'nana','forms':['base','fourth','partial_masks_arm1_arm2'],'refs':[138,139],'new_authored_body_keys':[138],'translated_alias_refs':[139],'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL00_U.ARC']['before'],'files':[{'path':rel(f),'sha256':sha(f)}for f in files],'input_files_verified_unchanged':len(lock['files']),'independent_counts':ij['counts'],'root_art_review_checkpoints':[rel(cp)],'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,
 'body_provenance':'전신2셀을 고정96×128으로 등록한 새138. 새 포스 다리의 같은행36표본으로 공통부 실루엣을 정합하고 기본 부츠는 원화 그대로 유지했다. 새머리 국소2셀에서 기본59/포스8 내부색인만 반영했으며 머리전체알파/눈/몸/총/손발은 수정전 후보exact다.',
 'weapon_provenance':'정본85 실제20texel에 matrix[[0,1],[1,0]]+translation[2,-9]를 적용한 직교반사·이동이다. determinant−1이므로 순수90도회전으로 표현하지 않는다. 새 피부손 가림 후 새기본 손·모듈 영역을 양폼 공통화했다.',
 'layer_policy':'head5/body6/arms7/legs8 기존v2 소유맵exact. 머리 색차에 따라 구형v2의10개 대신11개 활성유색셀이 뒤베일8 배정영역에 해당한다. 원화 픽셀을 지우거나 두께를 축소해 맞추지 않았다.',
 'packing_policy':'원은행 범위·13기타그래픽은행·팔레트·소리·비대상조립 보존.138/139 각32tile예산 중17tile,각17파트. head5슬랙0B 유지이며 새head는각1파트다.',
 'reproduction':'별도프로세스 byte-exact 재현과 잘못된입력9종 거부. 제작자7296전체RGBA와 재현/독립64목표RGBA는 구분한다.',
 'limits':['126canvas의 정지화면 대조와 원표2/95/96 및 수동연결 기계재생/정지 검사다.60호출/초 가정이며 실제 게임 이벤트/물리/호출자는 미실행.','표2에 포함된133..137등 다른 기본/포스등장은 부모그림 그대로이며 이번 새제작 완료에 포함하지 않는다.','Root RN26에서 관측한138139는 이 후보 통합 이전 그림이다.','전체 나나 미술통일·최종사용자수용이 아니다.'],'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'asset':FINAL,'frozen_sha256':sha(out),'bound_files':len(files)}))
if __name__=='__main__':main()
