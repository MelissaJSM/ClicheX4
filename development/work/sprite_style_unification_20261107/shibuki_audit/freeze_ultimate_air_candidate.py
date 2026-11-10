"""새 Ultimate 공중22의 입력잠금은 유지하고 최종검수 결과만 추가한다."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def evidence(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    d=H/'prepared_ultimate_air01';need(not(d/'FROZEN.json').exists(),'Already frozen')
    arc_sha='3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7';parent_sha='d636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d'
    lock=json.loads((d/'INPUT_FROZEN.json').read_text('utf8'))
    for name,digest in lock['files'].items():need(sha((d/name).read_bytes())==digest,'Input-frozen file changed')
    for name,digest in lock['source_files'].items():need(sha((H/name).read_bytes())==digest,'Source art changed')
    need(sha((d/'PL02_U.ARC').read_bytes())==arc_sha,'Wrong candidate')
    ind_path=H.parent/'zero_audit/shibuki_ultimate_air_independent.json';nat_path=H.parent/'br_pending_v12_air22_native_checks.json';own_path=H/'ultimate_air_final_visual_review01.json'
    need(sha(ind_path.read_bytes())=='7eef88f19b48524eeecbf32a1259443f931c1ce5a1fedf6a6458e3bd2c7ccab0','Independent report changed')
    ind=json.loads(ind_path.read_text('utf8'));nat=json.loads(nat_path.read_text('utf8'));own=json.loads((d/'verification.json').read_text('utf8'))
    need(ind['passed']and ind['candidate_sha256']==arc_sha and ind['source_sha256']==parent_sha,'Independent failure')
    need(nat['passed']and nat['resources']['PL02_U.ARC']['candidate_sha256']==arc_sha,'Native report does not match')
    need(own['passed']and own['reproducible_same_sha256']==arc_sha and len(own['rejected_bad_inputs'])==4,'Producer/repro checks failed')
    visual={p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in(d/name for name in own['actual_readback_sheets'])}
    for row in ind['actually_viewed_readback_sheets']:need(sha((ROOT/row['path']).read_bytes())==row['sha256'],'Viewed image changed')
    result={'passed':True,'scope':'시부키 Ultimate 공중/사격33..54 전후44표시. 이전누적그림·음향·팔레트·시간표보존.','candidate_sha256':arc_sha,'parent_arc_sha256':parent_sha,'counts':ind['counts'],'evidence':[evidence(p)for p in(ind_path,nat_path,own_path,d/'verification.json')],'actually_viewed_readbacks':visual,'root_review':'루트가최종before/after_readback00..03 총8판을직접열람하고세부·크기·51굽힌팔·42/44사격정리를수용하여다음통합승인한다는메시지를전달했다. 전체작업완료/사용자최종수용은아니다.','casing_policy':'이전각참조의서로다른총열보존이아니라수용after34총열60비투명+11투명보호칸을각원총구로평행이동하여22경우RGBA완전일치.','native_mips_gpu_passed':True,'independent_readback_passed':True,'readback_visual_review_passed':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False,'old_input_status_fields':'proposal/verification의pending필드는입력동결당시기록으로보존했다. 최종검수상태는이파일과FROZEN을따른다.'}
    write(d/'final_verification.json',result)
    write(d/'FROZEN.json',{'frozen':True,'candidate_sha256':arc_sha,'files':{name:sha((d/name).read_bytes())for name in('PL02_U.ARC','proposal.json','verification.json','INPUT_FROZEN.json','final_verification.json')},'parent_arc_sha256':parent_sha,'target_art_lock_sha256':lock['target_lock_sha256'],'selected_visual_refs':list(range(33,55)),'source_art_files':lock['source_files'],'root_native_and_independent_evidence':[evidence(p)for p in(ind_path,nat_path,own_path)],'readback_visual_review_passed':True,'native_mips_gpu_passed':True,'emulator_gameplay_test':False,'user_accepted':False,'full_style_unification_complete':False,'remaining_work':'기본/포스대시10몸체新원화정합중.81/83높이국소수정·사격·Ultimate의상및다른전폼잔여계속.'})
    print(json.dumps({'FROZEN_sha256':sha((d/'FROZEN.json').read_bytes()),'candidate_sha256':arc_sha,'final_verification_sha256':sha((d/'final_verification.json').read_bytes())}))
if __name__=='__main__':main()
