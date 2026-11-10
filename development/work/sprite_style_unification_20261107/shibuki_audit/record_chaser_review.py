"""체이서 고정후보의 실제 열람22판과 후속 원순서 근거를 기록."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write

def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    d=H/'prepared_chaser_base01';need(not(d/'author_visual_review.json').exists(),'이미 기록됨')
    plates=[H/f'chaser_base_pack03/{form}_readback_{i:02}.png'for form in('base','fourth')for i in range(4)]
    plates += [H/f'chaser_base_pack03/partial_{n:03}.png'for n in(162,166,170,174)]
    plates += [H/f'chaser_base_sequence01/{form}_id{n}_ordered.png'for form in('base','fourth')for n in(66,68,70,72,75)]
    need(len(plates)==22,'실제 열람 수')
    write(d/'author_visual_review.json',{'candidate_sha256':sha((d/'PL00_U.ARC').read_bytes()),'actually_viewed':list(map(ev,plates)),'actually_viewed_count':22,'findings':['새 머릿결·귀면·금색 눈과 두 의상의 칼라/소매/부츠 구획이 재추출 뒤 유지된다.','4고유자세의 부분16표시에서 새 확정 소매 누출·추가 팔·손목/허리 절단을 찾지 못했다.','원표의 상하이동 및174 진입/복귀 순서판에서 갑작스러운 전신 크기 도약을 찾지 못했다.'],'limits':['정지 순서판 열람이며 연속 영상을 실제 보았다는 뜻은 아니다.','새 피부손 ROI 일부1px 차이와174 귀/머리폭 증가를 전신스케일 변경이나 물리접점 exact로 설명하지 않는다.','실제 차량 손잡이·발판 및 게임실기는 미검증.','원화 최종 root수용/독립reader는 별도 근거다.']})
    paths=[H/'chaser_base_sequence01/report.json',H/'chaser_base_sequence01/browser_verification.json',H/'review_chaser_sequence.py',H/'check_chaser_browser.py',H.parent/'zero_audit/shibuki_chaser_sequences01/report.json',H.parent/'zero_audit/shibuki_chaser13_directory_native01/report.json',d/'author_visual_review.json']
    write(d/'post_lock_evidence.json',{'evidence':list(map(ev,paths)),'prepared_assets_modified':False,'source_scope':'잠금 이후 새 정적 순서/브라우저·독립 원MIPS 근거만 추가. 자산/고정입력은 불변.','runtime_verified':False})
    print(json.dumps({'review':sha((d/'author_visual_review.json').read_bytes()),'evidence':sha((d/'post_lock_evidence.json').read_bytes())}))
if __name__=='__main__':main()
