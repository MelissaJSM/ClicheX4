"""v3 HUD의 기존 왼쪽 금속 홈을 가로로 연결해 빈 흰 면을 마감한다."""
import argparse
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_frame_underlay as previous
from scripts import hud_frame_fix as base
from scripts.project import digest
from scripts.prepare_rin_common import read_disc
from scripts.discover_inputs import sha256

SOURCES = {
    'ver_buki_riko': ('shibuki_riko', '33125a35f256f48aa4814b2f071a8de7b924f8e021d0c90f941e841e3f773b27'),
    'ver_rin_nana': ('rin_nana', '24949917b23b8fc7e3ae2da9976f5116c769e6b549a00b248a50314115bcab25'),
}
SOURCE_FOLDER = 'hud_white_underlay_20261105_v3'
SYMBOL_SOURCES = previous.SYMBOL_SOURCES
require = base.require


def desired(before, native, symbol, bounds):
    out = before.copy()
    left, top = bounds[:2]
    # Extend the native 5px metallic groove, using its original A/B/C tones.
    # Existing left cap x=-20..-19 stays intact. The new right bevel ends at x=1,
    # before the original life-number rim at x=2. No E/navy fill is added.
    for y in range(29, 34):
        for x in range(-19, 2):
            if y in (29, 33) or x in (-19, 1):
                value = 12
            else:
                value = 11 if y == 32 else 10
            out[y-top, x-left] = value
    mask = np.zeros(out.shape, dtype=bool)
    mask[24-top:41-top, -24-left:2-left] = symbol[24-top:41-top, -24-left:2-left] != 0
    out[mask] = symbol[mask]
    require(np.array_equal(out == 14, (native == 14) | (mask & (symbol == 14))),
            'Native number aperture or symbol dark pixels changed')
    require(np.array_equal(out[mask], symbol[mask]), 'Accepted symbol pixels changed')
    require(np.array_equal(out[:, 2-left:], before[:, 2-left:]), 'Life-number rim changed')
    require(np.array_equal(out[:24-top], before[:24-top]), 'Health bar changed')
    allowed = np.zeros(out.shape, dtype=bool)
    allowed[29-top:34-top, -19-left:2-left] = True
    require(np.array_equal(out[~allowed], before[~allowed]), 'Unrelated HUD pixels changed')
    return out


def patch(arc):
    new, proof = previous.patch(arc)
    proof.update(native_groove_extended=True, groove_bounds=[-19, 29, 2, 34],
                 original_left_cap_preserved=True, native_number_rim_x2plus_preserved=True)
    return new, proof


def configure():
    original = ROOT / 'MegaMan X4.bin'
    require(digest(original) == '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b',
            'Original BIN differs')
    native, _ = read_disc(original, base.NAMES)
    previous.CONTEXT.clear()
    for project, (stem, expected) in SOURCES.items():
        source = ROOT / 'out' / project / SOURCE_FOLDER / (stem + '.bin')
        symbols = ROOT / 'out' / project / 'overhaul_20261105_candidate04' / (stem + '.bin')
        require(digest(source) == expected and digest(symbols) == SYMBOL_SOURCES[project], 'Source identity changed')
        assets, _ = read_disc(source, base.NAMES)
        symbol_assets, _ = read_disc(symbols, base.NAMES)
        for name in base.NAMES:
            previous.CONTEXT[sha256(assets[name])] = (native[name], symbol_assets[name], project, name)
    previous.WHITE_ONLY = True
    previous.desired = desired
    base.SOURCES = SOURCES
    base.SOURCE_FOLDER = SOURCE_FOLDER
    base.BUILD_KIND = 'native_metal_groove_extended_original_number_aperture'
    base.patch = patch


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'build'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--project', choices=SOURCES)
    parser.add_argument('--proposal', type=Path)
    args = parser.parse_args()
    configure()
    if args.action == 'prepare':
        base.prepare(args.output)
    else:
        base.build(args.project, args.proposal, args.output)
