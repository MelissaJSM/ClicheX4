"""검증된 나나 이동32를 새 FROZEN에 고정한다. 자원/원화/포인터 쓰기 없음."""
from pathlib import Path
import json,hashlib
N=Path(__file__).resolve().parent;ROOT=N.parents[2];D=N/'ultimate_run_repaint';P=D/'packed_run_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()
FINAL='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'
def main():
 out=P/'FROZEN.json';assert not out.exists()
 assert sha(P/'PL02_U.ARC')==FINAL
 assert sha(P/'proposal.json')=='782b498fe886c24d0af732af3cec12ce99da0bfb3a0029bfcced292a3c25e5a5'
 independent=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_run_independent/report.json'
 root=ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint48.json'
 assert sha(independent)=='d86b0fe27e71f741f51c8912b2428bdbe4a918bbf39100bb60c4d3c091972291'
 assert sha(root)=='126916876d2a57dffd88374b3651baeb7d494ac65db4c31f766ade7dd21bdf99'
 ij,rj=read(independent),read(root);assert ij['passed'] and ij['candidate_sha256']==rj['nana_candidate_sha256']==FINAL
 lock=read(P/'INPUT_FROZEN.json');assert lock['candidate_sha256']==FINAL and len(lock['files'])==1841
 for q in lock['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
 for q in rj['art_review_images']:
  if 'ultimate_run_repaint/' in q['path']:assert q['root_actually_viewed'] and sha(ROOT/q['path'])==q['sha256']
 names=('verification.json','extended_verification.json','baseline_binding.json','reproduction.json')
 proofs=[P/n for n in names]+[D/'native_components_native_checks.json',D/'native_cycle_v1/verification.json',independent]
 for p in proofs:assert read(p)['passed'],rel(p)
 assert read(D/'native_components_native_checks.json')['resources']['PL02_U.ARC']['candidate_sha256']==FINAL
 assert read(P/'baseline_binding.json')['candidate_sha256']==FINAL
 assert read(P/'reproduction.json')['candidate_sha256']==FINAL
 files=[P/'PL02_U.ARC',P/'proposal.json',P/'INPUT_FROZEN.json',*proofs,root,D/'joint_native_targets_v1/manifest.json',
  *[P/f'readback_{i}.png' for i in range(1,5)],*[P/f'timeline_{i}.png' for i in (7,8,38,119,120,16,128)]]
 result={'frozen':True,'status':'나나 Ultimate 이동32 준비자원 동결. 루트 정적 미술 수용·기술/독립 검사 완료, 새 게임 통합·실기는 별도.',
  'character':'nana','forms':['ultimate_before','ultimate_after'],'refs':list(range(1,33)),
  'asset_sha256':FINAL,'parent_asset_sha256':ij['parent_sha256'],
  'original_active_asset_sha256':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa',
  'files':[{'path':rel(p),'sha256':sha(p)}for p in files],'input_files_verified_unchanged':len(lock['files']),
  'independent_counts':ij['counts'],'root_art_review_checkpoint':rel(root),'root_static_art_direction_accepted':True,
  'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,
  'independent_scope_limits':'등록64원화→160층 및 실제 ARC를 검사했다. RGB57셀/재킷48셀 의미영역 선택·생성원화 전체 재현은 독립 reader 범위 밖이며 제작 출처와 루트 미술 검토에 별도로 묶었다.',
  'reproduction':'동일 프로세스 메모리 재제작 byte-identical. 별도 출력 파일 재생성 검사는 아님.',
  'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'frozen':True,'asset_sha256':FINAL,'freeze_sha256':sha(out)}))
if __name__=='__main__':main()
