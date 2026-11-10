"""Ultimate 체이서 실제 재추출/부분/원순서22판 열람 기록."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    d=H/'prepared_chaser_ultimate01';need(not(d/'author_visual_review.json').exists(),'새 검토기록')
    plates=[H/f'chaser_ultimate_pack01/{f}_readback_{i:02}.png'for f in('before','after')for i in range(4)]+[H/f'chaser_ultimate_pack01/partial_{n:03}.png'for n in(162,166,170,174)]+[H/f'chaser_ultimate_sequence01/{f}_id{n}_ordered.png'for f in('before','after')for n in(66,68,70,72,75)]
    write(d/'author_visual_review.json',{'candidate_sha256':sha((d/'PL02_U.ARC').read_bytes()),'actually_viewed':list(map(ev,plates)),'actually_viewed_count':22,'findings':['머릿결·금색안경·재킷칼라/소매·맨팔과 샌들 구획이 재추출 뒤 유지된다.','새4키의 부분16표시에서 추가 확정 소매누출/손목·허리·발목절단을 찾지 못했다.','원표65..76 중 상하·174 진입/복귀대표5표의 정지순서판에서 갑작스러운 전신체격 도약을 찾지 못했다.'],'limits':['정적 순서판 열람이며 연속영상/실제게임을 새로 봤다고하지않는다.','174 귀정점/폭이 새기본보다각1px추가인 부분은 전신비율변형이아니며 원발높이27 유지.','162발+1,166전체−1,170발목·샌들−1 강체등록은 소스/겹침근거로만설명하며 차량실기접점exact가아니다.','금색안경 표본의 의미팔레트 등록과 현재Ultimate후폼9개를원US Y정책으로통일한 차이는 별도기록이다.','실제차량 손잡이·발판은미검증, root최종과독립검사는별도.']})
    evidence=[H/'chaser_ultimate_components.json',H/'chaser_ultimate_components_native_checks.json',H/'chaser_ultimate_sequence01/report.json',H/'chaser_ultimate_sequence01/browser_verification.json',H/'review_chaser_ultimate_sequence.py',H/'check_chaser_ultimate_browser.py',Path(__file__),d/'author_visual_review.json']
    write(d/'post_lock_evidence.json',{'evidence':list(map(ev,evidence)),'prepared_assets_modified':False,'runtime_verified':False});print(json.dumps({'author':sha((d/'author_visual_review.json').read_bytes()),'evidence':sha((d/'post_lock_evidence.json').read_bytes())}))
if __name__=='__main__':main()
