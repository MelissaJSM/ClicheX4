"""BR31 실제 디스크 재추출과 최신 동결을 결속한다. 게임은 실행하지 않는다."""
from pathlib import Path
import copy
import json
import sys

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import digest


def ev(p):
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': digest(p)}


def main():
    report_path = H / 'br31_readback01.json'
    need(not report_path.exists() and not (H / 'fullform_ledger44.json').exists(), '저장된 결과 보호')
    latest = ROOT / 'out/ver_buki_riko/sprite_style_unification_20261107_v31/shibuki_riko.bin'
    prior = ROOT / 'out/ver_buki_riko/sprite_style_unification_20261107_v30/shibuki_riko.bin'
    manifest_path = latest.parent / 'manifest.json'
    manifest = json.loads(manifest_path.read_text('utf8'))
    expected = 'ad4f2ceab100098e88977f383d314efd0337379feb70999989eaa53926332516'
    need(digest(latest) == manifest['modified_bin']['sha256'] == expected, '완성 BR31 해시')
    need(digest(prior) == 'ccdf6058c2f105057dbb105c71988d683ffca604492b60c665e5f2eab2f69875', '기준 BR30 해시')
    names = ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC', 'ST0E_U1.ARC', 'SLUS_005.61')
    now, records = read_disc(latest, names)
    old, old_records = read_disc(prior, names)
    frozen = {
        'PL00_U.ARC': H.parent / 'root_shibuki_hover/packed_hover_candidate03',
        'PL02_U.ARC': H / 'prepared_vehicle_head_ultimate01',
    }
    for name, directory in frozen.items():
        lock = json.loads((directory / 'FROZEN.json').read_text('utf8'))
        need(lock['frozen'] and sha(now[name]) == lock['candidate_sha256'], '통합 자원 동결 해시')
        need(now[name] == (directory / name).read_bytes(), '실제 디스크 자원 exact')
    for name in ('PL01_U.ARC', 'ST0E_U1.ARC', 'SLUS_005.61'):
        need(now[name] == old[name], '비대상 자원 보존')
    need(sha(now['ST0E_U1.ARC']) == '47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5', '선택 사본 보호')
    need(all(records[n]['lba'] == old_records[n]['lba'] and records[n]['size'] == old_records[n]['size'] for n in names), 'LBA/크기 보존')
    write(report_path, {
        'passed': True, 'bin': ev(latest), 'manifest': ev(manifest_path), 'baseline': ev(prior),
        'resources': {n: sha(now[n]) for n in names},
        'frozen_records': {n: ev(d / 'FROZEN.json') for n, d in frozen.items()},
        'lba_and_size_exact': {n: {'lba': records[n]['lba'], 'size': records[n]['size']} for n in names},
        'unchanged_Riko_selection_and_EXE': True, 'actual_disc_readback': True,
        'new_gameplay_execution_here': False, 'new_native_execution_here': False,
        'limits': ['새 디스크의 실제 자원 읽기와 바이트 대조만 수행했다.', '원MIPS·전체 섹터·게임 실행·실제 GPU 검사는 루트의 별도 결과다.'],
    })
    q = json.loads((H / 'fullform_ledger43.json').read_text('utf8'))
    q['previous_ledger'] = ev(H / 'fullform_ledger43.json')
    q['active_integration'] = {
        'project': 'ver_buki_riko', 'build': 'sprite_style_unification_20261107_v31',
        'bin_sha256': expected, 'PL00_sha256': sha(now['PL00_U.ARC']),
        'PL02_sha256': sha(now['PL02_U.ARC']), 'ST0E_sha256': sha(now['ST0E_U1.ARC']),
        'proof': ev(report_path), 'new_independent_bin_readback_here': True,
        'unaccepted_generated_art_included': False, 'new_gameplay_execution_here': False,
    }
    for entry in q['current_candidates'].values():
        entry.update(integrated=True, integrated_build='BR31')
    for key in ('tiny_vehicle_head_base_frozen', 'tiny_vehicle_head_ultimate_frozen', 'hover_frozen_base_fourth'):
        q[key].update(integrated=True, integrated_build='BR31')
    q['current_remaining']['pending_integration'] = []
    q['current_remaining']['integration_readback'] = ev(report_path)
    write(H / 'fullform_ledger44.json', q)
    keys = json.loads((H / 'unique_art_keys43.json').read_text('utf8'))
    keys['scope'] = 'BR31 실제 재추출의 기본8b4cc 및 Ultimate a0629 폼별 고유표시. 품질완료율이 아니다. 실기는 별도다.'
    keys['source_ledger'] = ev(H / 'fullform_ledger44.json')
    keys['candidates'] = q['current_candidates']
    keys['integration'] = q['active_integration']
    keys['remaining'] = q['current_remaining']
    keys['tiny_heads'] = {'base_frozen': q['tiny_vehicle_head_base_frozen'], 'ultimate_frozen': q['tiny_vehicle_head_ultimate_frozen']}
    write(H / 'unique_art_keys44.json', keys)
    print(json.dumps({'readback': ev(report_path), 'ledger': ev(H / 'fullform_ledger44.json'), 'keys': ev(H / 'unique_art_keys44.json')}))


if __name__ == '__main__':
    main()
