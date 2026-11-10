"""확대 크기에 맞춰 직접 정리한 네 심볼을 금속 홈과 함께 삽입한다."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_larger_aligned as larger
from scripts import hud_frame_underlay as engine
from scripts import hud_frame_fix as base
from scripts.discover_inputs import sha256
from scripts.project import digest

SOURCES = larger.SOURCES
SOURCE_FOLDER = larger.SOURCE_FOLDER
SYMBOL_SOURCES = larger.SYMBOL_SOURCES
LAYOUTS = larger.LAYOUTS
ART_ROOT = ROOT / 'work/hud_frame_fix_20261105/refined_v7/art'
CHARACTERS = {
    'ver_buki_riko': {'PL00_U.ARC': 'shibuki', 'PL01_U.ARC': 'riko', 'PL02_U.ARC': 'shibuki'},
    'ver_rin_nana': {'PL00_U.ARC': 'nana', 'PL01_U.ARC': 'rin', 'PL02_U.ARC': 'nana'},
}
ART = {}
CURRENT_CHARACTER = None
require = base.require
ALLOWED = {
    'shibuki': {0, 3, 4, 10, 11, 12, 14},
    'riko': {0, 5, 6, 7, 8, 9, 10, 14},
    'nana': {0, 3, 4, 10, 11, 14},
    'rin': {0, 5, 6, 7, 8, 9, 10, 14},
}


def layer(symbol, bounds, layout):
    width, height, x, y = layout
    pixels, _ = ART[CURRENT_CHARACTER]
    require(pixels.shape == (height, width), 'Wrong refined symbol dimensions')
    result = np.zeros_like(symbol)
    result[y-bounds[1]:y-bounds[1]+height, x-bounds[0]:x-bounds[0]+width] = pixels
    return result


def patch(arc):
    global CURRENT_CHARACTER
    require(sha256(arc) in engine.CONTEXT, 'Unsupported source ARC')
    _, _, project, name = engine.CONTEXT[sha256(arc)]
    CURRENT_CHARACTER = CHARACTERS[project][name]
    result, proof = larger.patch(arc)
    proof.update(symbol_palette_and_index_features_preserved=False,
                 symbol_method='hand_refined_at_final_native_resolution',
                 palette_bytes_unchanged=True,
                 symbol_art=(ART_ROOT/(CURRENT_CHARACTER+'.json')).relative_to(ROOT).as_posix(),
                 symbol_art_sha256=ART[CURRENT_CHARACTER][1])
    return result, proof


def configure():
    for name, size in [('shibuki',(21,19)),('riko',(18,21)),('nana',(18,21)),('rin',(21,19))]:
        path = ART_ROOT/(name+'.json')
        data = json.loads(path.read_text('utf8'))
        require((data['width'],data['height']) == size, 'Refined art dimensions differ')
        require(len(data['rows']) == size[1] and all(len(r) == size[0] for r in data['rows']), 'Ragged indexed art')
        require(all(c in '0123456789ABCDEF' for r in data['rows'] for c in r), 'Invalid indexed art')
        pixels = np.array([[int(c,16) for c in row] for row in data['rows']],dtype=np.uint8)
        require(np.any(pixels) and np.any(pixels == 0), 'Invalid transparent symbol')
        require(set(map(int,pixels.flat)) <= ALLOWED[name], 'Unexpected character colors')
        ART[name] = (pixels,digest(path))
    larger.configure()
    larger.symbol_layer = layer
    base.patch = patch
    base.BUILD_KIND = 'hand_refined_larger_centered_HUD_symbols'


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
        base.build(args.project,args.proposal,args.output)
