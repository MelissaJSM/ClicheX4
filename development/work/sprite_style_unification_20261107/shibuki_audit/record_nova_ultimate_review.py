"""실제 열람8판과 원코드·순서 검사를 준비본 후속 근거로 기록한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    d=H/'prepared_nova_ultimate01';need(not(d/'author_visual_review.json').exists(),'새 기록')
    files=[H/f'nova_ultimate_pack01/{f}_readback_{i:02}.png'for f in('before','after')for i in(0,1)]+[H/f'nova_ultimate_pack01/partial_{n}.png'for n in(213,215)]+[H/f'nova_ultimate_sequence01/{f}_preparation_order.png'for f in('before','after')]
    write(d/'author_visual_review.json',{'candidate_sha256':sha((d/'PL02_U.ARC').read_bytes()),'actually_viewed':[{**ev(p),'actually_viewed':True}for p in files],'plate_count':8,'observations':['새 머릿결·귀 내부층·금색 안경과 재킷 주름/맨팔이 실제 해당폼 대기와 이어진다.','첫 생성의 긴 신발은 새 종아리 donor만 등록해 교정하고 첫 새 샌들·발바닥 좌표는 그대로 보존했다.','32부분 표시에서 추가 확정 목/손목/발목 단절이나 소매 잔여를 찾지 못했다.','원표106 첫4만 새그림이며217의 옛 흰 재킷 몸체/218..220 효과는 그대로다. 전후 준비와217 이후 강제mask15 의상 정책은 후속 제작 대상이다.'],'runtime_verified':False,'user_accepted':False})
    paths=[H/'nova_ultimate_components.json',H/'nova_ultimate_components_native_checks.json',H/'nova_ultimate_sequence01/report.json',H/'nova_ultimate_sequence01/browser_verification.json',H/'nova_ultimate_sequence01/REVIEW.html',H/'review_nova_ultimate_preparation.py',H/'check_nova_ultimate_preparation_browser.py',Path(__file__)]
    write(d/'post_lock_evidence.json',{'candidate_sha256':sha((d/'PL02_U.ARC').read_bytes()),'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in paths},'native_changed_refs':4,'original_sequence_steps':13,'new_art_steps':4,'offline_canvas_form_checks':200,'final_art_root_and_independent_pending':True,'runtime_verified':False});print(json.dumps({'visual':sha((d/'author_visual_review.json').read_bytes()),'evidence':sha((d/'post_lock_evidence.json').read_bytes())}))
if __name__=='__main__':main()
