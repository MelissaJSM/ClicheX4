from pathlib import Path
import json
import hashlib

O = Path(__file__).resolve().parent
ROOT = O.parents[2]
read = lambda p: json.loads(p.read_text('utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = read(O / 'context_manifest.json')
for name, digest in manifest['inputs'].items():
    assert sha(ROOT / name) == digest, name
match = read(O / 'nana_fourth_historical_context_match.json')
assert match['whole_composite_exact'] and match['historical_scene_exact_pixels'] == 2521
assert match['head_parts5_opaque'] == 78 and not match['head5_empty']
names = ['historical_vehicle_page0.png', 'shibuki_before_after_static.png',
         'four_characters_current_static.png', 'nana_idle_vehicle_comparison.png']
out = O / 'visual_review.json'
assert not out.exists()
result = {
    'scope': '현재 네 캐릭터12폼의 작은 머리 조종석 정적 비교와 Nana 베일 누락 의심 재검토.',
    'actually_viewed_files': [
        {'path': (O / n).relative_to(ROOT).as_posix(), 'sha256': sha(O / n), 'actually_viewed': True}
        for n in names
    ],
    'input_hashes_unchanged': True,
    'observations': [
        '시부키 새 기본/포스/Ultimate전후의 머리184·196을 기존 머리와 같은 실제 몸체0에 놓았다. 직접 본 정적 표본에서 추가 확정 부유/큰 크기 도약/목 연결 단절은 찾지 못했다.',
        'Riko와 Rin의 일반/블랙, Nana와 Shibuki 네 의상의 작은 머리를 함께 비교했다. 선택한 몸체0 위에서 추가 확정 누락은 찾지 못했다.',
        'Nana 기본과 포스가 같아 보이는 첫 인상은 누락으로 확정하지 않았다. 포스 머리층5의78불투명 픽셀과 베일 연장을 직접 확인했다.',
        '현재 Nana 포스184와 보존된 실제 차량 몸체0를 좌우반전·원점(160,160)으로 결합하면 과거 X 차량 상태 화면의2521불투명 픽셀 전체와 exact다. 베일 파츠 누락 주장은 근거 없음으로 닫았다.',
    ],
    'latest_live_vehicle_test': False,
    'limits': manifest['limits'] + [
        '과거 X/Nana 차량 화면과 현재 머리의 픽셀 동일성은 새 BR31의 실제 부팅/조종석 플레이를 대신하지 않는다.',
        '라이드 체이서 손잡이/발판, 다른 차량 몸체 프레임과의 동적 접점은 여전히 별도 검증이다.',
    ],
    'context_manifest_sha256': sha(O / 'context_manifest.json'),
    'nana_historical_match_sha256': sha(O / 'nana_fourth_historical_context_match.json'),
    'new_art_or_rom_changes': False,
    'all_character_work_complete': False,
}
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(sha(out))
