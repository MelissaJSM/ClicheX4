"""실제 열람한 최종 재추출·원순서·원효과 점유판만 기록한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_hover_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=P/'producer_visual_review.json';assert not out.exists()
 files=[P/f'readback_{i}.png'for i in range(1,6)]+[D/f'native_cycle_v1/timeline_{i}.png'for i in [*range(21,27),*range(133,139)]]+[D/f'packed_contacts_v1/jets_{i}.png'for i in (221,223,225,227,229)]+[D/f'packed_contacts_v1/muzzle_{i}.png'for i in (1,2,3)]
 r={'candidate_sha256':sha(P/'PL02_U.ARC'),'actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in files],'observations':['재추출5판의 새 머리 층/피부 음영과 접힌 무릎·회색신발이 유지되며 목·손목·발목에 추가 확정 절단을 찾지 못했다.','222/224는 원발사점으로 낮춰 뻗은 새팔,226/228은 접힌팔이며230 손목도 정본총에 이어진다. 228 팔이 가슴앞을 덮지만 별도 추가팔이나 옛소매로 읽히는 확정 문제는 보이지 않는다.','원순서12판의 공중45~48 연결과 호버221..230 전환에서 새머리 전체 크기의 급격한 변화나 새 다리 단절을 찾지 못했다. 정지순서도 판단이며 인간 실시간 게임 관측은 아니다.','원15추진위상과 새 일반/사격짝 하체를 원점에 합성한5판에서 발과 추진점유가 이어진다. 227바닥1px차를 억지 평행이동으로 보정하지 않았다.','첫탄환188px 중립점유3판의 중심은 새총 앞면X−1에 있으며 그림 총 내부 중심/위로 분리되던 진단안 문제를 완화했다. 원색·블렌딩·렌더순서·게임물리는 별도다.'],'offline_canvas_verified':True,'runtime_verified':False,'new_art_final_acceptance':False,'scope':'25개 파일 직접열람. 기술적 단일연결만으로 미술완료를 주장하지 않으며 독립·루트·실기를 분리한다.'}
 out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'files':len(files),'sha256':sha(out)}))
if __name__=='__main__':main()
