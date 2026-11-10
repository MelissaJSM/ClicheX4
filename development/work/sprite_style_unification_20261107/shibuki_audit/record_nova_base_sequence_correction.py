"""PL00의 표시마스크를 Ultimate 강제마스크와 혼동한 순서 미리보기 오류 정정."""
from pathlib import Path
import sys,json
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    p=H/'prepared_nova_base01/sequence_mask_correction.json';need(not p.exists(),'새 정정');a=Archive((H/'prepared_nova_base01/PL00_U.ARC').read_bytes());old=H/'nova_base_sequence01';new=H/'nova_base_sequence02';deltas={}
    for n in(217,218,219,220):deltas[str(n)]=int(np.any(np.array(a.composite(n,0)[0])!=np.array(a.composite(n,15)[0]),axis=2).sum())
    write(p,{'candidate_sha256':sha(a.data),'candidate_unchanged':True,'cause':'Ultimate217..230만 강제mask15인데 PL00 기본행에도 같은 규칙을 적용한 미리보기 작성 오류. 일반PL00는player+A7를 유지한다.','original_renderer_reading':ev(H.parent/'zero_audit/shibuki_nova_hover_relations01/report.json'),'superseded_for_mask_validation':[ev(old/'report.json'),ev(old/'browser_verification.json'),ev(old/'REVIEW.html')],'original_material_preserved':True,'scope_of_error':'sequence01 기본행217/220 RGBA 각528셀. 새213..216·포스행·후보ARC·원MIPS·정적/부분검사는 변화 없음. 당시canvas검사는 잘못된마스크기대값과의일치만 증명했다.','wrong_vs_correct_pixels':deltas,'corrected_report':ev(new/'report.json'),'corrected_browser':ev(new/'browser_verification.json'),'corrected_html':ev(new/'REVIEW.html'),'actually_viewed_corrected_plates':[ev(new/f'{f}_preparation_order.png')for f in('base','fourth')],'actually_viewed':True,'root_reviewer_addendum_pending':True,'ledger37_masks_already_correct':{'base':0,'fourth':15,'ultimate_217_plus':15},'runtime_verified':False});print(sha(p.read_bytes()))
if __name__=='__main__':main()
