"""흰 HUD 몸체만 확장한 v3를 기존 진행을 보존하면서 적용한다."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_frame_apply as apply
from scripts.hud_frame_underlay import SOURCES


def configure():
    apply.SOURCES = SOURCES
    apply.FINAL = {
        'ver_buki_riko': '33125a35f256f48aa4814b2f071a8de7b924f8e021d0c90f941e841e3f773b27',
        'ver_rin_nana': '24949917b23b8fc7e3ae2da9976f5116c769e6b549a00b248a50314115bcab25',
    }
    apply.WORK = ROOT / 'work/hud_frame_fix_20261105/underlay_white_v3'
    apply.OLD_STATE = '43a5eda05884a844154383ad1c86efaa20ddfc11d01e17d50b431b84cae17aa5'
    apply.NEW_STATE = 'ae56761ff6fbb0280c02735e29e2439f6951193b6fbe314ea1c72b416f0535d7'
    apply.CLONE = ROOT / 'work/hud_frame_fix_20261105/checkpoint/nana_white_underlay_v3/SLUS_005.61.000'
    apply.LIVE = ROOT / 'work/overhaul_20261105/hud_underlay_followup/live_progress'
    apply.BUILD_FOLDER = 'hud_white_underlay_20261105_v3'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['trial', 'activate'])
    parser.add_argument('--session', type=Path, required=True)
    args = parser.parse_args()
    configure()
    (apply.trial if args.action == 'trial' else apply.activate)(args.session)
