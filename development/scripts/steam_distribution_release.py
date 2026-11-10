from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RELEASE='1.0.3'
BUILD=ROOT/'work/steam_distribution_20261110_v103'
STAGE=BUILD/'source'
OUT=ROOT/'out/releases'/('ClicheX4_Steam_v'+RELEASE)
