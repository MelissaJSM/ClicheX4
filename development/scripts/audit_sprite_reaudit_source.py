"""스프라이트 재검토의 현재 입력과 이전 검토판 픽셀 출처를 읽기 전용으로 결속한다."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.build_hurt_capsule_fix import require, write_json
from src.psx_disc import file_hash

WORK = ROOT / 'work/sprite_reaudit_20261106'
EXPECTED = {
    'ver_buki_riko': ('shibuki_riko', '8c1a2fa5b3f985be9945717d3d88776f2f4534030c42818843ec8093a3ce1a81',
                      '5a57b31c7a4410d697183a01b2246a28344c847cefb331d27aad56135e7a924d'),
    'ver_rin_nana': ('rin_nana', 'dcdf175eb93014da90d1bfb429774b48533e1c156e289a3ac49f969ea7a0f9c7',
                     'de818d585fe1a4455d9b07551f3161b24357e3a1a2343d84102628a1fde55679'),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    WORK.mkdir(exist_ok=True)
    previous = json.loads((ROOT / 'work/hurt_capsule_fix_20261106/audit/protection_before.json').read_text('utf8'))
    paths = set(previous['files'])
    result = {}
    names = ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC', 'MOJIPAT.ARC', 'LOAD_U.ARC', 'SLUS_005.61')
    for mode, (stem, expected, album_sha) in EXPECTED.items():
        pointer = json.loads((ROOT / 'projects' / mode / 'current_build.json').read_text('utf8'))
        source = ROOT / pointer['build'] / (stem + '.bin')
        album_source = ROOT / 'out' / mode / 'sprite_consistency_20261105_v1' / (stem + '.bin')
        require(pointer['sha256'] == file_hash(source) == expected, 'Current source mismatch')
        require(file_hash(album_source) == album_sha, 'Album source mismatch')
        current, _ = read_disc(source, names)
        old, _ = read_disc(album_source, names)
        checks = {}
        for name in names[:3]:
            checks[name] = {}
            for kind in (2, 3, 9):
                a, b = entry(current[name], kind), entry(old[name], kind)
                require(a == b, 'Prior album no longer represents current player graphics')
                checks[name][str(kind)] = {'size': len(a), 'sha256': sha(a), 'exact_match': True}
        for name in ('MOJIPAT.ARC', 'LOAD_U.ARC'):
            require(current[name] == old[name], 'Prior UI sprite collection stale')
            checks[name] = {'size': len(current[name]), 'sha256': sha(current[name]), 'exact_match': True}
        # The only later EXE edit restored boss introductions; player timing/display code must be unchanged.
        delta = [i for i, (a, b) in enumerate(zip(current['SLUS_005.61'], old['SLUS_005.61'])) if a != b]
        allowed = set(range(0x800921F8 - 0x80010000 + 2048, 0x800921F8 - 0x80010000 + 2052))
        require(len(current['SLUS_005.61']) == len(old['SLUS_005.61']) and set(delta) <= allowed,
                'Player animation/display executable differs')
        result[mode] = {'bin': source.relative_to(ROOT).as_posix(), 'bin_sha256': expected,
                        'album_bin_sha256': album_sha, 'graphics_composition_palette_UI': checks,
                        'EXE_changed_offsets': delta, 'player_animation_display_code_identical': True,
                        'album_revised_mapping_must_be_used': True}
        paths.update(p.relative_to(ROOT).as_posix() for p in (source, source.with_suffix('.cue')))
    proof = WORK / 'source_identity.json'
    require(not proof.exists(), 'Source evidence already exists')
    write_json(proof, {'passed': True, 'projects': result,
                       'scope': '현재 BIN과 이전 최종 검토판 입력의 그림/조립/팔레트/UI 및 플레이어 코드 동일성. 미술 품질 통과가 아님.'})
    protection = {p: {'sha256': file_hash(ROOT / p), 'size': (ROOT / p).stat().st_size} for p in sorted(paths)}
    write_json(WORK / 'protection_before.json', {'files': protection, 'count': len(protection)})
    print(json.dumps({'source_identity': True, 'protected_files': len(protection)}))


if __name__ == '__main__':
    main()
