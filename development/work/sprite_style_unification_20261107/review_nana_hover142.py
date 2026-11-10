from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/ultimate_hover_repaint'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();arc=D/'packed_hover_candidate_v1/PL02_U.ARC'
assert sha(arc)=='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff'
images=[D/'packed_hover_candidate_v1'/f'readback_{n}.png'for n in range(1,6)]+[D/'muzzle_contacts_probe_v1'/f'comparison_{n}.png'for n in range(1,4)]+[D/'jet_contacts_probe_v1'/f'comparison_{n}.png'for n in(221,223,225,227,229)]
r={'checkpoint':142,'candidate_sha256':sha(arc),'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in images],'count':13,'observations':['새 호버10 자세의 재독출5판에서 머리갈래·얼굴·의상·새 팔과 정본 권총·추진 부츠 구분을 직접 보았다.','현재 실제 표시마스크15로 평가했다. 상층0만의 반신 표시는 실제 완성형 몸체와 구분한다.','첫 탄환 위치를 나타낸 중립색3판에서 원점과 새 권총 입구의 연결을 확인했다. 이전 총끝 고정 후보를 실발사점 증명으로 사용하지 않는다.','추진 효과 중립색5판에서 발과 효과의 겹침 관계가 유지되며 추가 확정 이탈을 찾지 못했다.'],'limitations':['탄환/추진 합성은 중립색 점유 비교이며 실제 CLUT·게임 실행·동작 시간 검증은 아니다.','원순서 애니메이션 검토는 별도로 진행한다.'],'runtime_verified':False,'whole_project_complete':False}
p=W/'root_review_checkpoint142.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
