"""독립 감사와 원래 MIPS 검사가 끝난 공중 누적 후보의 근거를 고정한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write

def main():
    d=H/'prepared_air01';need(not(d/'FROZEN.json').exists(),'Freeze already exists')
    expected='c580b371564252fd73cb97aa31d3282dcebabf5855cbec6d5b00acc7f7b7c6be';need(sha((d/'PL00_U.ARC').read_bytes())==expected,'Candidate changed')
    independent=H.parent/'zero_audit/shibuki_air22_independent.json';native=H.parent/'br_pending_v8f_components_native_checks.json'
    ind=json.loads(independent.read_text('utf8'));nat=json.loads(native.read_text('utf8'));need(ind['passed']and ind['candidate_sha256']==expected,'Independent check differs');need(nat['passed']and nat['resources']['PL00_U.ARC']['candidate_sha256']==expected,'Native check differs')
    own=json.loads((H/'air_pack_probe01/candidate_verification.json').read_text('utf8'));repro=json.loads((d/'repro_and_rejections.json').read_text('utf8'));need(own['passed']and repro['passed'],'Producer checks failed')
    readback=H/'air_pack_probe01/readback';visual=[*(readback/f'{form}_actual_{i:02}.png'for form in('base','fourth')for i in range(3)),*(readback/f'partial_all_{i:02}.png'for i in range(6)),*(d/f'sequences/id{i:03}_contact.png'for i in(10,11,12,122,123,124))]
    evidence={p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in(independent,native)}
    result={'passed':True,'scope':'기본/포스 공중 33~54 새 원화·공유 사격팔. 기존 누적 그림은 보존.','candidate_sha256':expected,'parent_sha256':own['parent_sha256'],'target_refs':list(range(33,55)),'target_layers_exact':110,'all_layers_checked':1140,'non_target_layers_exact':1030,'raw_references':508,'non_target_raw_exact':486,'non_target_compositions_exact':1677,'partial_rgba_conditions':704,'original_barrel_conditions':352,'gpu_static_parts':313,'all_composition_and_graphics_bank_boundaries_preserved':True,'whole_arc_outside_entry2_entry3_bytes_exact':573748,'reproduction_and_7_rejections':True,'source_art_shadows_below_alpha128_not_native_pixels':True,'shot44_original_cuff_over_barrel_pixels_replaced_with_accepted34_casing':21,'all_directly_viewed_contact_sheets':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in visual},'reviewers':{'producer':'기본3/포스3/부분6/순서6 비교를 실제 열람','root':'기본3/포스3 재추출 실제 열람, 추가 결함 없음이라는 메시지','independent':'기본3/포스3/부분6 및33확대 총13장 실제 열람'},'evidence':evidence,'native_mips_gpu_passed':True,'emulator_gameplay_test':False,'user_accepted_this_new_art':False,'full_style_unification_complete':False,'remaining_current_work':'98/99 네 의상: 기본/포스 원화 등록 중, Ultimate 길어진 다리는 수정 전 보류.'}
    write(d/'verification.json',result)
    frozen={'frozen':True,'files':{name:sha((d/name).read_bytes())for name in('PL00_U.ARC','proposal.json','verification.json','repro_and_rejections.json','sequences.json')},'baseline_bin_sha256':'21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a','parent_arc_sha256':own['parent_sha256'],'target_art_lock_sha256':'50117af7e0a8b0c64b387d2dd0b4424bb3a2eac8b66f1581ad411f0c6eb61af6','root_native_and_independent_evidence':evidence,'selected_visual_refs':list(range(33,55)),'cumulative_previous_proposal':'prepared_arrival_victory01/proposal.json','source_art_method':'builtin imagegen 4몸체 페이지,4사격 페이지 및 추가팔 국소교정1회. 고정배율/원CLUT/접점 등록. 옛 머리·몸 덮기 또는 전신 리사이즈 없음.','readback_visual_review_passed':True,'native_mips_gpu_passed':True,'emulator_gameplay_test':False,'user_accepted':False,'full_style_unification_complete':False}
    write(d/'FROZEN.json',frozen);print(json.dumps({'frozen_sha256':sha((d/'FROZEN.json').read_bytes()),'resource_sha256':expected,'verification_sha256':sha((d/'verification.json').read_bytes())}))
if __name__=='__main__':main()
