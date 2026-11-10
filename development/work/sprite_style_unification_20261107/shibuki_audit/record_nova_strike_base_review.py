"""실제로 열람한 재추출/부분/원순서8판과 네이티브·브라우저 결과를 별도 결속."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'prepared_nova_strike_base01';need(not(d/'author_visual_review.json').exists(),'새 실제열람기록');paths=[]
    for name in('base_readback.png','fourth_readback.png','partial_217.png','partial_220.png'):paths.append(H/'nova_strike_base_pack01'/name)
    for form in('base','fourth'):
        for suffix in('preparation_order','strike_order'):paths.append(H/'nova_strike_base_sequence01'/f'{form}_{suffix}.png')
    write(d/'author_visual_review.json',{'actually_viewed':True,'images':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for p in paths],'actual_images':8,'candidate_sha256':sha((d/'PL00_U.ARC').read_bytes()),'findings':['새217의 머릿결·접힌 팔·옷과 부츠의 경계가 재추출에서도 유지된다.','포스217 부츠는 검보라/금색이며 원화의 잘못된 흰/붉은 큰 면이 남지 않았다.','220 원효과 뒤/앞 순서에서 새몸이 이어지고16부분조합에도 새 확정 손목/허리/발목 단절을 찾지 못했다.','218/219는 원효과를 그대로 두며 새몸이 나타나는217/220과 별도이다.','Ultimate 새단독217 첫비교는 이 기본후보8판 검사와 별도이며 포함하지 않았다.'],'limits':['실제 연속게임·물리이동·입력조건·속도·외부충돌 검증은 아니다.','원31+7 렌더러 packet와전체directory는 독립 후속 검사가 필요하다.','이 원화시각검토는 루트최종수용/사용자수용이 아니다.']})
    extra=[H/'nova_strike_base_components.json',H/'nova_strike_base_components_native_checks.json',H/'nova_strike_base_sequence01/report.json',H/'nova_strike_base_sequence01/browser_verification.json',H/'nova_strike_base_sequence01/REVIEW.html',H/'review_nova_strike_base.py',H/'check_nova_strike_base_browser.py',Path(__file__),d/'author_visual_review.json']
    write(d/'post_lock_evidence.json',{'candidate_sha256':sha((d/'PL00_U.ARC').read_bytes()),'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in extra},'ARC_unchanged':True,'new_MIPS_changed_refs':8,'original_table_steps':13,'new_art_table_steps':5,'browser_calls':100,'browser_canvas_checks':200,'source_sequence_console_note':'첫 실행 콘솔의 고정 new_steps4는 이전템플릿 출력이었다. 실제report의5와13개원표는처음부터정확하며콘솔계산식만교정했다.','native_renderer_candidate_pending':True,'runtime_verified':False});print(sha((d/'author_visual_review.json').read_bytes()))
if __name__=='__main__':main()
