"""새 등장 원화 두 번째 페이지의 실제 미술 검토를 후보와 분리 기록한다."""
from pathlib import Path
import sys, json
H=Path(__file__).resolve().parent; ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write

def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    d=H/'ultimate_arrival_native02';p=H/'ultimate_arrival_inputs01/page02/generated.png'
    need(sha(p.read_bytes())=='b6f77ba7481b70b8bc8f97a06f3a38edb9f0ec8529172193e388436d1672566c','New art changed')
    out=d/'author_visual_review.json';need(not out.exists(),'Fresh review')
    write(out,{'generated':ev(p),'registration':ev(d/'report.json'),
      'actually_viewed':[ev(d/f'{f}_comparison.png') for f in ('before','after')],
      'method':'실제 view_image로 원점/대기와 나란히 놓인 두 비교판을 열람했다. 수치검사를 미술 합격으로 대체하지 않았다.',
      'observations':[
        {'refs':[137],'forms':['before','after'],'decision':'머릿결/금색 장식/옷 명암 개선 방향. 공통 머리·손발/의상 경계는 아직 미검증. 원번개는 등록판 새몸에 아직 합성하지 않았다.'},
        {'refs':[138],'forms':['before'],'decision':'머리 위 맞댄 손·짧은 체형·재킷 상세가 유지되는 방향. 실제 관절 접점 및 공통층 등록 전이다.'},
        {'refs':[138],'forms':['after'],'decision':'반려. 올린 팔에 넓은 흰/연한 파랑 재킷 소매가 남아 수용 수영복형의 맨팔과 다르다. 생성 원화부터 존재하며 숫자상 몸체/바닥 보존으로 통과시킬 수 없다. 같은 오류가 이전 부모138에도 있어 단순 신규 회귀라고 단정하지 않는다.'}],
      'peer_readonly_observation':{'agent':'hud_checkpoint','sheet':ev(d/'after_comparison.png'),'scope':'정적 한 판 열람 의견. 138의 흰 세로 팔을 재킷 소매로 읽었으며137 피부색 팔과 대조해 반려에 동의했다. 원화 재구성/패킹/실기 검사를 뜻하지 않는다.'},
      'unchanged_sole_world_y':23,'wholebody_rescale':False,'old_master_overlay':False,
      'not_done':['공통 머리/사지 정합','138 후폼 소매 새 원화 수정','효과 합성','ARC 패킹','원MIPS/GPU','실기'],
      'separate_blocked_edit':ev(H/'ultimate_arrival135_arms01/generation_failure.json'),
      'blocked135_retry_performed':False,'arc_changed':False,'approved_for_packing':False})
    receipt=d/'generation_source_origin.json';write(receipt,{'generated':ev(p),'builtin_original':'<LOCAL_PATH>','original_preserved':True})
    print(json.dumps({'review':ev(out)},ensure_ascii=False))
if __name__=='__main__':main()
