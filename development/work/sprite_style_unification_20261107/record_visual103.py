from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=W/'root_review_checkpoint103.json';assert not p.exists()
paths=[W/'shibuki_audit/prepared_hurt_base01'/f'{form}_readback_{n:02}.png' for form in('base','fourth')for n in range(4)]
p.write_text(json.dumps({'root_actually_viewed':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)}for q in paths],
 'findings':['시부키 기본/포스 피격13의 네이티브 재추출8판을 직접 열람했다. 대기 기준의 얇은 보라 윤곽, 옷 경계, 머릿결, 명암 구획이 피격4몸체에도 유지된다. 추가 확정 몸체 분리·갑작스러운 체형 축소는 찾지 못했다.',
 '235/236 새234몸 위로 원 시부키 백색/청색 오라가 연결된다. 기존 포스 의상 조각을 효과로 남기지 않는 수정 정책을 확인했다. 원보이스/판정/시간을 바꾸는 수정이 아니다.'],
 'limits':['정지 네이티브 재추출 열람이며 원순서 재생과 실제 피격 실행은 별도다.','부분착용 전조합의 미술 전수 판정·사용자 수용으로 확대하지 않는다.'],
 'arc_sha256':sha(W/'shibuki_audit/prepared_hurt_base01/PL00_U.ARC'),'final_user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(p.name,sha(p))
