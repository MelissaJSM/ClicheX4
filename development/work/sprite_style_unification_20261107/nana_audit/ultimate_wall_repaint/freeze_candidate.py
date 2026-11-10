"""생산·독립·원MIPS/GPU 증거를 동일 벽 ARC에 묶어 동결한다."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path.insert(0,str(D.parent/'native_restore'))
from preview_restore import digest,write,need
def main():
 out=D/'packed_wall_candidate_v1';dest=out/'FROZEN.json';need(not dest.exists(),'Already frozen');expected='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031';need(digest(out/'PL02_U.ARC')==expected,'Candidate SHA')
 ind=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_wall_independent/nana_ultimate_wall12.json';need(digest(ind)=='868be301184c30dc1083c05b7aa660a7430b819c7544674cad786689dcac7629','Independent SHA');native=ROOT/'work/sprite_style_unification_20261107/rn_pending_v10_wall_native_checks.json'
 checks=[out/'verification.json',out/'extended_verification.json',out/'baseline_binding.json',D/'native_cycle_v2/verification.json',ind,native]
 for p in checks:need(json.loads(p.read_text('utf8'))['passed'],'Failed evidence '+str(p))
 need(json.loads(native.read_text('utf8'))['resources']['PL02_U.ARC']['candidate_sha256']==expected,'Native resource')
 paths=[out/'PL02_U.ARC',out/'proposal.json',*checks,D/'joint_native_targets_v1/manifest.json',D/'native_cycle_v2/manifest.json',D/'native_cycle_v2/REVIEW.html',D/'pack_native.py',D/'prepare_native_targets.py',D/'register_firing_joint.py',D/'register_skin_material.py']
 paths += [D/f'{p}/generation.json'for p in('before_a_v1','before_b_v1','after_a_v1','after_b_v1','firing_a_before_v1','firing_b_before_v1','firing_a_after_v1','firing_b_after_v1')]
 write(dest,{'frozen':True,'character':'nana','forms':['ultimate_before','ultimate_after'],'refs':list(range(55,67)),'asset_sha256':expected,'parent_asset_sha256':'122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18','original_active_asset_sha256':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in paths],'producer_reproduction_passed':True,'producer_7296_RGBA_passed':True,'independent_readback_passed':True,'independent_384_target_RGBA_checked':True,'original_muzzle_192_checked':True,'offline_canvas_90_exact':True,'offline_play_pause_8_cases':True,'root_native_mips_gpu_passed_separately':True,'no_new_bank_dedup_or_relocation':True,'source_material_registration':'맨팔 원화 갈색 명암29px를 피부/회색 CLUT로 분류, 원화RGB좌표 기록. 신규색/단색채움 없음.','shared_silhouette':'새 맨팔 경계11px만 새 재킷 외곽 안으로 제한; 옛 알파 사용 없음.','art_review':'루트 최종 재추출2장 미술 방향 수용. 제작자2장·브라우저57/64 실제 열람. 독립 담당도2장 열람.','gameplay_verified_here':False,'all_nana_art_complete':False});print(digest(dest))
if __name__=='__main__':main()
