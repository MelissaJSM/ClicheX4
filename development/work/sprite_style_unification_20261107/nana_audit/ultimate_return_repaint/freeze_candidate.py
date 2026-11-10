"""Ultimate 귀환3의 최종 원화·독립·native·루트 열람을 불변 동결한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=D/'packed_return_candidate_v1'
FINAL='493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29'
PARENT='b7dcf46dba35084265e8b32529d7a4d072108ed201a60ba4f17fcc71494aa1c5'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
 out=P/'FROZEN.json';assert not out.exists(),'기존 동결 덮어쓰기 거부'
 assert sha(P/'PL02_U.ARC')==FINAL
 proposal=read(P/'proposal.json');assert proposal['parent_arc_sha256']==PARENT
 assert proposal['files']['PL02_U.ARC']['after']==FINAL
 independent=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_return3_independent01/report.json'
 assert sha(independent)=='e13407379ca22f52efe8630a138f958aaccbc93ae85a9754ec41577c525cdff3'
 iv=independent.parent/'visual_review.json';assert sha(iv)=='b54fcf8be75a8ce3223300a5392df11f2b1d6732c5d3f3e3bae8a08e5e54af6e'
 ij=read(independent);assert ij['passed'] and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
 lockpath=P/'INPUT_FROZEN.json';assert sha(lockpath)==ij['input_lock_sha256'];lock=read(lockpath);assert lock['candidate_sha256']==FINAL
 for q in lock['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
 target=D/'final_targets_v1/manifest.json';assert sha(target)==ij['target_manifest_sha256']
 cp=ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint115.json';assert sha(cp)=='ace37b9012cc8de6891c727c2976367270d90b2824cb040c84f2683f72624e8f';assert read(cp)['arc_sha256']==FINAL
 viewed=[]
 for q in read(cp)['root_actually_viewed']:
  p=ROOT/q['path'];assert sha(p)==q['sha256'];viewed.append(p)
 proofs=[P/'verification.json',P/'source_reconstruction.json',P/'reproduction.json',D/'native_components_v1_native_checks.json',D/'native_cycle_v1/verification.json',independent]
 for p in proofs:assert read(p)['passed'],rel(p)
 assert read(P/'verification.json')['after']==FINAL
 assert read(P/'reproduction.json')['candidate_sha256']==FINAL
 assert read(D/'native_components_v1_native_checks.json')['resources']['PL02_U.ARC']['candidate_sha256']==FINAL
 assert read(D/'native_cycle_v1/verification.json')['candidate_arc_sha256']==FINAL
 files=list(dict.fromkeys([P/'PL02_U.ARC',P/'proposal.json',lockpath,target,*proofs,iv,cp,*viewed,D/'native_components_v1.json',D/'native_cycle_v1/manifest.json',D/'native_cycle_v1/REVIEW.html',D/'verify_sources.py',D/'verify_reproduction.py',D/'make_native_cycle.py',D/'verify_native_cycle.py',Path(__file__).resolve()]))
 result={'frozen':True,'status':'나나 Ultimate 귀환3 준비본 동결. 새156 한 몸체×2의상 및157/158 효과 파생이며 실제 귀환 실기는 별도.','character':'nana','forms':['ultimate_before','ultimate_after','partial_masks_arm1_arm2'],'refs':[156,157,158],'new_authored_body_keys':[156],'derived_body_effect_refs':[157,158],'preserved_related_refs':[0,81,88,89,142,159,160,204,205,206,207],
 'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL02_U.ARC']['before'],'files':[{'path':rel(p),'sha256':sha(p)}for p in files],'input_files_verified_unchanged':len(lock['files']),'independent_counts':ij['counts'],'root_art_review_checkpoints':[rel(cp)],'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,
 'reproduction':'별도 프로세스 byte-exact 재제작 및 잘못된 입력8종 거부. 최초7296RGBA와 재현96목표RGBA/전체raw·층·조립은 다른 검사 범위다.',
 'body_provenance':'1536×1024 전신 원화2셀과 국소 의상 원화1셀을 고정96×128으로 등록. 후폼 허리40셀만 x+4 강체 정합하며 머리/팔/다리/눈/바닥은 첫 새몸체를 보존. 첫 원화의(5,5) 어두운 의상 경계는64표본 중30불투명 실제 RGB 색인1로 등록한1셀이다. donor(3,8) 다리는 의상 영역에서 제외했다.',
 'gesture_policy':'가슴 앞 빈손 두 팔과 짧게 굽힌 원래 귀환 자세 유지.156에는 권총을 추가하지 않았다.',
 'effect_policy':'157은 각 새156 y−1과Chebyshev1/2 외곽이며158은 각 새156 y−10 에너지 색인 변환+역사159의1875px 원에너지다. 구형 after guard1셀 및 구형 before alpha는 복사하지 않았다.159/160 원표시·타일은 불변.',
 'shared_ownership_policy':'156의빈층은0/142와,158의빈층은88/89와기존주소공유한다. 비대상 전체조립·raw·표시를 보존했으며 고정은행/팔레트/음향/다른항목도 불변이다.158의base는부모처럼18파트이며16개로잘라맞추지않았다.',
 'limits':['원표39/40 및 수동연결 66canvas 기계재생과 정적 직접 열람이다.60호출/초 가정·상대스텝을 확인했지만 실제게임 이벤트/물리/호출자 및 사람의 실시간 관찰은 별도다.','독립96부분RGBA와 제작자7296RGBA는 서로 다른 검사 범위다.','전체 나나 미술 통일/최종 사용자 수용이 아니다.'],'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'asset':FINAL,'frozen_sha256':sha(out),'files':len(files)}))
if __name__=='__main__':main()
