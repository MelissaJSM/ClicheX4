"""직접 열람 범위와 실패한 중간본을 최종 준비본 밖에 기록한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    p=H/'ultimate_hurt_author_review02.json';need(not p.exists(),'Fresh review')
    d=H/'prepared_ultimate_hurt02';need(sha((d/'PL02_U.ARC').read_bytes())=='b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94','Candidate changed')
    packed=[d/f'{f}_readback_{i:02}.png'for f in('before','after')for i in range(4)]
    ordered=[H/f'ultimate_hurt_sequence01/{f}_id{n}_ordered.png'for f in('before','after')for n in(33,34,35)]
    for f in packed:
        probe=H/'ultimate_hurt_pack_probe02'/f.name;need(f.read_bytes()==probe.read_bytes(),'Viewed probe differs from prepared')
    write(p,{'candidate':ev(d/'PL02_U.ARC'),'actually_viewed_via_view_image':{'packed':[ev(x)for x in packed],'ordered':[ev(x)for x in ordered]},'observations':['106/110/233/234의 새 머리 갈래·금색 장식과 재킷/맨팔 구획이 대기와 연결된다.','234 앞팔은 얼굴을 가로지르던 중간 원화에서 아래 팔꿈치로 접힌 새 국소 수정 형태로 돌아왔다.','109는 각 의상106 윤곽과 연결되고107/108 번개는 고정 원점에서 유지된다.','111 타일 복제 후에도 청색 감전 효과와 몸의 표시가 그대로다.112..114는 기존 정책의 공통 재킷 실루엣이며 두 의상을 각자 반영한 효과라고 주장하지 않는다.','235/236의 백색/청색 오라 사이에서 새234 몸이 같은 기준점과 체형을 유지한다.14판에서 추가 확정 손목·무릎 단절이나 갑작스러운 축소를 찾지 못했다.'],'limits':['정지 순서판 열람과710 canvas 검사는 연속 게임 영상을 직접 본 것과 다르다.','실제 넉백/상태종료/무적깜빡임/소리·모든 방향/피해원은 검사하지 않았다.','110 발끝은 이전보다1px 낮다.몸을 확대/축소하지 않았으며 실제 지면 접촉은 별도이다.'],'native':ev(H/'ultimate_hurt_v2_components_native_checks.json'),'independent':ev(H.parent/'zero_audit/shibuki_ultimate_hurt13_independent01/report.json'),'sequence':ev(H/'ultimate_hurt_sequence01/report.json'),'browser':ev(H/'ultimate_hurt_sequence01/browser_verification.json'),'root_final_review_pending':True,'runtime_verified':False,'full_project_complete':False})
    write(H/'ultimate_hurt_v1_rejection.json',{'candidate':ev(H/'prepared_ultimate_hurt01/PL02_U.ARC'),'excluded_from_final_integration':True,'cause':'원 MIPS/GPU 검사에서 New GPU U edge PL02_U.ARC/0/111/5/16 검출.원 base의 예외 타일을 새 layer5에 그대로 사용한 저장 배치 문제.','art_change_required':False,'replacement':ev(d/'PL02_U.ARC'),'correction':'원 효과 tile16 전체256nibble을 빈31에 복제하고111 layer5 레코드 하나만16→31. 원base16과목표65층은그대로.','v2_native_passed':True,'v1_retained_as_intermediate':True})
    print(json.dumps({'review':sha(p.read_bytes())}))
if __name__=='__main__':main()
