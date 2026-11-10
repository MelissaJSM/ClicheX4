"""검증된 고정 크기 스프라이트 빌더를 이번 재검토 작업 공간에서 사용한다."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import build_sprite_consistency as builder


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    builder.WORK = ROOT / 'work/sprite_reaudit_20261106'
    builder.build(args.plan)
