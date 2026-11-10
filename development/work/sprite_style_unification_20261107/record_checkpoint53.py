from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent; ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pages=[W/'shibuki_audit/base_run_contacts02'/f'{form}_all_{i:02}.png' for form in ('base','fourth') for i in range(3)]
record={'art_review_images':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'root_actually_viewed':True} for p in pages],
 'findings':['기본/포스 보행15자세씩의6판 모두 직접 열람. 머리 내부층·옷깃·부츠 경계가 대기와 가까워진 방향을 수용한다.','포스 달리기 가슴의 흰색은 이전2/4의 큰 흰 덩어리보다 개선되었다.'],
 'limits':['고정 접점 원화 등록 단계이며 아직 사격팔 합성·부분파츠·패킹·실제 게임 검증은 아니다.','대기와 움직임의 모든 전환 및 최종 품질 완료를 뜻하지 않는다.'],
 'next':'공통층 및 사격팔 합성 후 어깨 연결·윤곽·부분 조합·원순서 반복 검토', 'final_user_accepted':False}
p=W/'root_review_checkpoint53.json'; assert not p.exists()
p.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8'); print(sha(p))
