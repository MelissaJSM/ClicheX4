"""루트의 원래 MIPS/GPU 검사·열람과 독립 감사가 모두 끝난 얼티밋만 동결한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'prepared_rising_fire_ultimate01';dest=d/'FROZEN.json';need(not dest.exists(),'Already frozen')
    initial=json.loads((d/'INPUT_FROZEN.json').read_text('utf8'))
    for name,digest in initial['files'].items():need(sha((d/name).read_bytes())==digest,'Frozen input changed')
    for name,digest in initial['producer_scripts'].items():need(sha((H/name).read_bytes())==digest,'Producer changed')
    evidence=['work/sprite_style_unification_20261107/zero_audit/rising_independent/ultimate.json','work/sprite_style_unification_20261107/br_pending_v10_ultimate_native_checks.json']
    reports=[json.loads((ROOT/p).read_text('utf8'))for p in evidence];need(all(r['passed']for r in reports),'Incomplete checks')
    expected='71d02fe6d965c1fb42cc786766bad62372c792ccd8ecf6d5bc1e40dc8deb8597'
    need(reports[0]['candidate_sha256']==expected,'Wrong independent candidate');need(reports[1]['resources']['PL02_U.ARC']['candidate_sha256']==expected,'Wrong native candidate')
    visual=sorted((H/'rising_ultimate_native01').glob('*_comparison.png'))+sorted((H/'rising_ultimate_native02').glob('*_comparison.png'))+sorted((H/'rising_ultimate_pack_probe01').glob('*_readback_*.png'))
    write(dest,{'frozen':True,'files':{p:sha((d/p).read_bytes())for p in('PL02_U.ARC','proposal.json','verification.json','INPUT_FROZEN.json')},'baseline_bin_sha256':'21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a','parent_arc_sha256':'dd6416c8840a1a0e5fd7ff4c73fe33b6ebd90e69b5f86f9be5f9671cc4d53c1d','target_art_lock_sha256':initial['source_lock_sha256'],'selected_visual_refs':[100,101,102,103,104,231,232],'root_native_and_independent_evidence':{p:sha((ROOT/p).read_bytes())for p in evidence},'root_actual_visual_review':{'source':'루트 메시지: Ultimate native 전후4시트와 packed 전후6시트 실제 열람 완료, 방향 수용.','files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for p in visual]},'native_mips_gpu_passed':True,'independent_counts':reports[0]['counts'],'effect_contact_native_initializer_verified':True,'charged_effect_phase_simulation':False,'emulator_gameplay_test':False,'user_accepted':False,'full_style_unification_complete':False})
    print(json.dumps({'path':str(dest),'sha256':sha(dest.read_bytes())}))
if __name__=='__main__':main()
