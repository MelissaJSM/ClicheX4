"""실제로 열람한 노바 패킹/원순서 판만 제작자 의견으로 기록한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_nova_candidate_v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=P/'producer_visual_review.json';assert not out.exists();files=[P/f'readback_{i}.png'for i in range(1,5)]+[D/f'native_cycle_v1/timeline_106_{i}.png'for i in range(1,5)]+[D/'targets_preview_v1/preparation_layers.png']
 r={'candidate_sha256':sha(P/'PL02_U.ARC'),'actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in files],'observations':['준비213의 앞손/옆팔·접힌무릎과215의 높은주먹/굽힌팔/긴다리에서 새 확정 절단을 찾지 못했다. 머릿결과 재킷/맨팔 명암이 대기 방향과 이어진다.','217의 새머리/홍채와 모인 두 신발이 기존 얇은 하체보다 구분된다.215에서217로 전신자세가 크게 바뀌는 것은 원표 전환이며, 동일원점 정지순서도에서 새머리의 명백한 축소/팔다리 분리를 찾지 못했다. 실제 빠른 게임 시각판단은 별도이다.','218/220에서는 새몸을 덮던 기존 효과영역을 재등록해 새몸윤곽이 이어지며,219 새실루엣은 새몸을 따른다.220 에너지 오른쪽 끝 world x87까지 패킹/재추출에서 보존된다.','효과색은 고정 팔레트의 비교일 뿐 실제 CLUT시간변화·블렌딩·물리·이벤트 실행을 검증한 것은 아니다. 214/216 기존 Nana별칭 유지와 원US 변형/흰섬광 복원은 구분한다.'],'offline_canvas_verified':True,'runtime_verified':False,'new_art_final_acceptance':False,'scope':'완성 재추출4+원순서4+준비층1 실제열람. 독립reader·루트 검토·실기는 각각 별도이다.'};out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'files':len(files),'sha256':sha(out)}))
if __name__=='__main__':main()
