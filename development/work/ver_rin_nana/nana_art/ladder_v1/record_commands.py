from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];p=ROOT/'docs/COMMANDS.md'
text='''
## 2026-10-30 나나 사다리14참조 (실행 완료)

```powershell
python scripts/prepare_shibuki_ladder_plan.py --project ver_rin_nana
work/tools/voice_env/Scripts/python.exe scripts/normalize_nana_ladder.py --source work/ver_rin_nana/nana_art/ladder_v1/generated.png --output work/ver_rin_nana/nana_art/ladder_v1/production01
work/tools/voice_env/Scripts/python.exe scripts/optimize_nana_ladder.py --art work/ver_rin_nana/nana_art/ladder_v1/production01 --parent out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z --steps 18000
python scripts/prepare_shibuki_ladder.py --project ver_rin_nana --art work/ver_rin_nana/nana_art/ladder_v1/production01 --parent out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z
python scripts/build_nana_run.py --scope ladder --candidate work/ver_rin_nana/nana_ladder/20261029T232636368928Z --reproduced work/ver_rin_nana/nana_ladder/20261029T232710157930Z
python -m unittest tests.test_psx_frame_edit tests.test_psx_compress tests.test_psx_player tests.test_psx_tile_layout tests.test_psx_paired_layout
python work/ver_rin_nana/nana_art/ladder_v1/checks.py
python scripts/emulator_session.py --project ver_rin_nana launch --cue out/ver_rin_nana/nana_ladder_20261029T232724676396Z/rin_nana.cue --card0 work/ver_rin_nana/test_cards/nana_ladder_v1/epsxe000.mcr --card1 work/ver_rin_nana/test_cards/nana_ladder_v1/epsxe001.mcr
```

ARC 준비는 독립2회 실행했다. 재실행 시 정규화/거부검사 출력 폴더는 새 이름을 사용한다. 기본 Python에는 scipy가 없으므로 이미지 정규화·배치 탐색은 기존 격리 voice_env 환경을 명시한다. 실기는 기존 저장의 그래픽만 갱신한 F3를 사용했고 사다리 발동 전수 검사는 미완료다. 실행 중인 에뮬레이터가 있으면 중복 실행하지 않는다. [결과·정적/실기 구분](NANA_LADDER.md).
'''
with p.open('a',encoding='utf8')as f:f.write(text)
