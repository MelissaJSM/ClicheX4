"""린 보닛의 시각적 중심을 게이지 축에 맞춰 왼쪽 1픽셀 이동한다."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_reference_details as previous
from scripts import hud_frame_underlay as engine
from scripts import hud_frame_fix as base
from scripts import hud_larger_aligned as layout_module
from scripts.prepare_rin_common import read_disc
from scripts.project import digest
from scripts.discover_inputs import sha256

SOURCES = {'ver_rin_nana': ('rin_nana','2ed8c388fafe4122aee301bf932632f1fef4ca80fff9cb8c93ea93ffc99bc29f')}
SOURCE_FOLDER = 'hud_reference_details_20261105_v8'
LAYOUTS = previous.LAYOUTS
require = base.require


def patch(arc):
    require(sha256(arc) in engine.CONTEXT, 'Unsupported v8 source ARC')
    _, _, _, name = engine.CONTEXT[sha256(arc)]
    new, proof = previous.patch(arc)
    if name != 'PL01_U.ARC':
        require(new == arc, 'Nana resources must remain byte identical')
    proof.update(rin_optical_horizontal_offset=-1 if name=='PL01_U.ARC' else 0,
                 canonical_art_pixels_unchanged=True,
                 symbol_method='optical_alignment_only')
    return new, proof


def configure():
    previous.configure()
    layout_module.LAYOUTS['ver_rin_nana']['PL01_U.ARC'] = (21,19,-19,23)
    native, _ = read_disc(ROOT/'MegaMan X4.bin',base.NAMES)
    source = ROOT/'out/ver_rin_nana'/SOURCE_FOLDER/'rin_nana.bin'
    require(digest(source)==SOURCES['ver_rin_nana'][1], 'Current v8 BIN differs')
    current, _ = read_disc(source,base.NAMES)
    symbols, _ = read_disc(ROOT/'out/ver_rin_nana/overhaul_20261105_candidate04/rin_nana.bin',base.NAMES)
    engine.CONTEXT.clear()
    for name in base.NAMES:
        engine.CONTEXT[sha256(current[name])] = (native[name],symbols[name],'ver_rin_nana',name)
    base.SOURCES = SOURCES
    base.SOURCE_FOLDER = SOURCE_FOLDER
    base.BUILD_KIND = 'rin_emblem_shifted_left_one_native_pixel'
    base.patch = patch


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','build'])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--project',choices=SOURCES,default='ver_rin_nana')
    parser.add_argument('--proposal',type=Path)
    args=parser.parse_args()
    configure()
    if args.action=='prepare':
        base.prepare(args.output)
    else:
        base.build(args.project,args.proposal,args.output)
