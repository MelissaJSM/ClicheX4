"""실제 열람8판·중간 실패 원인 정정·최종 검사 결속. 원화/ARC 변경 없음."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'prepared_nova_strike_ultimate01';need(not(d/'author_visual_review.json').exists(),'기존 검토 보호');pack=H/'nova_strike_ultimate_pack03';seq=H/'nova_strike_ultimate_sequence01'
    files=[pack/n for n in('actual_readback_00.png','actual_readback_01.png','ownership_218.png','ownership_220.png')]+[seq/f'{form}_{part}_order.png'for form in('after','before')for part in('preparation','strike')]
    write(d/'author_visual_review.json',{'candidate_sha256':sha((d/'PL02_U.ARC').read_bytes()),'actually_viewed':True,'actual_images':8,'images':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for p in files],'findings':['새217 머리갈래/금색 안경·맨팔·허리와 굽힌 다리의 연결이 최종 재추출에도 유지된다. 기존 재킷 넓은 흰면은 새 after 의상으로 바뀌었다.','218의 실제3점은 원래 위치에 남으며 새몸과 추가 겹침이 없다.219는 같은 새몸을 따른 밝은 실루엣이다.','220의 몸체/효과/최종 판에서 새머리와 팔이 옛몸 가림으로 잘리는 추가 확정 문제를 찾지 못했다.','원표106 준비와 돌진9단계 판에서217 이후 양쪽은 원renderer 강제15로 같은 after 의상이다. 앞선 준비4의 전후 의상은 각 소유를 유지한다.'],'limitations':['정적8판을 실제 열람한 의견이며 연속 실기·60Hz 관측이 아니다.','218의3점은 현재 보존 정책,219 실루엣 및220의93셀 가림은 새몸 제작정책으로 과거효과전체raw exact라고 주장하지 않는다.','기존217 대비 앞쪽 발끝 외곽1px 안쪽이지만 원점·홍채·귀와 위아래 높이가 같고 외부 접점 강제연장은 하지 않았다.'],'new_confirmed_defect':False})
    failed=H/'nova_strike_ultimate_effects01/failed_probe.json';need(failed.exists(),'실패기록 없음')
    write(d/'historical_probe_correction.json',{'previous_failure_record':{'path':failed.relative_to(ROOT).as_posix(),'sha256':sha(failed.read_bytes())},'previous_reason_label_inaccurate':True,'corrected_cause':'첫 효과 재현은 새몸이 기존3점을 덮은 실패가 아니다. 옛몸의 발끝(12,13)이 가리던 역사색인1 한점을 새발끝이1px안으로 들어가며 다시 노출하여4점이 되는 차이를 검출한 것이다.','final_policy':'현재 실제 보이는218 효과3점을 전체 그대로 유지하고 가려졌던 역사점은 새로 노출하지 않는다.220은 별도로 역사 효과를 새몸에 맞춰 가림을 다시 계산한다.','original_failed_record_preserved':True,'current_three_points':[{'xy':[7,-28],'index':1},{'xy':[12,-14],'index':1},{'xy':[7,27],'index':1}],'candidate_unchanged':True})
    paths=[H/'nova_strike_ultimate_components_native_checks.json',seq/'report.json',seq/'browser_verification.json',seq/'REVIEW.html',H/'review_nova_strike_ultimate.py',H/'check_nova_strike_ultimate_browser.py',d/'author_visual_review.json',d/'historical_probe_correction.json',Path(__file__)]
    write(d/'post_lock_evidence.json',{'candidate_sha256':sha((d/'PL02_U.ARC').read_bytes()),'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in paths},'actual_engine_mask_after217':15,'old_failed_effects01_and_pack01_02_not_candidates':True,'fixed_staging_window_220_world_translation':[0,0],'tile16_220_nonzero_pixels_use_safe_U_padding':True,'runtime_verified':False})
    print(json.dumps({'visual':sha((d/'author_visual_review.json').read_bytes()),'evidence':sha((d/'post_lock_evidence.json').read_bytes())}))
if __name__=='__main__':main()
