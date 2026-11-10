"""보행32 새 ARC와 독립 디렉터리 원MIPS/정적/실제 미술 열람을 고정."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
EXPECTED='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce'

def main():
    d=H/'prepared_base_run01';need(not(d/'FROZEN.json').exists(),'Already frozen')
    lock=json.loads((d/'PREPARED_LOCK.json').read_text('utf8'))
    for n,digest in lock['files'].items():need(sha((d/n).read_bytes())==digest,'Changed prepared '+n)
    for n,digest in lock['source_scripts'].items():need(sha((H/n).read_bytes())==digest,'Changed producer '+n)
    need(sha((d/'PL00_U.ARC').read_bytes())==EXPECTED,'Changed ARC')
    proposal=json.loads((d/'proposal.json').read_text('utf8'))
    for n,digest in proposal['source_files'].items():need(sha((H/n).read_bytes())==digest,'Changed authored source '+n)
    prefix=ROOT/'work/sprite_style_unification_20261107'
    paths=[prefix/'zero_audit/shibuki_run32_independent01/report.json',prefix/'zero_audit/shibuki_run32_directory_native01/report.json',prefix/'root_review_checkpoint75.json',H/'base_run_readback_review01.json']
    ind,native,root,art=[json.loads(p.read_text('utf8'))for p in paths]
    need(sha(paths[0].read_bytes())=='bd446a6955df3ee80d859f82a286c859dafa6a06bbc0950f10e2b3f1ba37f3a6','Independent changed')
    need(sha(paths[1].read_bytes())=='11dd4c9bf5de510e9124d5b7e67e9ac42d04a256598100d4b018844152982331','Native changed')
    need(ind['passed']and native['passed']and ind['candidate_sha256']==native['candidate_sha256']==EXPECTED,'Wrong checks')
    need(root['packed_asset_sha256']==EXPECTED,'Wrong root candidate')
    for r in root['root_actually_viewed']:need(sha((ROOT/r['path']).read_bytes())==r['sha256'],'Changed viewed plate')
    need(len(root['root_actually_viewed'])==12,'Expected twelve root readback plates')
    initial=json.loads((d/'verification.json').read_text('utf8'))
    write(d/'final_verification.json',{'passed':True,'candidate_sha256':EXPECTED,'parent_sha256':proposal['sequential_parent']['sha256'],'refs':list(range(1,33)),'target_layers':160,'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in paths},'independent_counts':ind['counts'],'native_stats':native['stats'],'native_scope':native['scope'],'native_limits':native['limits'],'bank12_13_absolute_bytes_exact':ind['bank12_13_absolute_bytes_exact'],'ref1_is_existing_idle0_exact':ind['ref1_is_existing_idle0_exact'],'source_assets_checked':len(proposal['source_files']),'identical_builds':initial['total_identical_builds'],'rejected_inputs':initial['rejection_count'],'author_readback_plates':12,'root_readback_plates':12,'entry2_fixed_length':186228,'bank0_growth':672,'capsule_unconsumed_tail_trim':{'10':344,'11':328},'art_reduced':False,'no_EXE_ARC_entry_LBA_palette_audio_changes':True,'implementation_authorization':'전체 스프라이트 상세화/재삽입 승인 안에서 루트가 가역 시험 ARC 구현으로 판단. 사용자가 내부offset 변경을 직접 승인했다고 기록하지 않음.','replaces_pending_status_in_initial_reports':True,'fresh_boot_required_for_runtime':'상주 객체가 이전 bank 포인터를 캐시하므로 새 부팅/새 자원 로드에서 실기. 기존 F1 메모리로 성공을 주장하지 않음.','gameplay_verified':False,'user_accepted':False,'full_project_complete':False})
    write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':EXPECTED,'parent_arc_sha256':proposal['sequential_parent']['sha256'],'source_lock_sha256':proposal['target_lock_sha256'],'storage_lock_sha256':proposal['storage_lock_sha256'],'selected_visual_refs':list(range(1,33)),'native_and_independent_passed':True,'root_packed_art_reviewed':True,'supersedes_initial_pending_flags':True,'bank_directory_relocated_inside_fixed_entry':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False})
    print(json.dumps({'arc_sha256':EXPECTED,'frozen_sha256':sha((d/'FROZEN.json').read_bytes()),'final_verification_sha256':sha((d/'final_verification.json').read_bytes())}))
if __name__=='__main__':main()
