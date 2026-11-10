from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit'
paths=[H/'standing_special_pack02'/n for n in ('base_readback.png','fourth_readback.png','partial_095.png')]
paths += [H/'prepared_standing_special_base01/partial_097.png']
paths += [H/'prepared_standing_special_ultimate01'/n for n in ('before_readback.png','after_readback.png','partial_095.png','partial_097.png')]
paths += [H/'standing_special_sequence01'/f'{f}_id{i}_ordered.png' for i in (95,104) for f in ('base','fourth','before','after')]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in paths],
'candidate_sha256':{'PL00_U.ARC':'fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e','PL02_U.ARC':'26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce'},
'findings':['95/96/97의 새 머릿결·옷 주름·얇은 밝은 외곽이 각 의상의 대기 기준과 이어진다.','기본/포스/얼티밋 전후 원표95·104의 정지 순서판을 직접 비교했으며 추가 확정된 몸체 분리나 발 위치 급변을 찾지 못했다.','부분 파츠 판에서 공통 얼굴·팔다리 경계와 의상 연결을 확인했다.'],
'limits':['정지 순서판 검토이며 연속 애니메이션 직접 시청이나 새 BIN 실기 검증이 아니다.','96은 새95의 x+1 파생으로 기존96 픽셀 동일성을 주장하지 않는다.','전체 캐릭터 미술 완료 및 최종 사용자 수용을 뜻하지 않는다.'],
'runtime_verified':False,'final_user_accepted':False}
p=W/'root_review_checkpoint127.json';assert not p.exists();p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
