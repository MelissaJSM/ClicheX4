from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit';D=H/'prepared_standing_fire_ultimate01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'PL02_U.ARC')=='1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad'
images=[D/f'{form}_readback_{n:02}.png'for form in('before','after')for n in range(3)]+[H/'ultimate_standing_fire_sequence01'/f'{form}_id{n}_ordered.png'for form in('before','after')for n in(88,91)]
r={'checkpoint':140,'candidate':{'path':(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),'sha256':sha(D/'PL02_U.ARC')},'actually_viewed_images':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in images],'actual_images_count':10,'observations':['Ultimate 사격85..92의 전후 두 의상 재독출6판과 원순서88/91 네판을 직접 열람했다.','대기와 비교해 머리갈래·얼굴·의상·피부손·신발의 구분이 유지된다. 이번 판에서 추가 확정 분리나 큰 크기 도약은 찾지 못했다.','88의 원래 효과가 새 몸 앞에 표시됨을 정적 비교했다.'],'limitations':['실제 게임 플레이 검증은 아직 수행하지 않았다.','외부 무기 객체 궤적·가림과 모든60Hz시간 흐름을 이 정적판으로 증명하지 않는다.'],'whole_project_complete':False}
p=W/'root_review_checkpoint140.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
