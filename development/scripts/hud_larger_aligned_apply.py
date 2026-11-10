"""확대·중앙 정렬·금속 홈 마감을 현재 진행을 보존하며 함께 적용한다."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_frame_apply as apply
from scripts.hud_larger_aligned import SOURCES


def configure():
    apply.SOURCES = SOURCES
    apply.FINAL = {
        'ver_buki_riko': 'b0c99979667c4c1c4b0ebded0f327ee4fa26beea3afca507b230ea1f51dea090',
        'ver_rin_nana': 'c698c882ff1f2bb3c7c70c9048a46765d217be1446b3a4786651bfaee703a693',
    }
    apply.WORK = ROOT / 'work/hud_frame_fix_20261105/larger_aligned_v6'
    apply.OLD_STATE = 'ae56761ff6fbb0280c02735e29e2439f6951193b6fbe314ea1c72b416f0535d7'
    apply.NEW_STATE = '21a35f03f9d84cd2c17e3619a21f6901e67baa0cded7266736896d1686162585'
    apply.CLONE = ROOT / 'work/hud_frame_fix_20261105/checkpoint/nana_larger_aligned_v6/SLUS_005.61.000'
    apply.LIVE = ROOT / 'work/overhaul_20261105/hud_larger_alignment/live_progress'
    apply.BUILD_FOLDER = 'hud_larger_aligned_20261105_v6'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['trial', 'activate'])
    parser.add_argument('--session', type=Path, required=True)
    args = parser.parse_args()
    configure()
    (apply.trial if args.action == 'trial' else apply.activate)(args.session)
