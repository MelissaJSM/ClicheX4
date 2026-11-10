"""사다리14 준비·독립/미술 범위와 다음 피격 조사를 새 장부에 기록."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    need(not(H/'fullform_ledger18.json').exists(),'Fresh ledger');d=H/'prepared_ultimate_ladder01';j=json.loads((H/'fullform_ledger17.json').read_text('utf8'));u=json.loads((H/'unique_art_keys17.json').read_text('utf8'));refs=[*range(143,156),183];candidate=ev(d/'PL02_U.ARC');ind=ROOT/'work/sprite_style_unification_20261107/zero_audit/shibuki_ultimate_ladder_independent01/report.json'
    j['pending_candidates']={'PL02_U.ARC':{**candidate,'proposal':ev(d/'proposal.json'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'independent':ev(ind),'selected_refs':refs,'frozen':False,'native_pending':True,'integrated':False,'gameplay_verified':False}}
    for r in j['references']:
        if r['form']in('ultimate_before','ultimate_after')and r['ref']in refs:r['candidate_progress']={'status':'新원화28표시·70층 패킹/재현3/거부8/독립448부분 통과, 원MIPS·동결 대기','evidence':ev(d/'verification.json'),'completed':False,'independent':ev(ind)}
    j['next_generation']={'group':'전폼 피격106..114/233..236','unique_body_keys':[106,110,233,234],'first_page':ev(H/'hurt_inputs01/page01/input.json'),'status':'실제 네폼 몸체4판 열람, 기본/포스106/110 입력2장 열람·원화생성대기. 효과 관계는 실제시부키 부모별 조사중.','read_only_relation_probe':ev(H/'hurt_relations01/report.json'),'generated':False,'packed':False}
    j['ladder14_prepared_scope']={'candidate':candidate,'targets':ev(H/'ultimate_ladder_complete_targets01/LOCK.json'),'independent':ev(ind),'author_packed_sheets':6,'root_packed_sheets':6,'reproduction_runs':3,'rejection_cases':8,'runtime_verified':False,'frame155_policy':'원US 전체몸체반동 복원 아님. 현재수용기본형의149 공통몸체와 서로다른150/155팔 및총구를사용.','foot_limits':'143/149/151/154 최하단은이전Ult보다1px,183은2px높음. 앞뒤새폼다리알파/등록색인대응같음. 실제사다리발판접점미확인.','sequence_review':ev(H/'ultimate_ladder_shot_sequence01/browser_verification.json'),'endpoint_review':ev(H/'ultimate_ladder_endpoint_review02/report.json')}
    j['new_root_review_evidence'] +=[ev(ROOT/f'work/sprite_style_unification_20261107/root_review_checkpoint{n}.json')for n in(89,91,94)if(ROOT/f'work/sprite_style_unification_20261107/root_review_checkpoint{n}.json').exists()]
    write(H/'fullform_ledger18.json',j);u.update(source_ledger=ev(H/'fullform_ledger18.json'),note='사다리14는 준비·독립 통과 후보이며 아직 frozen 집계에 추가하지 않음. BR15실기는기존범위그대로.');write(H/'unique_art_keys18.json',u)
    files=[H/f'ultimate_ladder_pack01/{f}_readback_{n:02}.png'for f in('before','after')for n in range(3)]+[H/f'ultimate_ladder_shot_sequence01/{f}_ordered_contacts.png'for f in('before','after')]+[H/'ultimate_ladder_shot_sequence01/browser_call_05.png']+[H/f'ultimate_ladder_endpoint_review02/feet_{n:02}.png'for n in range(2)]
    write(H/'ultimate_ladder_review_progress02.json',{'author_actually_viewed':[ev(p)for p in files],'observations':['새14자세 두의상6재추출판에서 머리/등/소매와맨팔 상세유지,추가확정분리못찾음.','원순서92/93 contact2판에서150→155→150 총열반동과손연결확인. 팔범위밖머리/몸체/다리는정확동일.','브라우저반동프레임 스크린샷1판 실제열람.128canvas/말단유지자동검사는연속영상을직접본것이나실기와구분.','발비교2판에서1~2px높이차이를별도표기. 픽셀/관절전체exact나실제발판접촉을주장하지않음.'],'rejected_diagnostic_assumption':'endpoint_review01의두CLUT RGB전체동일검사는잘못된가정으로중단. 새공통다리는원색표최근접대응과알파가exact이며팔레트자체는보존.','candidate_assets_changed_by_review':False,'continuous_video_actually_watched':False,'runtime_verified':False,'user_final_acceptance':False})
    print(json.dumps({'ledger':ev(H/'fullform_ledger18.json'),'review':ev(H/'ultimate_ladder_review_progress02.json')}))
if __name__=='__main__':main()
