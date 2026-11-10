"""대시20 준비자원, 입력거부, 재현 및 실제 열람 범위를 고정한다."""
from pathlib import Path
import json,sys,shutil
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_dash_complete import validate_inputs,protected_entries,PARENT,LOCK
from prepare_dash_body_layers import P
from scripts.discover_inputs import psx_arc

OUTSHA='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b'
def identity(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def reject_tests():
    source=P.read_bytes();read=lambda p:(H/p).read_bytes();validate_inputs(source,read);tests=[]
    def mutated(v):return bytes([v[0]^1])+v[1:]
    lock=json.loads(read('dash_complete_targets01/LOCK.json'))
    names=['dash_complete_targets01/LOCK.json','dash_complete_targets01/targets.json','dash_complete_targets01/'+next(iter(lock['files'])),next(iter(lock['source_reports']))]
    for name in [None]+names:
        try:
            validate_inputs(mutated(source) if name is None else source,lambda p:mutated(read(p))if p==name else read(p))
        except ValueError as ex:tests.append({'corrupt_input':name or 'parent ARC','rejected':True,'reason':str(ex)})
        else:raise ValueError('Corruption was accepted')
    data=(H/'dash_pack_probe02/PL00_U.ARC').read_bytes();entries=psx_arc(data)
    for e in [next(e for e in entries if e['index']==12),{'index':'archive header','offset':32}]:
        wrong=bytearray(data);wrong[e['offset']]^=1
        try:protected_entries(source,bytes(wrong))
        except (ValueError,KeyError,IndexError)as ex:tests.append({'corrupt_input':e['index'],'rejected':True,'reason':str(ex)})
        else:raise ValueError('Unrelated mutation accepted')
    return tests

def main():
    o=H/'prepared_dash_base01';need(not o.exists(),'Fresh prepared output');d=H/'dash_pack_reproduction02';data=(d/'PL00_U.ARC').read_bytes();need(sha(data)==OUTSHA,'Candidate changed')
    for folder in ('dash_pack_probe02','dash_pack_reproduction01'):need((H/folder/'PL00_U.ARC').read_bytes()==data,'Reproduction mismatch')
    verification=json.loads((d/'verification.json').read_text('utf8'));need(verification['passed'],'Verification failed');tests=reject_tests()
    receipt=H/'dash82_arm_retry01';prompt=(receipt/'prompt.txt').read_text('utf8').strip();(receipt/'prompt_used.txt').write_text(prompt,encoding='utf8')
    need(sha((receipt/'generated.png').read_bytes())=='cd2ad4fec7baba7479ff40d76999d788c53f6a29c76b0cd45923f677965564a4','Retry source changed')
    write(receipt/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':'exec-0d1799be-a29b-48c8-ba1d-361aacb561e1.png','source_sha256':sha((receipt/'generated.png').read_bytes()),'prompt_sha256':sha(prompt.encode()),'scope':'82의 짧고 접힌 발사팔 국소 교정. 84는 첫 페이지 원화를 유지.','input_files':[identity(receipt/n)for n in('edit_target.png','anchor_guide.png')if(receipt/n).exists()]})
    o.mkdir();(o/'PL00_U.ARC').write_bytes(data)
    for name in ('report.json','verification.json'):shutil.copyfile(d/name,o/name)
    for p in sorted(d.glob('*_readback_*.png')):shutil.copyfile(p,o/p.name)
    for p in sorted((d/'verification').glob('partial_all_*.png')):shutil.copyfile(p,o/p.name)
    viewed=[p for p in sorted((H/'dash_pack_probe02').glob('*_readback_*.png'))]+list(sorted((H/'dash_pack_probe02/verification').glob('partial_all_*.png')))
    write(o/'visual_review.json',{'author_actually_viewed':[identity(p)for p in viewed],'observations':['기본/포스 8재독출판과 16부분 조합 5판을 실제 열람했다. 소매에서 손목, 목과 어깨, 무릎과 발목에 새 단절 또는 추가 손을 발견하지 못했다.','82는 첫 생성의 총구6px 이동을 거부하고 짧게 접힌 팔을 새로 받아 원총구에 등록했다.','79→81→83은 웅크린 회복에서 서는 순서이며 새로운 몸체 키 변화는 접지 기준을 유지한다. 실제 게임 물리/이벤트 연결은 아직 검증하지 않았다.','기본과 포스의 머리 공통층은 새 원화의 머릿결과 얼굴이며 구형 머리로 덮지 않았다.','원래 총열의 프레임별 모양까지 동일하다는 뜻은 아니다. 수용된34의60불투명+11투명칸을 각 원총구에 복제했다.'],'root_review_messages':['dash_recovery_height_native01 기본/포스 높이·질감 방향 수용','dash_shot_native02 68/70 기본/포스 실제 열람 수용','dash82_arm_native04 기본/포스 짧은 팔·총구 연결 수용'],'root_final_packed_review_pending':True,'sequence_live_viewed':False,'emulator_verified':False,'user_accepted':False})
    write(o/'input_rejection.json',{'passed':True,'cases':tests,'filesystem_inputs_modified':False,'actual_output_written_during_bad_cases':False})
    parent=json.loads((H/'prepared_rising_right_base01/proposal.json').read_text('utf8'))
    parent['files']['PL00_U.ARC']['path']=(o/'PL00_U.ARC').relative_to(ROOT).as_posix();parent['files']['PL00_U.ARC']['after']=OUTSHA
    parent.update({'replaces':(H/'prepared_rising_right_base01/proposal.json').relative_to(ROOT).as_posix(),'supersedes':'prepared_rising_right_base01','selected_visual_refs':list(range(67,85))+[93,94],'source_art_manifest':(H/'dash_complete_targets01/LOCK.json').relative_to(ROOT).as_posix(),'source_art_manifest_sha256':LOCK,'parent_arc_sha256':PARENT,'sequential_parent':identity(P),'scope':'기본/포스 대시 몸체10, 사격8, 원속도선 합성2의 총20참조를 대기 기준 세밀도로 통일. 원래 은행/엔트리 경계·타이밍·음향·팔레트·총구·속도선 기록과 타일을 보존.','static_review_passed':True,'native_cpu_pending':True,'independent_review_pending':True,'actual_gameplay_pending':True})
    parent.pop('runtime_bug_evidence',None);write(o/'proposal.json',parent)
    scripts=['prepare_dash_detail_inputs.py','register_dash_detail_page01.py','prepare_dash_recovery_height.py','register_dash_recovery_height.py','align_dash_initial_contacts.py','align_dash_all_contacts.py','probe_dash_common_head.py','prepare_dash_body_layers.py','prepare_dash_shot_inputs.py','prepare_dash82_arm_retry.py','register_dash_shot_page.py','prepare_dash_complete_targets.py','pack_dash_complete.py','verify_dash_candidate.py','finalize_dash_candidate.py','audit_dash_barrels.py','audit_dash_speed_streaks.py','pack_air_targets_probe.py','probe_air_body_capacity.py']
    folders=['dash_detail_inputs01','dash_detail_inputs02','dash_detail_inputs04','dash_recovery_height01','dash_detail_contacts02','dash_common_head_probe01','dash_body_layers01','dash_shot_inputs02','dash82_arm_retry01','dash_shot_page01_final01','dash_shot_page02_final01','dash_shot_page03_final01','dash82_arm_native04','dash_shot_page04_final01','dash_barrel_guard02','dash_speed_streak_audit02','dash_complete_targets01']
    sources={}
    for folder in folders:
        for p in sorted((H/folder).rglob('*')):
            if p.is_file()and p.suffix.lower()in('.png','.json','.txt'):sources[p.relative_to(H).as_posix()]=sha(p.read_bytes())
    write(o/'INPUT_FROZEN.json',{'input_frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(o.iterdir())if p.is_file()},'producer_scripts':{p:sha((H/p).read_bytes())for p in scripts},'source_files':sources,'source_lock_sha256':LOCK,'parent_arc_sha256':PARENT,'reproduction_runs':3,'reproduced_sha256':OUTSHA,'source_files_count':len(sources),'input_rejection_cases':len(tests),'root_native_pending':True,'independent_pending':True,'root_packed_visual_pending':True,'user_accepted':False,'emulator_tested':False,'full_project_complete':False})
    print(json.dumps({'path':str(o),'sha256':OUTSHA,'input_files':len(sources),'rejection_cases':len(tests),'proposal_sha256':sha((o/'proposal.json').read_bytes())}))
if __name__=='__main__':main()
