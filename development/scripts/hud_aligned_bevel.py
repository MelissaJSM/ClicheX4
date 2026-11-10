"""원작 금속 홈 마감과 심볼 중심 정렬. 숫자칸과 게이지 위치는 유지한다."""
import argparse
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_frame_underlay as original_underlay
from scripts import hud_beveled_underlay as bevel
from scripts import hud_frame_fix as base
from scripts.discover_inputs import sha256

SOURCES = bevel.SOURCES
SOURCE_FOLDER = bevel.SOURCE_FOLDER
SYMBOL_SOURCES = bevel.SYMBOL_SOURCES
WHITE_BODY = original_underlay.desired
SHIFTS = {
    'ver_buki_riko': {'PL00_U.ARC': 1, 'PL01_U.ARC': 1, 'PL02_U.ARC': 1},
    'ver_rin_nana': {'PL00_U.ARC': 2, 'PL01_U.ARC': 2, 'PL02_U.ARC': 2},
}
CURRENT_DX = None
require = base.require


def desired(before, native, symbol, bounds):
    require(CURRENT_DX is not None, 'Missing explicit symbol alignment')
    left, top = bounds[:2]
    # Rebuild the whole empty native white body, removing the previous symbol.
    out = WHITE_BODY(before, native, np.zeros_like(symbol), bounds)
    for y in range(29, 34):
        for x in range(-19, 2):
            out[y-top, x-left] = 12 if y in (29, 33) or x in (-19, 1) else (11 if y == 32 else 10)
    old_mask = np.zeros(symbol.shape, dtype=bool)
    old_mask[24-top:41-top, -24-left:2-left] = symbol[24-top:41-top, -24-left:2-left] != 0
    ys, xs = np.where(old_mask)
    moved_mask = np.zeros_like(old_mask)
    shifted = np.zeros_like(symbol)
    require(np.all(xs+CURRENT_DX < symbol.shape[1]), 'Shift leaves composed HUD')
    shifted[ys, xs+CURRENT_DX] = symbol[ys, xs]
    moved_mask[ys, xs+CURRENT_DX] = True
    require(not np.any(moved_mask & (native == 14)), 'Symbol overlaps life-number aperture')
    out[moved_mask] = shifted[moved_mask]
    require(np.array_equal(out == 14, (native == 14) | (shifted == 14)), 'Number aperture changed')
    require(np.array_equal(out[ys, xs+CURRENT_DX], symbol[ys, xs]), 'Symbol shape/colors changed')
    require(np.array_equal(out[:24-top], before[:24-top]), 'Gauge body moved')
    require(np.array_equal(out[:, 5-left:], before[:, 5-left:]), 'Counter digits/right frame moved')
    protected_rim = np.zeros(out.shape, dtype=bool)
    protected_rim[:, 2-left:] = True
    protected_rim &= ~moved_mask
    require(np.array_equal(out[protected_rim], before[protected_rim]), 'Uncovered numeric rim changed')
    return out


def patch(arc):
    global CURRENT_DX
    require(sha256(arc) in original_underlay.CONTEXT, 'Unsupported source ARC')
    _, _, project, name = original_underlay.CONTEXT[sha256(arc)]
    CURRENT_DX = SHIFTS[project][name]
    new, proof = original_underlay.patch(arc)
    proof.update(native_groove_extended=True, symbol_translation=[CURRENT_DX, 0],
                 symbol_pixels_preserved=True, symbol_absolute_position_preserved=False,
                 target_gauge_axis_x=-8, numerical_aperture_preserved=True)
    return new, proof


def configure():
    bevel.configure()
    original_underlay.desired = desired
    base.patch = patch
    base.BUILD_KIND = 'native_metal_groove_with_centered_character_symbols'


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
