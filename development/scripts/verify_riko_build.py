"""전체 BIN의 변경 섹터·EDC/ECC·재생성 일치·원본 및 설정화 보존을 별도 읽기로 확인."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import load_project, inspect_references, digest, write_json
from src.psx_sector import validate_checks


def verify(build, repeat):
    for folder in (build, repeat):
        if not folder.resolve().is_relative_to((ROOT/'out/ver_buki_riko').resolve()):
            raise ValueError('Expected first-project output directories')
    profile = json.loads((ROOT/'config/ps1_us_slus00561.json').read_text(encoding='utf-8'))
    project = load_project(ROOT, 'ver_buki_riko')
    source = ROOT/project['source_bin']
    manifest = json.loads((build/'manifest.json').read_text(encoding='utf-8'))
    filename = manifest.get('bin_file', 'riko_idle.bin')
    if filename not in ('riko_idle.bin', 'riko_motion.bin'):
        raise ValueError('Unsupported output BIN filename')
    target = build/filename
    if digest(source) != profile['source_sha256']:
        raise ValueError('Original BIN changed')
    expected = manifest['modified_bin']['sha256']
    if digest(target) != expected or digest(repeat/filename) != expected:
        raise ValueError('Build readback or reproducibility mismatch')
    if source.stat().st_size != target.stat().st_size:
        raise ValueError('BIN size changed')
    expected_sectors = {s['lba'] for s in manifest['modified_bin']['changed_sectors']}
    found = []
    with source.open('rb') as a, target.open('rb') as b:
        lba = 0
        while True:
            old, new = a.read(2352*256), b.read(2352*256)
            if not old:
                if new: raise ValueError('Trailing output data')
                break
            if len(old) != len(new): raise ValueError('Short output')
            if old != new:
                for offset in range(0, len(old), 2352):
                    original, modified = old[offset:offset+2352], new[offset:offset+2352]
                    if original == modified: continue
                    sector = lba+offset//2352
                    if sector not in expected_sectors: raise ValueError('Unexpected changed sector')
                    validate_checks(original); validate_checks(modified)
                    if original[:24] != modified[:24]: raise ValueError('Sector header changed')
                    found.append({'lba': sector, 'changed_bytes': sum(x != y for x, y in zip(original, modified)),
                                  'data_changed_bytes': sum(x != y for x, y in zip(original[24:2072], modified[24:2072])),
                                  'edc_ecc_valid': True})
            lba += len(old)//2352
    if {f['lba'] for f in found} != expected_sectors:
        raise ValueError('Changed sector manifest mismatch')
    references = []
    for project_id in ('ver_buki_riko', 'ver_rin_nana'):
        references.append({'project': project_id, 'verified': inspect_references(ROOT, load_project(ROOT, project_id))})
    protected = {'MegaMan X4.cue': '2648ebb71da8724a5b7378b4837bd1ebb9cbff48b53f28f30e217d1cdbbd79aa',
                 'ePSXe2018/ePSXe.exe': 'a266ee19bbeba0da38ffbaa8b02b89fe2524af7a45a13ea9ff37feab7423986d',
                 'ePSXe2018/bios/SCPH1001.BIN': '71af94d1e47a68c11e8fdb9f8368040601514a42a5a399cda48c7d3bff1e99d3'}
    for path, hash_value in protected.items():
        if digest(ROOT/path) != hash_value: raise ValueError(f'Protected input changed: {path}')
    report = {'source_sha256': profile['source_sha256'], 'modified_sha256': expected,
              'repeat_build': str(repeat.resolve()), 'reproducible': True, 'size': target.stat().st_size,
              'total_sectors_compared': lba, 'changed_sectors': found, 'all_other_raw_bytes_unchanged': True,
              'protected_inputs': protected, 'reference_checks': references,
              'check_scope': 'Changed sector EDC/ECC, whole BIN byte comparison, exact source/reference hashes.'}
    path = build/('verification_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.local.json')
    write_json(path, report)
    print(json.dumps({'report': str(path), 'changed_sectors': found, 'reproducible': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--repeat', type=Path, required=True)
    args = parser.parse_args()
    verify(args.build, args.repeat)
