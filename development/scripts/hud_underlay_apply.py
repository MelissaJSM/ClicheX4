"""연속 HUD 몸체 v2의 검증된 입력만 기존 보존형 적용기에 전달한다."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import hud_frame_apply as apply
from scripts.hud_frame_underlay import SOURCES

def configure():
    apply.SOURCES=SOURCES
    apply.FINAL={'ver_buki_riko':'8541da021edfadec70d4da4e4b7f423ae79ded2f1c3cb72b5718d0ae566df63a',
                 'ver_rin_nana':'675ff984709f7557f4dc4ed9a54bd7cbc179e79430e0f0eda5640c31107648df'}
    apply.WORK=ROOT/'work/hud_frame_fix_20261105/underlay_v2'
    apply.OLD_STATE='43a5eda05884a844154383ad1c86efaa20ddfc11d01e17d50b431b84cae17aa5'
    apply.NEW_STATE='8a70c554f68689c9545c3a04ca9b416da3d2f45d74e9695e1427e9b8c2e43347'
    apply.CLONE=ROOT/'work/hud_frame_fix_20261105/checkpoint/nana_underlay_v2/SLUS_005.61.000'
    apply.LIVE=ROOT/'work/overhaul_20261105/hud_underlay_followup/live_progress'
    apply.BUILD_FOLDER='hud_underlay_20261105_v2'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['trial','activate']);p.add_argument('--session',type=Path,required=True);args=p.parse_args();configure()
    (apply.trial if args.action=='trial'else apply.activate)(args.session)
