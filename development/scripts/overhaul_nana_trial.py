"""최종 통합본의 진행 보존 F1을 잠시 검증하고 사용자 원본 슬롯은 즉시 복원한다."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import digest

SOURCE_SHA = '736cdc2dc277767d2e4c8b935137bc9ad5ab07ff8074323e0b2f710070657719'
TARGET_SHA = '57977106f9bf2a8fae08834c94225fdcdf477d895e82256510e7a745f5259440'
BIN_SHA = '1a2d97272bb0dde2395aa7f1daa9136dd247125456090ff519fe3c484e3be2e2'
CLONE = ROOT / 'work/overhaul_20261105/audio/nana_user_progress_candidate04_final_v1/SLUS_005.61.000'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', type=Path, required=True)
    args = parser.parse_args()
    session = args.session.resolve()
    if not session.is_relative_to(ROOT / 'work/ver_rin_nana/emulator_sessions'):
        raise ValueError('Unexpected session path')
    record = json.loads((session / 'session.local.json').read_text('utf8'))
    if record['bin_sha256'] != BIN_SHA or digest(Path(record['cue']).with_suffix('.bin')) != BIN_SHA:
        raise ValueError('Unexpected mounted BIN')
    active = ROOT / 'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000'
    if digest(active) != SOURCE_SHA or digest(CLONE) != TARGET_SHA:
        raise ValueError('User progress or verified clone changed')
    output = ROOT / 'work/overhaul_20261105/runtime/nana_final_checkpoint_trial'
    output.mkdir(parents=True, exist_ok=False)
    backup = output / 'original_f1.000'
    shutil.copyfile(active, backup)
    results = []
    try:
        shutil.copyfile(CLONE, active)
        if digest(active) != TARGET_SHA:
            raise ValueError('Installed clone differs')
        # F3 loads the clone; Start immediately pauses for read-only inspection.
        for scan in ('0x3d', '0x35'):
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/korean_runtime_control.py'),
                '--project', 'ver_rin_nana', 'key', '--session', str(session), '--scan', scan],
                check=True, capture_output=True, text=True)
            results.append(json.loads(result.stdout))
    finally:
        shutil.copyfile(backup, active)
        if digest(active) != SOURCE_SHA:
            raise RuntimeError('User F1 restore failed')
    evidence = dict(session=str(session.relative_to(ROOT)), bin_sha256=BIN_SHA,
        source_sha256=SOURCE_SHA, clone_sha256=TARGET_SHA, original_F1_restored=True,
        cards_written=False, preview_written=False, runtime_key_results=results,
        scope='Asset-cache refreshed user progress; not fresh-disc loading proof')
    (output / 'evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n', 'utf8')
    print(json.dumps(evidence, ensure_ascii=False))

if __name__ == '__main__':
    main()
