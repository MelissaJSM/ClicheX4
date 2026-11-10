"""독립 감사·생산·루트 native 근거가 같은 자원을 가리킬 때만 공중 후보를 동결한다."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path.insert(0,str(D.parent/'native_restore'))
from preview_restore import digest,write,need
def main():
 out=D/'packed_air_candidate_v1';dest=out/'FROZEN.json';need(not dest.exists(),'Already frozen')
 expected='122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18';need(digest(out/'PL02_U.ARC')==expected,'ARC hash')
 independent=ROOT/'work/sprite_style_unification_20261107/zero_audit/checkpoint20_x_independent/nana_ultimate_air22.json'
 need(digest(independent)=='9acfa90a0bbd67902d408445c7ad0687320b25bb69ad3b345fb8b30e92727905','Independent report hash')
 native=ROOT/'work/sprite_style_unification_20261107/rn_pending_v9a_components_native_checks.json'
 checks=[out/'verification.json',out/'extended_verification.json',out/'baseline_binding.json',D/'native_cycle_v1/verification.json',independent,native]
 for p in checks:need(json.loads(p.read_text('utf8'))['passed'],'Failed evidence '+str(p))
 need(json.loads(native.read_text('utf8'))['resources']['PL02_U.ARC']['candidate_sha256']==expected,'Native evidence resource')
 paths=[out/'PL02_U.ARC',out/'proposal.json',*checks,D/'joint_native_targets_v2/manifest.json',D/'native_cycle_v1/manifest.json',D/'pack_native.py',D/'prepare_native_targets.py']
 result={'frozen':True,'character':'nana','forms':['ultimate_before','ultimate_after'],'refs':list(range(33,55)),'asset_sha256':expected,'parent_asset_sha256':'bced7f9086a9e6a72440bab25cda7e0c87ccc121a2ffbbc970f750dee257da45','original_active_asset_sha256':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in paths],'producer_reproduction_passed':True,'producer_7296_combinations_passed':True,'independent_readback_passed':True,'independent_704_target_RGBA_checked':True,'independent_original_muzzle_352_checked':True,'offline_canvas_138_exact':True,'offline_play_pause_8_cases':True,'root_native_mips_gpu_passed_separately':True,'art_readback_review':'루트 재추출4장 전체열람 및 방향수용. 제작자 목표4장·브라우저39/52 실제열람.','gameplay_verified_here':False,'all_nana_art_complete':False}
 write(dest,result);print(digest(dest))
if __name__=='__main__':main()
