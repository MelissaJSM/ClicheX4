"""실제 열람한 최종8판과 새 원코드·순서 검사를 준비본 후속 근거로 저장."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    d=H/'prepared_nova_base01';need(not(d/'author_visual_review.json').exists(),'새 기록')
    files=[H/f'nova_base_pack02/{f}_readback_{i:02}.png'for f in('base','fourth')for i in(0,1)]+[H/f'nova_base_pack02/partial_{n}.png'for n in(213,215)]+[H/f'nova_base_sequence01/{f}_preparation_order.png'for f in('base','fourth')]
    write(d/'author_visual_review.json',{'candidate_sha256':sha((d/'PL00_U.ARC').read_bytes()),'actually_viewed':[{**ev(p),'actually_viewed':True}for p in files],'plate_count':8,'observations':['큰 단색 머리와 소매가 새 머릿결·귀 내부층·주름으로 세분화되어 대기와 이어진다.','포스 들린팔의 큰 흰 소매는 새 국소 원화의 검보라 주름으로 교정됐고 작은 붉은 허리 술은 구별된다.','부분16조합×2자세에서 새 확정 손목/목/발목 단절을 찾지 못했다.','원표106의 첫4는 새그림이며 이후217은 옛 몸체를 유지한다. 전체 노바를 완료로 세지 않는다.'],'runtime_verified':False,'user_accepted':False})
    paths=[H/'nova_base_components.json',H/'nova_base_components_native_checks.json',H/'nova_base_sequence01/report.json',H/'nova_base_sequence01/browser_verification.json',H/'nova_base_sequence01/REVIEW.html',H/'review_nova_preparation.py',H/'check_nova_preparation_browser.py',Path(__file__)]
    write(d/'post_lock_evidence.json',{'candidate_sha256':sha((d/'PL00_U.ARC').read_bytes()),'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in paths},'native_changed_refs':14,'original_sequence_steps':13,'new_art_steps':4,'offline_canvas_form_checks':200,'final_art_root_and_independent_pending':True,'runtime_verified':False});print(json.dumps({'visual':sha((d/'author_visual_review.json').read_bytes()),'evidence':sha((d/'post_lock_evidence.json').read_bytes())}))
if __name__=='__main__':main()
