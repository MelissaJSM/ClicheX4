import json
from pathlib import Path
R=Path(__file__).resolve().parents[3]
quote='심볼 확인해봤어 괜찮네 다음으로 넘어가자 일시정지 색상도 괜찮네'
p=R/'projects/ver_rin_nana/current_build.json';d=json.loads(p.read_text('utf8'));d.update(hud_theme_user_accepted=True,hud_theme_acceptance_quote=quote,runtime_verification_source='user visual acceptance; automated exhaustive runtime not performed');p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
p=R/'projects/ver_rin_nana/project.json';d=json.loads(p.read_text('utf8'));d['nana_hud_theme']={'build':'out/ver_rin_nana/nana_hud_theme_20261030T044031308363Z','sha256':'d966208b6698209c125ebaf34fbb32d7c70d7e0b1bb2bd441a23e6e2dffe2a49','user_accepted':True,'user_quote':quote,'symbol_meaning':'토끼귀 + 과녁; 얼굴이 아님','automated_exhaustive_runtime':False,'evidence':'docs/NANA_HUD_THEME.md'};d['nana_weapon_get']['acceptance_quote']='오케이 잘나온다 다음 작업으로 넘어가도 돼';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
items={
'docs/STATUS.md':'**최신 2026-10-30 / EXPANSION / ver_rin_nana/x_nana:** 기술 획득 일러스트와 토끼귀·과녁 체력바 심볼, 분홍 일시정지 메뉴를 사용자 실기 확인으로 수용했다. 현재 CUE `out/ver_rin_nana/nana_hud_theme_20261030T044031308363Z/rin_nana.cue`, BIN `d966208b6698209c125ebaf34fbb32d7c70d7e0b1bb2bd441a23e6e2dffe2a49`. 독립11파일/15단위/7거부/전체251793섹터·변경8섹터 EDC/ECC·20보호파일 검사 통과. 새 실행 세션 `20261030T044407793268Z`. 자동 실기 전수는 미실행이며 사용자 확인을 근거로 수용한다. 다음은 나나 잔기 아이템·개인 효과. 아머 의상은 미제작. [적용·제약](NANA_HUD_THEME.md). 아래는 이전 단계 기록이다.',
'docs/DECISIONS.md':'## 2026-10-30 나나 기술 획득·HUD·메뉴 수용\n\n사용자 “오케이 잘나온다 다음 작업으로 넘어가도 돼”로 기술 획득 그림을 수용했다. 심볼은 사용자 “아 나나 심볼 자세히 설명해주면 토끼귀야. 그리고 얼굴 아니고 과녁이야!”에 따라 토끼귀와 과녁으로 해석한다. 얼굴·하트 해석을 최종안에 사용하지 않는다. 사용자 “'+quote+'”로 `d966208b…`의 HUD와 일시정지 색상을 수용했다. 다음 잔기·개인 효과로 진행한다. 원본과 첫 모드를 보존하며 아머 의상 제작은 포함하지 않는다. [검사](NANA_HUD_THEME.md).',
'docs/ART_DIRECTION.md':'**2026-10-30 나나 심볼 확정:** `character/ver_rin_nana/nana(X)_mark.webp`는 토끼귀와 과녁/조준선이다. 사용자 직접 설명을 근거로 얼굴로 해석하지 않는다. 작은 체력바에서는 은색 금속 명암의 귀·원형 과녁·중앙 조준선을 유지한다. 새 마크와 분홍 메뉴는 사용자 수용 완료. [원화와 제약](NANA_HUD_THEME.md).',
'docs/TEST_RESULTS.md':'2026-10-30: 나나 기술 획득 그림 사용자 수용. 이어서 [HUD·메뉴](NANA_HUD_THEME.md) `d966208b…`의 9체력바 단계와 다른 정적 표시593/597개 보존, 독립11파일/15단위/7거부 검사 통과. 전체251793섹터·변경8섹터 EDC/ECC·두 ARC 재추출·20보호파일 검사 통과. 새 실행 후 사용자가 심볼·일시정지 색상을 확인하고 수용했다. 자동 프레임버퍼 전수 비교는 미실행.',
'docs/COMMANDS.md':'# 나나 HUD·메뉴 색상 (2026-10-30)\n\n실행한 준비·독립 재제작·빌드·검사 명령은 [NANA_HUD_THEME.md](NANA_HUD_THEME.md)에 있다. 최신 `nana_hud_theme_20261030T044031308363Z`는 사용자 수용 완료. 이전 기술 획득 검사 대기는 해제되었다.'}
for name,txt in items.items():
 p=R/name;s=p.read_text('utf8');i=s.find('\n\n');p.write_text(s[:i+2]+txt+'\n\n'+s[i+2:],'utf8')
p=R/'docs/NANA_WEAPON_GET.md';s=p.read_text('utf8');s=s.replace('**새 일러스트의 실기·사용자 수용은 대기**다.','이후 사용자 “오케이 잘나온다 다음 작업으로 넘어가도 돼”로 실제 표시와 그림을 수용했다. 아래 대기 기록은 수용 전 이력이다.');p.write_text(s,'utf8')
print('acceptance recorded')
