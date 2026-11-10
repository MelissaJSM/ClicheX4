"""Ultimate 승리4의 실제 검증 근거를 묶어 불변 동결한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=D/'packed_victory_candidate_v1'
FINAL='b7dcf46dba35084265e8b32529d7a4d072108ed201a60ba4f17fcc71494aa1c5'
PARENT='c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
 out=P/'FROZEN.json';assert not out.exists(),'기존 동결 덮어쓰기 거부'
 assert sha(P/'PL02_U.ARC')==FINAL
 proposal=read(P/'proposal.json');assert proposal['parent_arc_sha256']==PARENT
 assert proposal['files']['PL02_U.ARC']['after']==FINAL
 independent=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_victory4_independent01/report.json'
 assert sha(independent)=='f3cfb9419b6d2366fbe048ac299e5000b29244e0d5bbeb48fe544aa4aef0d082'
 iv=independent.parent/'visual_review.json';assert sha(iv)=='bae587120445cdb933074dee9b3b48f7259f768131910ce58f89b88382f58605'
 ij=read(independent);assert ij['passed'] and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
 lockpath=P/'INPUT_FROZEN.json';assert sha(lockpath)==ij['input_lock_sha256'];lock=read(lockpath);assert lock['candidate_sha256']==FINAL
 for q in lock['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
 target=D/'final_targets_v1/manifest.json';assert sha(target)==ij['target_manifest_sha256']
 cp=ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint112.json';assert sha(cp)=='110e710193a0abd8590e3d5aa22924e678c7365c4354676534dba8f1714af612';assert read(cp)['arc_sha256']==FINAL
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
 result={'frozen':True,'status':'나나 Ultimate 승리4 준비본 동결. 통합 BIN 및 실제 스테이지 클리어는 별도.','character':'nana','forms':['ultimate_before','ultimate_after','partial_masks_arm1_arm2'],'refs':[204,205,206,207],'new_authored_body_keys':[204,205,206,207],'derived_body_effect_refs':[],'preserved_related_refs':[81,89,156,157,158,159,160],
  'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL02_U.ARC']['before'],'files':[{'path':rel(p),'sha256':sha(p)}for p in files],'input_files_verified_unchanged':len(lock['files']),'independent_counts':ij['counts'],'root_art_review_checkpoints':[rel(cp)],'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,
  'reproduction':'별도 프로세스 재제작 byte-exact, 잘못된 입력8종 거부. 최초7296RGBA와 재현128목표RGBA/전체raw·층·조립 검사는 별도 범위다.',
  'body_provenance':'두 생성 원화의8개 고정 셀을 전체 캔버스 비율로 등록. 신규 의상 의미영역과 머리2셀 제외, 정본20texel 권총4변환 및 피부가림을 재구성했다. 옛 머리/단색 채움/전신 확대 없음.',
  'gesture_policy':'204 가슴 앞 빈손,205 빈손 경례,206 뺨 옆 권총,207 머리 위 권총. 역사 원화의 각기 다른 자세 유지. 8px 사랑이와 손 접점만 정본 모듈로 맞춘다.',
  'effect_policy':'204..207 별도 효과 없음. 원표39 event80/relative0 및 원표40 귀환 타이밍·실행코드 불변.',
  'shared_ownership_policy':'207 layer5와89의 기존 레코드 주소 공유를 분리하여89 전체조립/표시 보존. 비대상 빈층 소유도 전수 exact이며 고정 은행/원팔레트/소리/다른 엔트리 보존.',
  'limits':['귀환156..160은 부모 그림을 그대로 보존했으며 이번 승리 완료에 포함하지 않는다.156 새 원화는 별도 경로에서 제작 중이다.','원표39/40 및 수동연결 66canvas 기계재생·정적 직접 열람이다.60호출/초 가정과 상대스텝을 검증했으나 실제게임 이벤트·물리·호출자·사람의 실시간 관찰은 별도다.','독립128부분RGBA와 제작자7296RGBA는 서로 다른 검사 범위다.','전체 나나 미술 통일/최종 사용자 수용이 아니다.'],'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'asset':FINAL,'frozen_sha256':sha(out),'files':len(files)}))
if __name__=='__main__':main()
