"""원작 금속 홈을 이어 붙인 HUD v4를 검증 후 진행을 보존하며 적용한다."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_frame_apply as apply
from scripts.hud_beveled_underlay import SOURCES


def configure():
    apply.SOURCES = SOURCES
    apply.FINAL = {
        'ver_buki_riko': '4f3754285df21d863473ed915975dd7f99426f70bd635973e79927d86749dbe0',
        'ver_rin_nana': 'd70d095f9d4cb9ebb5fe07e103afbbdc8d866c519069e2485b4a729f203aa4bb',
    }
    apply.WORK = ROOT / 'work/hud_frame_fix_20261105/beveled_v4'
    apply.OLD_STATE = 'ae56761ff6fbb0280c02735e29e2439f6951193b6fbe314ea1c72b416f0535d7'
    apply.NEW_STATE = '00b4ba1ecce9a858b242f8bd41741865cf3490d2815c29d0a5dce3771224f76c'
    apply.CLONE = ROOT / 'work/hud_frame_fix_20261105/checkpoint/nana_beveled_v4/SLUS_005.61.000'
    apply.LIVE = ROOT / 'work/overhaul_20261105/hud_bevel_followup/live_progress'
    apply.BUILD_FOLDER = 'hud_beveled_underlay_20261105_v4'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['trial', 'activate'])
    parser.add_argument('--session', type=Path, required=True)
    args = parser.parse_args()
    configure()
    (apply.trial if args.action == 'trial' else apply.activate)(args.session)
