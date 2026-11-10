"""직접 정리한 확대 심볼을 현재 진행을 보존하며 적용한다."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_frame_apply as apply
from scripts.hud_refined_symbols import SOURCES


def configure():
    apply.SOURCES = SOURCES
    apply.FINAL = {
        'ver_buki_riko': 'e667d707fb87e936bd72afe72685c49571c9443948ca9277914dc049ef555e26',
        'ver_rin_nana': '95c8ea61a2edafdaf53750a724999227fadf09408789ca36ae2c9cd356a30861',
    }
    apply.WORK = ROOT / 'work/hud_frame_fix_20261105/refined_v7'
    apply.OLD_STATE = 'ae56761ff6fbb0280c02735e29e2439f6951193b6fbe314ea1c72b416f0535d7'
    apply.NEW_STATE = '8a576e6b9acb1ab2f453cd17eed1278cf9ef515fb728acb82fa0b3c451c10819'
    apply.CLONE = ROOT / 'work/hud_frame_fix_20261105/checkpoint/nana_refined_v7/SLUS_005.61.000'
    apply.LIVE = ROOT / 'work/overhaul_20261105/hud_refined_symbols/live_progress'
    apply.BUILD_FOLDER = 'hud_refined_symbols_20261105_v7'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['trial', 'activate'])
    parser.add_argument('--session', type=Path, required=True)
    args = parser.parse_args()
    configure()
    (apply.trial if args.action == 'trial' else apply.activate)(args.session)
