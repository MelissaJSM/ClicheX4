"""크기를 보강한 심볼을 게이지 중심에 맞추고 원작 금속 홈 위에 배치한다."""
import argparse
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_aligned_bevel as aligned
from scripts import hud_frame_underlay as engine
from scripts import hud_frame_fix as base
from scripts.discover_inputs import sha256

SOURCES = aligned.SOURCES
SOURCE_FOLDER = aligned.SOURCE_FOLDER
SYMBOL_SOURCES = aligned.SYMBOL_SOURCES
LAYOUTS = {
    'ver_buki_riko': {'PL00_U.ARC': (21, 19, -18, 23), 'PL01_U.ARC': (18, 21, -17, 22), 'PL02_U.ARC': (21, 19, -18, 23)},
    'ver_rin_nana': {'PL00_U.ARC': (18, 21, -16, 22), 'PL01_U.ARC': (21, 19, -18, 23), 'PL02_U.ARC': (18, 21, -16, 22)},
}
CURRENT_LAYOUT = None
require = base.require


def symbol_layer(symbol, bounds, layout):
    width, height, target_x, target_y = layout
    left, top = bounds[:2]
    old = symbol[24-top:41-top, -24-left:2-left]
    ys, xs = np.where(old != 0)
    crop = old[ys.min():ys.max()+1, xs.min():xs.max()+1]
    # Discrete index selection: no new colors, blur or semitransparent pixels.
    row = np.minimum(((np.arange(height)+.5)*crop.shape[0]/height).astype(int), crop.shape[0]-1)
    col = np.minimum(((np.arange(width)+.5)*crop.shape[1]/width).astype(int), crop.shape[1]-1)
    expanded = crop[row[:, None], col[None, :]]
    require(set(np.unique(crop)) == set(np.unique(expanded)), 'Symbol palette details lost')
    result = np.zeros_like(symbol)
    result[target_y-top:target_y-top+height, target_x-left:target_x-left+width] = expanded
    return result


def desired(before, native, symbol, bounds):
    require(CURRENT_LAYOUT is not None, 'Missing explicit symbol layout')
    left, top = bounds[:2]
    out = aligned.WHITE_BODY(before, native, np.zeros_like(symbol), bounds)
    for y in range(29, 34):
        for x in range(-19, 2):
            out[y-top, x-left] = 12 if y in (29, 33) or x in (-19, 1) else (11 if y == 32 else 10)
    enlarged = symbol_layer(symbol, bounds, CURRENT_LAYOUT)
    mask = enlarged != 0
    require(not np.any(mask & (native == 14)), 'Enlarged symbol overlaps number aperture')
    out[mask] = enlarged[mask]
    require(np.array_equal(out == 14, (native == 14) | (enlarged == 14)), 'Numeric dark aperture changed')
    require(np.array_equal(out[:22-top], before[:22-top]), 'Vertical health gauge changed')
    require(np.array_equal(out[:, 5-left:], before[:, 5-left:]), 'Numeral/right frame changed')
    return out


def patch(arc):
    global CURRENT_LAYOUT
    require(sha256(arc) in engine.CONTEXT, 'Unsupported source ARC')
    _, _, project, name = engine.CONTEXT[sha256(arc)]
    CURRENT_LAYOUT = LAYOUTS[project][name]
    new, proof = engine.patch(arc)
    proof.update(native_groove_extended=True, symbol_layout=list(CURRENT_LAYOUT),
                 symbol_pixels_preserved=False, symbol_palette_and_index_features_preserved=True,
                 symbol_source='accepted_candidate04', placement='gauge_axis_and_optical_body_center',
                 target_gauge_axis_x=-8, native_number_aperture_preserved=True,
                 unchanged_health_gauge_max_y=21)
    return new, proof


def configure():
    aligned.configure()
    engine.desired = desired
    base.patch = patch
    base.BUILD_KIND = 'larger_centered_symbols_on_native_metal_groove'


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
