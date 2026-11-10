"""원본 마크의 조준선/하트/장식을 복원한 v8을 현재 진행에 적용한다."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_frame_apply as apply
from scripts.hud_reference_details import SOURCES


def configure():
    apply.SOURCES = SOURCES
    apply.FINAL = {
        'ver_buki_riko': '92ab09adf0284c0581a6993c88f64b2348f4e2bdc886e4ca9df1e1bc8c2bdb50',
        'ver_rin_nana': '2ed8c388fafe4122aee301bf932632f1fef4ca80fff9cb8c93ea93ffc99bc29f',
    }
    apply.WORK = ROOT / 'work/hud_frame_fix_20261105/reticle_v8'
    apply.OLD_STATE = '8a576e6b9acb1ab2f453cd17eed1278cf9ef515fb728acb82fa0b3c451c10819'
    apply.NEW_STATE = 'aa1c53decbc5a7883e88224347c34aa19017fbb7691104664361b3e3a38e19ed'
    apply.CLONE = ROOT / 'work/hud_frame_fix_20261105/checkpoint/nana_reference_v8/SLUS_005.61.000'
    apply.LIVE = ROOT / 'work/overhaul_20261105/hud_reference_details/live_progress'
    apply.BUILD_FOLDER = 'hud_reference_details_20261105_v8'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['trial', 'activate'])
    parser.add_argument('--session', type=Path, required=True)
    args = parser.parse_args()
    configure()
    (apply.trial if args.action == 'trial' else apply.activate)(args.session)
