"""굵은 HUD 심볼에서 누락된 원본 마크의 핵심 세부를 복원한다."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_refined_symbols as refined
from scripts import hud_frame_underlay as engine
from scripts import hud_frame_fix as base
from scripts import hud_larger_aligned as larger
from scripts.prepare_rin_common import read_disc
from scripts.project import digest
from scripts.discover_inputs import sha256

SOURCES = {
    'ver_buki_riko': ('shibuki_riko','e667d707fb87e936bd72afe72685c49571c9443948ca9277914dc049ef555e26'),
    'ver_rin_nana': ('rin_nana','95c8ea61a2edafdaf53750a724999227fadf09408789ca36ae2c9cd356a30861'),
}
SOURCE_FOLDER = 'hud_refined_symbols_20261105_v7'
ART_ROOT = ROOT / 'work/hud_frame_fix_20261105/reticle_v8/art'
LAYOUTS = refined.LAYOUTS
require = base.require


def desired(before,native,symbol,bounds):
    # v7 has enlarged symbols outside the old y24..40 replacement rectangle.
    # Restore the native layer there before drawing the new foreground symbol.
    clean = before.copy()
    left,top = bounds[:2]
    for y0,y1 in ((22,24),(41,47)):
        clean[y0-top:y1-top,-24-left:5-left] = native[y0-top:y1-top,-24-left:5-left]
    return larger.desired(clean,native,symbol,bounds)


def patch(arc):
    result, proof = refined.patch(arc)
    proof.update(symbol_method='restore_reference_identity_details_at_native_size',
                 bold_style_size_and_alignment_retained=True)
    return result, proof


def configure():
    refined.ART_ROOT = ART_ROOT
    refined.configure()
    native, _ = read_disc(ROOT/'MegaMan X4.bin',base.NAMES)
    engine.CONTEXT.clear()
    for project,(stem,expected) in SOURCES.items():
        source = ROOT/'out'/project/SOURCE_FOLDER/(stem+'.bin')
        require(digest(source) == expected, 'Source v7 differs')
        current, _ = read_disc(source,base.NAMES)
        symbols, _ = read_disc(ROOT/'out'/project/'overhaul_20261105_candidate04'/(stem+'.bin'),base.NAMES)
        for name in base.NAMES:
            engine.CONTEXT[sha256(current[name])] = (native[name],symbols[name],project,name)
    base.SOURCES = SOURCES
    base.SOURCE_FOLDER = SOURCE_FOLDER
    base.BUILD_KIND = 'bold_HUD_reference_details_restored'
    engine.desired = desired
    base.patch = patch


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare','build'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--project', choices=SOURCES)
    parser.add_argument('--proposal', type=Path)
    args = parser.parse_args()
    configure()
    if args.action == 'prepare':
        base.prepare(args.output)
    else:
        base.build(args.project,args.proposal,args.output)
