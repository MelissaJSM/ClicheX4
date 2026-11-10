"""소매가 교정된 기본/포스 라이징파이어 v2의 최종 검사 연결."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'prepared_rising_fire_base02';dest=d/'FROZEN.json';need(not dest.exists(),'Already frozen');initial=json.loads((d/'INPUT_FROZEN.json').read_text('utf8'))
    for name,digest in initial['files'].items():need(sha((d/name).read_bytes())==digest,'Frozen input changed')
    for name,digest in initial['producer_scripts'].items():need(sha((H/name).read_bytes())==digest,'Producer changed')
    evidence=['work/sprite_style_unification_20261107/zero_audit/rising_independent/base_v2.json','work/sprite_style_unification_20261107/br_pending_v10_rising_native_checks.json'];reports=[json.loads((ROOT/p).read_text('utf8'))for p in evidence];need(all(r['passed']for r in reports),'Incomplete checks')
    expected='008eb1df4809fe6f8e7002604f98abbe58c885265cfa63a688105f9acf4d29ce';need(reports[0]['candidate_sha256']==expected,'Wrong independent candidate');need(reports[1]['resources']['PL00_U.ARC']['candidate_sha256']==expected,'Wrong native candidate')
    local=H/'rising103_sleeve_native03/comparison.png'
    write(dest,{'frozen':True,'files':{p:sha((d/p).read_bytes())for p in('PL00_U.ARC','proposal.json','verification.json','INPUT_FROZEN.json')},'baseline_bin_sha256':'21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a','parent_arc_sha256':'61495a2aaf002efc32492a4e12c3724a77c82b3f42464538ae1e2cc855da74c0','target_art_lock_sha256':initial['source_lock_sha256'],'selected_visual_refs':[100,101,102,103,104,231,232],'root_native_and_independent_evidence':{p:sha((ROOT/p).read_bytes())for p in evidence},'root_actual_local_visual_review':{'path':local.relative_to(ROOT).as_posix(),'sha256':sha(local.read_bytes()),'source':'루트 메시지: 새103 소매 실제 열람, 104와 맞는 검보라 접힘 후보 수용. 이어 원MIPS/GPU 통과 및 최종 동결 지시.'},'author_actual_packed_review':{'six_readback_sheets':True,'mask103_all16_sheet':True},'native_mips_gpu_passed':True,'independent_counts':reports[0]['counts'],'new103_alpha_and_fist_head_body_legs_exact':True,'effect_contact_native_initializer_verified':True,'charged_effect_phase_simulation':False,'supersedes_rejected_first_candidate':'prepared_rising_fire_base01/proposal.json','emulator_gameplay_test':False,'user_accepted':False,'full_style_unification_complete':False})
    print(json.dumps({'path':str(dest),'sha256':sha(dest.read_bytes())}))
if __name__=='__main__':main()
