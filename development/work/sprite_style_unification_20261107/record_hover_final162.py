from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_shibuki_hover';P=D/'packed_hover_candidate03';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
arc=P/'PL00_U.ARC';assert sha(arc)=='8b4cc387a59c5cc04b365bac7bc31cacfca79a02054e891e90049e2943b53397'
files=[P/f'pair_{n}.png'for n in(221,223,225,227,229)]
data={'checkpoint':162,'candidate':arc.relative_to(ROOT).as_posix(),'candidate_sha256':sha(arc),'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in files],'observations':['최종 ARC를 재추출한 기본/포스 호버10자세를5판으로 대기와 직접 대조했다.','머리·옷깃·커프·부츠의 세부 묘사와 고정좌표를 확인했고, 추가 확정 손목/팔 절단이나 여분팔은 찾지 못했다.','3셀 피부색 정정과 짧은 원래 발사점228의 굽힌팔을 유지한다.'],'limits':['실제 게임 호버·제트·탄환 검증은 후속이다.','별도16개 참조는 그림을 바꾼 것이 아니라 저장 순서만 바꿨으며 원타일 역순열·표시 동일성을 기술검사로 구분한다.'],'native_decode_report':{'path':(D/'native_components03_native_checks.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'native_components03_native_checks.json')},'prior_art_review':{'path':(W/'root_review_checkpoint161.json').relative_to(ROOT).as_posix(),'sha256':sha(W/'root_review_checkpoint161.json')},'runtime_verified':False,'all_character_work_complete':False}
p=W/'root_review_checkpoint162.json';assert not p.exists();p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
