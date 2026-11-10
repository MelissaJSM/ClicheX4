import json
from pathlib import Path
R=Path(__file__).resolve().parents[3]
def load(p):return json.loads((R/p).read_text('utf-8'))
def save(p,v):(R/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
for p in ['projects/ver_buki_riko/shibuki_voice_candidate.json','work/ver_buki_riko/shibuki_voice_mute_v1/completion.json']:
    v=load(p);v.update(user_accepted=True,user_test_pending=False,user_quote='좋아 이상 없어',stage='VOICE_MUTED_USER_ACCEPTED',acceptance_source='2026-10-28 사용자 플레이 확인');save(p,v)
p='out/ver_buki_riko/shibuki_voice_mute_20261028T064914983985Z/manifest.json';v=load(p);v.update(user_accepted=True,user_quote='좋아 이상 없어');save(p,v)
p='projects/ver_buki_riko/project.json';v=load(p);v.update(active_task='cliche_title_voice',active_substage='TITLE_VOICE_RESEARCH_AND_PRODUCTION',shibuki_gameplay_voice_user_accepted=True);save(p,v)
for path,heading,body in [
('docs/STATUS.md','# 프로젝트 상태','**2026-10-28 최신 — X 플레이 보이스 무음 사용자 수용, Cliché X4 타이틀 콜 제작.** `EXPANSION / cliche_title_voice / TITLE_VOICE_RESEARCH_AND_PRODUCTION`. 사용자가 “좋아 이상 없어”로 무음 빌드 `ab78f90aef06d8a884a0ea1b5eef36faf5c3f5af1b3df74c92f7dd9922a5ecf2`를 수용했다. 이어 인트로의 “메가맨x4” 음성을 “클리셰x4”로 바꾸도록 요청했다. 원본 미국판 `3ceab06a…`과 수용 빌드는 입력 전용. 음원 위치·길이 조사와 로컬 음성 제작 진행 중이며 새 타이틀 음성 적용/청취는 아직 미검증이다. 기존 그래픽·한글·플레이 음향을 보존하는 같은 길이 교체가 목표이며 추가 승인 차단은 없다. 아래는 이전 시점 이력이다.'),
('docs/DECISIONS.md','# 결정 기록','## 2026-10-28 — X 무음 수용 및 타이틀 콜 교체 승인\n\n사용자 “좋아 이상 없어”를 X 기본/포스·얼티밋 플레이 보이스 무음 빌드 `ab78f90a…`의 수용으로 기록한다. 이어 “인트로 화면에 메가맨x4 라고 말하는 보이스 클리셰x4 라고 말하도록 보이스 작업좀 부탁할게”에 따라 해당 타이틀 콜의 제작·별도 BIN 적용을 진행한다. 기존 영상 전체 음성 교체까지 확대하지 않으며 원본, 수용 부모, 저장 파일은 보호한다. 로컬 공개 TTS로 새 안내 음성을 제작하고 원작의 재생 형식/길이 안에 넣는 경로를 조사한다.')]:
    p=R/path;s=p.read_text('utf-8');assert s.startswith(heading);p.write_text(heading+'\n\n'+body+'\n\n'+s[len(heading):].lstrip(),'utf-8')
p=R/'docs/SHIBUKI_VOICE_MUTE.md';s=p.read_text('utf-8');p.write_text('> 2026-10-28 후속 사용자 확인: “좋아 이상 없어”. 현재 무음 빌드 사용자 수용 완료. 아래의 청취 대기는 작성 당시 기록이며 자동 전수 음향 검증을 추가 완료했다는 뜻은 아니다.\n\n'+s,'utf-8')
