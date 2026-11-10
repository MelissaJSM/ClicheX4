# 개발과 재현

## 공개 자료의 두 층

`platforms/`와 `tools/`는 배포 도구 및 현재 자산 추출 진입점입니다. `development/`는 실제 제작에 사용한 라이브러리·스크립트·검증·번역과 MIPS/x86 보정의 개발 이력을 보존합니다. 후자는 작업 당시의 상대 경로와 과거 해시를 사용하는 연구 코드도 포함합니다. 폴더 전체의 스크립트를 일괄 실행하지 마세요.

`development/work`는 실행 캐시가 아니라 **선택한 소스 파일만** 보존한 경로입니다. 원본 ARC/EXE, ROM, 모델, 저장 파일, 생성 중간 그림은 없습니다. 원래 개인 절대 경로가 있던 이력 소스는 `<LOCAL_PATH>`로 치환했으며 목록은 `docs/source-inventory.json`에 기록했습니다. 이력 파일의 `work/…` 또는 `out/…` 링크는 그 당시 로컬 입력·검증 결과를 뜻하며 모든 파일이 공개 자료에 포함됐다는 뜻은 아닙니다.

전체 제작 과정을 신규 원본에서 한 명령으로 재실행하는 빌드는 아직 제공하지 않습니다. 일부 생성 원화, 수동 선택 기록, 임시 입력이 공개 묶음 밖에 있기 때문입니다. 대신 **현재 패치의 적용/검증, 실행기 재빌드, 최종 자산 재추출**은 별도 진입점을 제공합니다.

## PS1 패처

Python 표준 라이브러리만 필요합니다.

```powershell
cd platforms/ps1
python -m unittest -v test_patcher
python patcher.py --source "원본.bin" --patch "ver_buki_riko.cxp" --output "새 출력 폴더" --report result.json
```

패치는 Releases ZIP에 있습니다. 원본+XOR 차이를 스트리밍 처리하고, 입력/출력 SHA-256을 모두 확인한 뒤 새 폴더를 확정합니다. 출력 폴더를 이미 만들었거나 같은 파일을 지정하면 중단합니다. `create()`는 입력·출력 해시를 명시하는 패치 제작 함수이며 완성 BIN 자체를 생성하는 아트 빌더는 아닙니다.

Windows 실행기 빌드:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install PyInstaller==6.22.3
.venv/Scripts/python.exe -m PyInstaller --onefile --windowed --name ClicheX4_PS1 platforms/ps1/patcher.py
```

실행 파일 옆에 두 `.cxp`와 안내/라이선스 파일을 둡니다. PyInstaller 부트로더 등 제3자 고지를 함께 배포합니다.

## Steam 실행기

`platforms/steam`은 실제 v1.0.3 설치기의 검토 가능한 소스입니다. Releases에 있는 같은 버전의 `patches.zip`을 이 폴더에 놓아 사용합니다. `release_config.py`의 패치 해시를 임의로 바꾸지 마세요.

```powershell
cd platforms/steam
python main.py
python -m PyInstaller --noconfirm ClicheX4.spec
```

PyInstaller 빌드 결과의 실행 파일과 `_internal` 폴더 옆에 해당 `patches.zip`을 둡니다. `runtime_specs/`는 빌드 설정에 포함됩니다. 검증 환경은 Python 3.13.14, PyInstaller 6.22.3입니다. 실행기 로직은 Python 표준 라이브러리와 Tkinter를 사용합니다.

## 최신 자산 다시 추출

필요 패키지는 `requirements-assets.txt`를 참고하세요. Windows의 맑은 고딕을 개발 미리보기에 사용하며 글꼴 파일은 배포하지 않습니다.

```powershell
python tools/export_assets.py --original "원본.bin" --br "shibuki_riko.bin" --rn "rin_nana.bin" --out "asset_export"
python tools/export_ui.py --br "shibuki_riko.bin" --rn "rin_nana.bin" --out "asset_export"
```

세 BIN은 `release-manifest.json`의 해시와 일치해야 합니다. 원본은 원작과 동일한 그림을 제외하는 비교용이며 입력 전용입니다. 일시정지 그림은 Unicorn에서 최종 MIPS 렌더러를 실행해 얻습니다. 이는 실제 플레이 검증과 구별됩니다. 출력은 새 작업 폴더를 권장합니다.

`tools/build_showcase.py`는 공개 자산에서 HTML 소개판과 모음집을 만듭니다. `tools/render_showcase.py`는 설치된 Chrome/Edge를 지정해 1600×1000 PNG로 출력합니다. 이미지 생성 모델이나 API 키는 필요 없습니다. 그림 자체를 다시 그리지 않고 문서 레이아웃만 구성합니다.

## 코드 위치

- `development/src/psx_player.py`: 압축 플레이어 그림·조립 참조 해석
- `development/src/psx_compress.py`, `psx_sector.py`, `psx_disc.py`: 압축·섹터·원본 보존 쓰기
- `development/src/psx_ui_atlas.py`, `psx_ui_render.py`: 인덱스 타일·팔레트·조립 일러스트
- `development/src/psx_korean_*`: 한글 글리프·배치·MIPS 연결
- `development/work/armor_dialogue_20261108`, `hq_armor_20261109`, `pause_variants_20261109`: 장비 상태별 초상화/전신/메뉴 선택과 로더
- `development/src/steam_*`: MT ARC, TEX/COF/PAT, UI·대화·오디오 및 실행 보정
- `platforms/steam/scripts/steam_*`: 배포 실행기의 엄격한 해시/명령 바이트 검사와 보정
- `development/work/ps1_sync_20261110`: 마지막 Steam→PS1 오드아이 반영·비대상 보존 검사

이전 코드는 실제 생성/검증의 이력이지만 그 안의 ‘현재’, ‘완료’, 날짜별 대상은 당시 시점을 가리킵니다. 공개 묶음의 현재 기준은 루트 `release-manifest.json`입니다.
