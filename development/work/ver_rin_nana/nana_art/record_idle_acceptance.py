import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
def read(p):return json.loads(p.read_text('utf8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
project=ROOT/'projects/ver_rin_nana/project.json';d=read(project)
build='out/ver_rin_nana/nana_idle_shot_20261029T055257544069Z'
accept={'date':'2026-10-29','quote':'좋아 충분해 계속 작업해도 되겠어','scope':'나나 대기·정지 사격 실적용 테스트 수용 및 다음 이동 제작 진행','build':build,'build_sha256':'02f8c18047c5705ea247a9f880f7c50a5b1866922a2c68c877a497af6962a3a4','source':'user','automated_exhaustive_runtime':False}
d['active_substage']='NANA_RUN_PRODUCTION';d['nana_idle_standing_acceptance']=accept;d['latest_integrated_build']=build;d['nana_pilot']['game_applied']=True;write(project,d)
pointer=ROOT/'projects/ver_rin_nana/current_build.json';d=read(pointer);d['user_tested_accepted']=True;d['acceptance']=accept;write(pointer,d)
manifest=ROOT/build/'manifest.json';d=read(manifest);d['new_animation_user_accepted']=True;d['user_acceptance']=accept;write(manifest,d)
runtime=ROOT/build/'runtime';runtime.mkdir(exist_ok=True);write(runtime/'user_acceptance.json',accept)
p=ROOT/'docs/DECISIONS.md';s=p.read_text('utf8');p.write_text('# 2026-10-29 나나 대기·정지 사격 사용자 수용\n\n사용자 “좋아 충분해 계속 작업해도 되겠어”로 `02f8c180…`의 대기·정지 사격을 수용했다. 이전의 직접 테스트 요청에 이어진 사용자 관찰이며 자동 전수 실기 검증으로 기록하지 않는다. 수용 도트와 팔레트를 유지하며 이동·이동 사격을 다음 묶음으로 제작한다. [제작 기록](NANA_PRODUCTION.md).\n\n'+s,'utf8')
p=ROOT/'docs/NANA_PILOT.md';s=p.read_text('utf8');p.write_text('> 2026-10-29 갱신: v9 기준안과 후속 대기·정지 사격 실적용을 사용자가 수용했다. 아래 미수용/미적용 설명은 초기 조사 이력이다. 현재 상태는 [나나 제작](NANA_PRODUCTION.md)을 따른다.\n\n'+s,'utf8')
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8');start=s.index('2026-10-29.');end=s.index('## 현재 적용본');s=s[:start]+'2026-10-29. `EXPANSION`, 활성 `ver_rin_nana/x_nana`. 나나 기준안과 대기·정지 사격 실적용은 사용자 테스트 수용. 수용한 대기 도트·팔레트를 고정하여 이동·이동 사격을 제작 중이다. 린 및 공통 한글/로고는 수용판을 계승한다. 풀네임 **아오쿠모 린 / 하나코 나나**. [나나 제작](NANA_PRODUCTION.md), [미술 기준](NANA_ART_DIRECTION.md), [공통 통합](RIN_COMMON_LOCALIZATION.md).\n\n'+s[end:];s=s.replace('- [CUE](../out/ver_rin_nana/rin_common_20261029T051459667484Z/rin_nana.cue), BIN SHA-256 `5434083adbcbb4dd651a4b6e83228dd6cbc2ca6a03291d882db13ba58de55571`.','- [CUE](../out/ver_rin_nana/nana_idle_shot_20261029T055257544069Z/rin_nana.cue), BIN SHA-256 `02f8c18047c5705ea247a9f880f7c50a5b1866922a2c68c877a497af6962a3a4`.\n- 나나 대기·정지 사격10참조/7스트림 적용. 전체251793섹터 비교, 변경12섹터 EDC/ECC,508압축참조 대조, 독립 ARC 재제작, 보호20파일·관련20단위 검사·4입력 거부 검사 통과. 사용자 실기 수용, 자동 전수 실기 미실행. 아래 린/공통 검사는 누적 계승 근거다.');start=s.find('다음 대상 나나의 대기0');end=s.find('## 보호 기준',start);s=s[:start]+'나나 대기·정지 사격 이후 모션과 UI·일러스트·개인 효과·음성은 순차 제작 대상이다. 미제작 동작에는 공용 팔레트가 적용된 원작 X 그림이 남아 있다. 아머의 나나 디자인은 아직 제작하지 않았다.\n\n'+s[end:];p.write_text(s,'utf8')
p=ROOT/'AGENTS.md';s=p.read_text('utf8');s=s.replace('나나 기본형 기준안 제작','나나 기본형 모션 제작').replace('현재 기준안 제작·검토','현재 기본형 모션 제작');p.write_text(s,'utf8')
print('Acceptance recorded')
