"""BR15 실기와 사다리 후보 진행을 분리한 새 장부. 동결 파일은 수정하지 않는다."""
from pathlib import Path
from collections import Counter
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    out=H/'fullform_ledger17.json';need(not out.exists(),'Fresh ledger')
    runtime=ROOT/'work/sprite_style_unification_20261107/runtime/shibuki_run15_summary.json';need(sha(runtime.read_bytes())=='6e2e38d6095a8837ca46fefb7f2c7a7bb9a583e195e64d8208819ea57f833edd','Runtime changed')
    j=json.loads((H/'fullform_ledger16.json').read_text('utf8'));u=json.loads((H/'unique_art_keys16.json').read_text('utf8'))
    j['current_candidates']['PL00_U.ARC'].update(new_run32_gameplay_verified=True,runtime_evidence=ev(runtime),integrated_build='sprite_style_unification_20261107_v15',integrated_bin_sha256='dfd1b9d09e8fad846aebfd51a89aecc46bff98bc6281619bb21abf1c8dbf27fc')
    j['run32_actual_scope']={'evidence':ev(runtime),'observer':'root 실제 새부팅·영상/연속판 열람 및 RAM/GPU 관측','basic_captures':288,'fourth_captures':287,'both_forms_new_refs':list(range(1,33)),'resident_entries_exact':[2,3,9],'fourth_charge_captures':192,'root_actually_viewed_plates':36,'unresolved_async_events':{'base':[29,16,74],'fourth':[9],'charge':[]},'unresolved_note':'각 참조는 다른 사건에서 성공 표본도 존재한다. 비동기 사건을 결함 또는 전표본 성공으로 치환하지 않음.','sessions_closed':True,'protected27_same':True,'user_final_acceptance':False}
    for r in j['references']:
        if r['form']in('base','fourth')and 1<=r['ref']<=32:r.update(runtime_evidence=ev(runtime),runtime_successful_sample=True,user_final_acceptance=False)
        if r['form']in('ultimate_before','ultimate_after')and r['ref']in(143,144,146,149,151,153,154,183):r['candidate_progress']={'status':'새 원화·공통부 등록 중, 패킹 전','evidence':ev(H/'ultimate_ladder_common_probe02/report.json'),'completed':False}
    j['next_generation']={'group':'Ultimate 사다리143..155/183','status':'8고유몸체×2의상 생성·고정64셀 등록,151 팔 국소 교정 및 새공통부 검토.4반전 파생과 사격150/155 남음.','source_reports':[ev(H/p)for p in('ultimate_ladder_native03/report.json','ultimate_ladder_native_page02/report.json','ultimate_ladder_native_page03/report.json','ultimate_ladder151_arm_composed01/report.json','ultimate_ladder_common_probe02/report.json')],'original_alias_evidence':ev(ROOT/'work/sprite_style_unification_20261107/zero_audit/ultimate_ladder_aliases01/report.json'),'packed':False,'runtime_verified':False,'source_contact_limit':'151은 원손 피부좌표와2px 중첩하나 새주먹 외곽exact나 실제사다리 접촉 검증은 아님. 발 최하단1..2px 차이는 별도검토.'}
    j['new_root_review_evidence']=[ev(ROOT/f'work/sprite_style_unification_20261107/root_review_checkpoint{n}.json')for n in(72,79,80,82,87)if(ROOT/f'work/sprite_style_unification_20261107/root_review_checkpoint{n}.json').exists()]
    write(out,j);u.update(source_ledger=ev(out),note='고유키는 기존 자료 동형 묶음. BR15 양폼1..32 성공 실기표본과 비동기미확정4건을 분리. 새사다리8몸체는 후보이며 완료수에 더하지 않음.');write(H/'unique_art_keys17.json',u)
    receipts=[('ultimate_ladder_inputs02/page02','exec-0a0c3e37-deb6-482b-bc23-cfcc416885ed.png'),('ultimate_ladder_inputs02/page03','exec-90e4b082-0434-4b28-9c23-71177f7e4320.png'),('ultimate_ladder151_arm_edit01','exec-c0c606c4-24ea-4ba1-a256-290d9382b825.png'),('ultimate_ladder151_arm_edit02','exec-30e08dd2-deb3-45da-a04b-c216e58f350e.png')]
    for name,filename in receipts:
        d=H/name;p=d/'generation_receipt.json';need(not p.exists(),'Receipt exists');inputs={x.name:sha(x.read_bytes())for x in d.glob('*.png')if x.name!='generated.png'};write(p,{'tool':'builtin imagegen','original_filename':filename,'generated':ev(d/'generated.png'),'prompt':ev(d/'prompt.txt'),'inputs':inputs,'original_preserved':True,'native_scale':0.125,'adoption_note':'새 원화 원본 보존.151 두 edit의149/153 및 비국소 변화는 채택하지 않음.'if'151'in name else'두 의상 전신 후보.접점/공통층/패킹은 별도 검증.'})
    viewed=[]
    for form in('before','after'):
        for n in range(3):viewed.append(ev(H/f'ultimate_ladder_common_probe01/{form}_comparison_{n:02}.png'))
    viewed +=[ev(H/'ultimate_ladder_common_probe02/after_comparison_01.png'),ev(H/'ultimate_ladder151_arm_composed01/comparison.png'),ev(H/'ultimate_ladder151_arm_native01/contact_grid.png')]
    write(H/'ultimate_ladder_review_progress01.json',{'actually_viewed':viewed,'observation':'새151 팔의 어깨-팔꿈치-손 연결은 이어진다. 공통probe01의149 머리영역에 들린소매 혼입을 발견하여probe02에서 그팔을공통머리제외. 새머릿결/옷 세부는 유지.','confirmed_rejected':['ultimate_ladder_native02 실패 중간출력','ultimate_ladder151_arm_edit01은2px높이잔여로최종팔donor아님','ultimate_ladder_common_probe01 after149 소매혼입'],'not_claimed':['원게임실기','새사다리ARC성공','정확한모든손발접점','사용자최종수용'],'remaining':['6개맨팔/옷외곽점의출처보존정합','발최하단차이검토','반전4파생','사격150/155새팔','32tile및전체참조회귀']})
    print(json.dumps({'ledger':ev(out),'counts':u['counts']},ensure_ascii=True))
if __name__=='__main__':main()
