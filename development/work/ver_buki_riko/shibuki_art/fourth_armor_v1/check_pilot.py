"""포스 아머 대기 후보: 실제 자산을 사용하는 거부·재현·보존 검사."""
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.prepare_shibuki_fourth_idle import prepare

STUDY = Path(__file__).resolve().parent
PARENT = ROOT / 'out/ver_buki_riko/shibuki_arrival_victory_style_20261026T235455012767Z'
BUILD = ROOT / 'out/ver_buki_riko/shibuki_fourth_idle_20261027T002313205126Z'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    out = STUDY / ('checks_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(exist_ok=False)
    cases = []
    for name in ('wrong_parent', 'wrong_scope', 'rgba_raster', 'shared_conflict', 'oversize', 'missing_frame'):
        art = out / name
        shutil.copytree(STUDY / 'layers03', art, ignore=shutil.ignore_patterns('frame_*', '*.gif', '*review*'))
        parent = PARENT
        if name == 'wrong_parent':
            parent = out / 'unsupported_parent'
            parent.mkdir()
            shutil.copyfile(PARENT / 'modified.arc', parent / 'modified.arc')
            manifest = json.loads((PARENT / 'manifest.json').read_text(encoding='utf-8'))
            manifest['modified_bin']['sha256'] = '0' * 64
            write_json(parent / 'manifest.json', manifest)
        elif name == 'wrong_scope':
            manifest = json.loads((art / 'layers.json').read_text(encoding='utf-8'))
            manifest['frames'] = [0]
            write_json(art / 'layers.json', manifest)
        elif name == 'rgba_raster':
            Image.open(art / 'head_000.png').convert('RGBA').save(art / 'head_000.png')
        elif name == 'shared_conflict':
            path = art / 'head_116.png'
            im = Image.open(path)
            x, y, _, _ = im.getbbox()
            im.putpixel((x, y), 1 if im.getpixel((x, y)) != 1 else 2)
            im.save(path, transparency=0)
        elif name == 'oversize':
            path = art / 'body_000.png'
            im = Image.open(path)
            im.putpixel((10, 10), 1)
            im.save(path, transparency=0)
        elif name == 'missing_frame':
            # Delete only a single newly copied fixture, never an input asset.
            missing = (art / 'head_119.png').resolve()
            assert missing.is_relative_to(out.resolve())
            missing.unlink()
        try:
            prepare(art, parent)
        except (ValueError, FileNotFoundError) as exc:
            cases.append({'case': name, 'rejected': True, 'error': str(exc)})
        else:
            raise AssertionError('Invalid input accepted: ' + name)
    write_json(out / 'negative_inputs.json', cases)

    arcs = [ROOT / 'work/ver_buki_riko/shibuki_fourth_idle' / stamp / 'modified.arc'
            for stamp in ('20261027T002246808636Z', '20261027T002335038253Z')]
    expected_arc = 'b165f3d33528605ffdcec209c413ce135b29bfd498c4d095de97b6e6f2929188'
    assert arcs[0].read_bytes() == arcs[1].read_bytes() == (BUILD / 'modified.arc').read_bytes()
    determinism = [{'path': str(p.relative_to(ROOT)), 'sha256': digest(p)} for p in arcs]
    assert all(item['sha256'] == expected_arc for item in determinism)
    write_json(BUILD / 'determinism.json', {'byte_identical': True, 'inputs': determinism})

    protected = [
        ('MegaMan X4.bin', '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'),
        ('character/ver_buki_riko/buki(4th armor).webp', '729065c46a128b5a6e307673a35d31a4738e5db5addb7ffc995c8cf1131eddd9'),
        ('character/ver_buki_riko/buki(X).webp', 'd7476066b352ac041901b331ff1c78e7c05776df79392d114f7a69b7e61ed1c5'),
        ('out/ver_buki_riko/riko_sfx_20261026T022446511583Z/riko_motion.bin', '1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246'),
        (str((PARENT / 'shibuki_riko.bin').relative_to(ROOT)), '6a8e7519a229994bbb831be74d77324ce3ffd0afaefc370329208cd3f38a05a9'),
        (str((PARENT / 'modified.arc').relative_to(ROOT)), 'f8f1d567e612b5e60f5911a1b2930993a76951a1840d15821bafb0725fec2903'),
    ]
    evidence = []
    for path, expected in protected:
        actual = digest(ROOT / path)
        assert actual == expected, path
        evidence.append({'path': path, 'expected_sha256': expected, 'actual_sha256': actual, 'equal': True})
    assert digest(BUILD / 'shibuki_riko.bin') == '7d2d80d9254a3971ceb6541d3d28c2a3ec4fdb952953b2868ec8a6938547c593'
    write_json(BUILD / 'preservation.json', {
        'files': evidence,
        'live_user_saves_read_or_written': False,
        'note': '사용자가 현재 아머 수집 중이다. 이번 검사는 저장 파일을 열거나 변경하지 않았다.'})

    exe = (ROOT / 'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.exe').read_bytes()
    assert hashlib.sha256(exe).hexdigest() == 'dae43d44a9f3176208830ddbba0607bb627ebcd7faf9b36fc03dd0ffda34d2e8'
    cs = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    start, end = 0x800361B0, 0x800363F8
    instructions = list(cs.disasm(exe[start - 0x80010000 + 2048:end - 0x80010000 + 2048], start))
    (STUDY / 'analysis/US_palette_copy.txt').write_text(
        '\n'.join(f'{i.address:08X} {i.mnemonic} {i.op_str}' for i in instructions) + '\n', encoding='utf-8')
    write_json(BUILD / 'pilot_checks.json', {
        'negative_cases': cases,
        'fixture_folder': str(out.relative_to(ROOT)),
        'deterministic_arc': True,
        'protected_files_checked': len(evidence),
        'runtime_verified': False,
        'game_was_not_controlled': True,
    })
    print(json.dumps({'negative_cases_rejected': len(cases), 'deterministic_arc': True,
                      'protected_inputs': len(evidence), 'output': str(out)}))


if __name__ == '__main__':
    main()
