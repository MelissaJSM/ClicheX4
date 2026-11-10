"""이번 대기 후보와 확보된 사용자 저장의 경로·출처·미완료 범위를 기록한다."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parent
BUILD = ROOT / 'out/ver_buki_riko/shibuki_fourth_idle_20261027T002313205126Z'
SAVE = ROOT / 'work/ver_buki_riko/shibuki_full_armor_save/20261027T002949099058Z'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def relative(path):
    return path.relative_to(ROOT).as_posix()


def evidence(path):
    data = path.read_bytes()
    item = {'path': relative(path), 'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)}
    if path.suffix.lower() in ('.png', '.webp'):
        with Image.open(path) as im:
            item.update(image_size=list(im.size), mode=im.mode)
    return item


def prepend(path, text):
    old = path.read_text(encoding='utf-8-sig')
    title, rest = old.split('\n', 1)
    if text not in old:
        path.write_text(title + '\n\n' + text.strip() + '\n\n' + rest.lstrip(), encoding='utf-8')


def main():
    sources = [ROOT / 'character/ver_buki_riko/buki(4th armor).webp',
               ROOT / 'work/ver_buki_riko/shibuki_art/idle_chubby_v2/candidate09/shibuki_idle000_8x.png']
    artifacts = [STUDY / name for name in ('idle_prompt.txt', 'idle_correction_prompt.txt', 'idle_generated.png',
        'idle_generated_v2.png', 'normalize_idle.py', 'candidate02/normalization.json',
        'candidate02/full_outfit_indexed.png', 'make_idle_layers.py', 'layers03/layers.json')]
    artifacts += sorted((STUDY / 'layers03').glob('head_*.png')) + sorted((STUDY / 'layers03').glob('body_*.png'))
    artifacts += sorted((STUDY / 'layers03').glob('arm_*.png')) + sorted((STUDY / 'layers03').glob('leg_*.png'))
    write(STUDY / 'provenance.json', {
        'tool': 'built-in image_gen.imagegen',
        'skill': 'imagegen',
        'task': 'fourth_armor_shibuki',
        'sources': [evidence(p) for p in sources],
        'generated_outputs': [
            {'preserved_copy': 'idle_generated.png', 'generated_filename': 'exec-bbb2749c-6680-4dc6-9650-dc138eed9534.png', 'selected': False, 'reason': '소매가 기존 기본형 실루엣을 충분히 덮지 못함'},
            {'preserved_copy': 'idle_generated_v2.png', 'generated_filename': 'exec-9b045ec6-1e1f-480f-a710-cf67aec521fb.png', 'selected': True, 'reason': '같은 의상·포즈의 소매 보완'},
        ],
        'postprocessing': ['RGB555 인덱스 팔레트 정규화, 디더링 없음', '동일47px 축척·발 위치 정렬',
            '기존 얼굴·귀·눈 보존', '생성 의상89개 경계 픽셀 정렬, 최대3px', '부위별 레이어 분리 및 기존 호흡 규칙 적용'],
        'edge_registration': read(STUDY / 'layers03/layers.json')['edge_registration'],
        'artifacts': [evidence(p) for p in artifacts],
        'final_layers': relative(STUDY / 'layers03'), 'final_build': relative(BUILD),
        'runtime_verified': False, 'art_user_accepted': False, 'full_animation_complete': False,
    })
    recipe = read(BUILD / 'recipe.json')
    manifest = read(BUILD / 'manifest.json')
    candidate = {
        'project': 'ver_buki_riko', 'task': 'fourth_armor_shibuki', 'stage': 'EXPANSION',
        'kind': 'fourth_armor_idle_candidate', 'build': relative(BUILD),
        'cue': relative(BUILD / 'shibuki_riko.cue'), 'bin_sha256': manifest['modified_bin']['sha256'],
        'arc_sha256': manifest['modified_archive_sha256'], 'source_sha256': manifest['source_sha256'],
        'parent_build': recipe['parent_build'], 'parent_bin_sha256': recipe['parent_bin_sha256'],
        'source_art': relative(STUDY / 'layers03'), 'provenance': relative(STUDY / 'provenance.json'),
        'review': relative(BUILD / 'armor_review/review_1x_4x.png'), 'animation': relative(BUILD / 'armor_review/idle.gif'),
        'scope': recipe['edited_frame_references'], 'full_animation_complete': False,
        'unimplemented_armor_frames_use_original_bitmap_with_candidate_palette': True,
        'art_user_accepted': False, 'art_review_requested': True, 'runtime_verified': False,
        'static_combinations_verified': 192, 'report': 'docs/SHIBUKI_FOURTH_ARMOR.md',
        'full_armor_save_backup': relative(SAVE), 'full_armor_save_verified_from_bytes': True,
        'save_runtime_load_verified': False,
        'next': '시안 미술 수용 후 동작 확대; 별도 사본에서 실제 아머 대기 로딩 검사',
    }
    write(ROOT / 'projects/ver_buki_riko/shibuki_fourth_candidate.json', candidate)
    project_path = ROOT / 'projects/ver_buki_riko/project.json'
    project = read(project_path)
    project['active_substage'] = 'ARMOR_PILOT_REVIEW_AND_RUNTIME'
    project['fourth_armor_candidate'] = 'projects/ver_buki_riko/shibuki_fourth_candidate.json'
    project['fourth_armor_save_backup'] = relative(SAVE)
    write(project_path, project)
    old = ROOT / 'out/ver_buki_riko/shibuki_fourth_idle_20261027T002150082229Z'
    write(old / 'discarded.json', {
        'discarded': True, 'reason': '특수무기의 몸·효과2행을 건너뛰지 않은 초기 아머 팔레트 오류',
        'runtime_launched': False, 'was_accepted_current_build': False,
        'replacement': relative(BUILD), 'regression_test': 'tests/test_psx_armor_palette.py',
    })
    backup = read(SAVE / 'backup.json')
    for entry in backup:
        for key in ('source', 'backup'):
            assert hashlib.sha256((ROOT / entry[key]).read_bytes()).hexdigest() == entry['sha256']
    write(SAVE / 'final_preservation.json', {'all_four_files_preserved': True, 'source_and_backup_match': True,
        'source_files': [r['source'] for r in backup], 'emulator_launched': False, 'runtime_load_verified': False})
    prepend(ROOT / 'docs/STATUS.md', '''**2026-10-27 현재 — Shibuki 포스 아머 망토 대기 시안·전체 아머 저장 확보.** 단계 `EXPANSION`, 활성 `ver_buki_riko/fourth_armor_shibuki`, 세부 `ARMOR_PILOT_REVIEW_AND_RUNTIME`. 사용자 제작 지시와 망토 의상 선택에 따라 기존 얼굴·체형을 보존한 대기6참조를 별도 시험 BIN `7d2d80d9…`에 적용했다. 원본 미국판 `3ceab06a…`, 기존 기본형 수용본/현재 포인터 `6a8e7519…`는 보존한다. 후보 포인터는 `shibuki_fourth_candidate.json`으로 분리했다.

182단위 검사·부정 입력6건 거부·반복 ARC 동일·508그래픽 참조/대상 밖1763조립 대조·정적192조합·전체251793섹터/변경12섹터 EDC/ECC 통과. 원래 파츠/압축 슬롯에 들어가 재배치는 없었다. 다른 아머 동작은 아직 원래 X 그림에 후보 색상이며 전체 완성이 아니다. 실제 게임 실행·미술 수용은 미완료다.

사용자가 전체 아머 F1과 메모리카드2/슬롯3 저장을 알렸으며 `shibuki_full_armor_save/20261027T002949099058Z`에 백업·원본 보존을 확인했다. F1 `eff46e6e…`: X/아머0x0F/팔 종류2/8보스0xFF/대기118. 카드2 `ab68aa74…`의3번 슬롯도 X/아머0x0F/팔 종류2/최대HP48이다. 파일 해석 검증이며 F3·메뉴 로드는 미실행. **아머 저장 부족은 해소됐고, 시안 미술 수용 답변과 실행 검사가 남아 있다.** 다음은 백업 사본 기반 실제 아머 대기 확인 및 수용 후 이동·공격 확대다. [시안·입출력 해시·검사·저장 근거](SHIBUKI_FOURTH_ARMOR.md). 아래는 이전 시점 이력이다.''')
    prepend(ROOT / 'docs/TEST_RESULTS.md', '''**2026-10-27 포스 아머 대기 시험:** BIN `7d2d80d9…`, ARC `b165f3d3…`. 182단위 검사, 거부6건, ARC 반복 바이트 동일.508그래픽 참조·대상 밖1763조립·24아머 래스터·192부분 장착/팔 종류 조합 확인. 전체251793섹터 중12변경, EDC/ECC 통과. 기본형/원본/Riko 보존. 새 게임 실행은 미실행. 사용자 새 F1 `eff46e6e…`와 카드2/슬롯3에서 네 파츠/팔 종류2를 파일 읽기로 확인하고4파일 백업·원본 해시 보존. 저장 로드와 아머 그림의 실제 실행 증거로 확대하지 않는다. [상세 결과](SHIBUKI_FOURTH_ARMOR.md).''')
    prepend(ROOT / 'docs/SPRITE_SPEC.md', '''**2026-10-27 X 포스 아머 명세:** 조립 은행5/6/7/8과 비트1/2/4/8은 머리/몸/팔/다리이며, 기본 몸 위에 다리→머리→팔→몸 순서로 덧그린다. 기본/팔 종류2 아머 CLUT는0x7843/0x7844. 일반·점멸은 기준 팔레트+1/+2, 특수무기는 몸·효과2행 뒤인+2/+3을 사용한다. 미국판 원본 명령과 실제 ARC에서 확인했으며 새 아머의 실행 검증은 아니다. 대기0/115..119의 별도 파츠·타일/공유·압축 제한 및 원본 명령 증거는 [포스 아머 보고서](SHIBUKI_FOURTH_ARMOR.md)에 있다.''')
    prepend(ROOT / 'docs/ART_DIRECTION.md', '''**2026-10-27 Shibuki 포스 아머 시안 — 미술 수용 전:** 사용자가 설정화 왼쪽 망토 의상을 선택했다. 대기 `fourth_armor_v1/layers03`는 수용된 얼굴·귀·체형·47px 키·접지를 유지하고 의상·장식을 별도 파츠로 덮는다. 생성 의상 원본과 소매 보정, 팔레트 후처리, 경계89픽셀 정렬을 기록했다. 대기 시안만 제작했으며 전체 동작 기준의 사용자 수용은 아직 없다. [정적 비교·출처·생략/해석·제약](SHIBUKI_FOURTH_ARMOR.md).''')
    prepend(ROOT / 'docs/DECISIONS.md', '''## 2026-10-27 — 전체 아머 저장 제공과 대기 시안 범위

사용자 “지금 아머파츠를 다모았고 f1눌러서 저장했고 메모리카드 2번의 3번슬롯에 저장해놨어 확인해봐”에 따라 원본을 읽고 별도4파일 백업을 만들었다. F1과 카드2/슬롯3의 네 파츠·팔 종류2를 확인했다. 저장 부족은 해소됐으며 실제 로드 검증은 아직이다. 대기 후보는 기존 수용본과 분리하고 전체 동작 확대용 미술 수용을 질문했다. 저장 제공을 새 픽셀 시안의 미술 승인으로 해석하지 않는다. [근거](SHIBUKI_FOURTH_ARMOR.md).''')
    prepend(ROOT / 'docs/COMMANDS.md', '''## 2026-10-27 포스 아머 대기 시안

다음은 실제 실행한 명령이다. 원본·현재 수용본을 보존하는 별도 출력이며 새 아머 게임 실행은 하지 않았다. 분석·아트 출력 폴더가 이미 존재하면 덮어쓰기 없이 실패하도록 되어 있다.

```powershell
python scripts/analyze_shibuki_armor.py
python work/ver_buki_riko/shibuki_art/fourth_armor_v1/normalize_idle.py --source idle_generated_v2.png --candidate candidate02
python work/ver_buki_riko/shibuki_art/fourth_armor_v1/make_idle_layers.py
python scripts/prepare_shibuki_fourth_idle.py --art work/ver_buki_riko/shibuki_art/fourth_armor_v1/layers03
python scripts/build_shibuki_run.py --recipe work/ver_buki_riko/shibuki_fourth_idle/20261027T002246808636Z/recipe.json
python scripts/preview_shibuki_fourth_idle.py --build out/ver_buki_riko/shibuki_fourth_idle_20261027T002313205126Z
python -m unittest discover -s tests -q
python work/ver_buki_riko/shibuki_art/fourth_armor_v1/check_pilot.py
```

新규 저장은 로컬 Python 읽기/백업으로 조사했다. `shibuki_full_armor_save/20261027T002949099058Z`의 백업 목록·F1 해석·카드 슬롯 해석·US 저장/로드 명령을 보존했다. 카드2/슬롯3과 F1을 실제 에뮬레이터에서 로드한 명령은 아직 없다. [검사 결과와 한계](SHIBUKI_FOURTH_ARMOR.md).'''.replace('新규', '신규'))
    print(json.dumps({'candidate': relative(BUILD), 'save_backup': relative(SAVE),
                      'accepted_current_pointer_unchanged': read(ROOT / 'projects/ver_buki_riko/current_build.json')['bin_sha256'] == recipe['parent_bin_sha256'],
                      'report': 'docs/SHIBUKI_FOURTH_ARMOR.md'}))


if __name__ == '__main__':
    main()
