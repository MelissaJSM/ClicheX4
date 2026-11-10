"""실제로 본90/91 최종판과 무기정책의 한계를 보존한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_recoil_candidate_v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 paths=[P/'readback_1.png',D/'native_cycle_v1/timeline_91.png',D/'common_probe_v2/comparison.png',D/'first_registered_v1/comparison_1.png',D/'first_registered_v1/comparison_2.png',D/'a_v1/generated.png'];out=P/'producer_visual_review.json';assert not out.exists()
 j={'candidate_arc_sha256':sha(P/'PL02_U.ARC'),'actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in paths],'findings':['새90/91 뒤머리의 가닥과 재킷 소매/몸통 명암이 대기와 직전새89에 더 가깝다. 새몸의 발바닥 높이는 원래와 같고 전신 확대/축소·옛몸복사를 하지 않았다.','90의 굽힌팔과91의수평팔에서 피부 하단음영/손목이 이어지며 새 확정 절단을 찾지 못했다. 원화가 가진 피부 밝은면은 유지하고 검정선을 임의추가하지 않았다.','초기v1의91팔아래 소매고립점을 실제후폼원화의 투명틈으로 재등록했다. 두몸의19경계셀을 기록했고 최종v2는 단일연결이다.','원표91의85→86→88→89→90→91→92 순서에서 새두그림과 기존연결을 정지판으로 비교했다.85/86/92를 새 제작으로 집계하지 않는다.'],'weapon_scope':'90은새원화의 사선권총/손을 공유한다.91은수용된85의20texel 사랑이를X−2,Y불변으로둔기본/포스수용정책이다. docs/NANA_SPECIALS.md가88..91을발사뒤올림/내림으로설명하며 원US91 단독탄환발생점 수치추출/실기증명을주장하지않는다.','source_policy_clarification':'초기common_probe_v2의 실제원91수평총구 위치유지 문구는 과대표현이며 targets_v1/manifest.json에서 위정책으로정정했다. 픽셀수정이아닌검증범위정정이다.','limits':'정지판 실제열람·오프라인기계재생·격리MIPS는별도증거다. 실제게임과 인간실시간움직임관찰로표현하지않는다. 전체나나미술통일은미완료.','runtime_verified':False}
 out.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
if __name__=='__main__':main()
