"""루트 실제 열람/원MIPS 및 별도 감사의 완료 근거를 해시로 묶는다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
    native=H.parent/'br_pending_v11_rising_right_native_checks.json';need(json.loads(native.read_text('utf8'))['passed'],'Native failed')
    configs=[('base','PL00_U.ARC','prepared_rising_right_base01','rising_right_base_pack02','27f201d48c879621dacb81ffa18f91cb0bcb3a60e7da6131f9795e14f9e2d384'),('ultimate','PL02_U.ARC','prepared_rising_right_ultimate01','rising_right_ultimate_pack01','243f900892dff06cd948a83009eca8fa86aafd606c66c5c8eec1dcf1b88e61a6')]
    results=[]
    for form,name,folder,artifact,ind_sha in configs:
        out=H/folder;target=out/'FROZEN.json';inp=json.loads((out/'INPUT_FROZEN.json').read_text('utf8'));prop=json.loads((out/'proposal.json').read_text('utf8'))
        if target.exists():
            done=json.loads(target.read_text('utf8'))
            for f,h in done['files'].items():need(sha((out/f).read_bytes())==h,'Frozen files changed')
            results.append({'path':rel(target),'sha256':sha(target.read_bytes()),'existing_preserved':True});continue
        for f,h in inp['files'].items():need(sha((out/f).read_bytes())==h,'Prepared input changed')
        ind=H.parent/f'zero_audit/rising_right_independent/{form}.json';need(sha(ind.read_bytes())==ind_sha,'Independent report changed');ir=json.loads(ind.read_text('utf8'));need(ir['passed'],'Independent failed')
        candidate=sha((out/name).read_bytes());need(native.exists(),'Native missing');need(json.loads(native.read_text('utf8'))['resources'][name]['candidate_sha256']==candidate,'Native source differs')
        views=list(sorted((H/artifact).glob('*_readback_*.png')))+[H/'rising_right_packed_contact01/four_forms_native_effect_overlay.png']
        doc={'frozen':True,'files':{f:sha((out/f).read_bytes())for f in(name,'proposal.json','verification.json','INPUT_FROZEN.json')},'baseline_bin_sha256':prop['baseline_sha256'],'parent_arc_sha256':prop['parent_arc_sha256'],'target_art_lock_sha256':prop['source_art_manifest_sha256'],'selected_visual_refs':[103,104],'root_native_and_independent_evidence':{rel(ind):ind_sha,rel(native):sha(native.read_bytes())},'root_actual_local_visual_review':{'images':{rel(p):sha(p.read_bytes())for p in views},'source':'루트 메시지: 최종 네 의상 readback4판과 원효과 합성판 실제 열람, 방향/의상/연결 수용. 원MIPS/GPU 통과 후 동결 지시.'},'native_mips_gpu_passed':True,'independent_passed':True,'effect_contact_native_initializer_verified':True,'contact_report':{'path':rel(H/'rising_right_packed_contact01/report.json'),'sha256':sha((H/'rising_right_packed_contact01/report.json').read_bytes())},'repaired_defect':'103 준비→104 상승에서 반대쪽 손을 올렸던 기존 결함. 원US 공중 발원점쪽 손으로 교정.','source_alpha_handling':'기본/포스104 alpha224의 실제큰몸체 보존, 떨어진 배경성분19/13픽셀만 제외. 240손실중간본은사용하지않음.','emulator_gameplay_test':False,'user_accepted':False,'full_style_unification_complete':False}
        write(target,doc);results.append({'path':rel(target),'sha256':sha(target.read_bytes())})
    print(json.dumps(results))
if __name__=='__main__':main()
