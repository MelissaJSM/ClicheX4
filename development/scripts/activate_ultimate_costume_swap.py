"""승인·독립 디스크 검사 후 최신 의상 교환 BIN 포인터를 연결한다."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.ultimate_costume_package import WORK, SOURCES, STEMS, write_json
from scripts.c01_audio_build import require
from scripts.project import working_cue
from src.psx_disc import file_hash

BUILD = 'ultimate_costumes_swapped_20261105_v1'
SESSIONS = {
    'ver_buki_riko': 'work/ver_buki_riko/emulator_sessions/20261105T093439953026Z',
    'ver_rin_nana': 'work/ver_rin_nana/emulator_sessions/20261105T092624071713Z',
}


def main():
    destination = WORK / 'application'
    require(not (destination / 'applied.json').exists(), 'Already activated')
    proof = json.loads((WORK / 'audit/applied_discs.json').read_text('utf8'))
    require(proof['passed'], 'Independent disc validation must pass')
    initial = json.loads((WORK / 'protection/before.json').read_text('utf8'))['files']
    pointer_names = {f'projects/{p}/{n}' for p in SOURCES for n in ('project.json', 'current_build.json')}
    protected = {p: r['sha256'] for p, r in initial.items() if p not in pointer_names}
    saves = json.loads((destination / 'before_mode_switch.json').read_text('utf8'))['files']
    protected.update(saves)
    for path, expected in protected.items():
        require(file_hash(ROOT / path) == expected, 'Protected file changed: ' + path)
    pending, summaries = {}, {}
    for project, (parent, parent_hash) in SOURCES.items():
        folder = ROOT / 'projects' / project
        cur = json.loads((folder / 'current_build.json').read_text('utf8'))
        cfg = json.loads((folder / 'project.json').read_text('utf8'))
        require(cur['sha256'] == cfg['latest_integrated_bin_sha256'] == parent_hash, 'Current parent changed')
        build = ROOT / 'out' / project / BUILD
        stem = STEMS[project]
        manifest = json.loads((build / 'manifest.json').read_text('utf8'))
        digest = file_hash(build / (stem + '.bin'))
        require(digest == manifest['modified_bin']['sha256'] == proof['projects'][project]['applied_sha256'],
                'Output differs from independently checked disc')
        require(manifest['parent_sha256'] == parent_hash and file_hash(ROOT / parent) == parent_hash,
                'Parent changed')
        cue = build / (stem + '.cue')
        require(cue.read_text('ascii') == working_cue((ROOT / parent).with_suffix('.cue').read_text('ascii'), stem + '.bin'),
                'CUE changed')
        session_path = SESSIONS[project]
        session = json.loads((ROOT / session_path / 'session.local.json').read_text('utf8'))
        require(session['bin_sha256'] == digest, 'Runtime session belongs to another build')
        nana = project == 'ver_rin_nana'
        if nana:
            require(json.loads((ROOT / session_path / 'close.local.json').read_text('utf8'))['exited'],
                    'Nana session not closed')
        else:
            command = json.loads((ROOT / session_path / 'ultimate_native_command.json').read_text('utf8'))
            require(command['activated'] and command['source_bin_sha256'] == digest,
                    'Native Ultimate command evidence differs')
            require(command['trace'][-1]['character'] == 0 and command['trace'][-1]['ultimate'] == 1 and
                    command['trace'][-1]['armor'] == 0, 'Unexpected Ultimate start state')
        stage = 'ULTIMATE_SWAP_USER_CHECKED' if nana else 'ULTIMATE_SWAP_APPLIED_REVIEW'
        cur.update(task='ultimate_costume_swap', stage=stage,
                   build=build.relative_to(ROOT).as_posix(), cue=cue.relative_to(ROOT).as_posix(), sha256=digest,
                   status_report='docs/ULTIMATE_COSTUME_SWAP.md', ultimate_swap_report='docs/ULTIMATE_COSTUME_SWAP.md',
                   ultimate_costume_policy='pre_capsule_jacket__acquired_swimsuit',
                   ultimate_swap_user_accepted=nana,
                   ultimate_swap_user_acceptance_source='나나모드는 내가 확인했어 부키모드 확인으로 넘어가자' if nana else None,
                   user_accepted=False, automatic_sprite_runtime_verified=False,
                   runtime_verification_scope='Nana checked by user; Shibuki fresh boot/native Ultimate command verified; sprite review is manual',
                   current_session=None if nana else session_path, last_test_session=session_path,
                   running_bin_sha256=None if nana else digest,
                   current_runtime_state='User Nana test completed; session closed for Shibuki test' if nana else
                       'Fresh swapped-costume build; native Ultimate flag1/armor0; user controls test',
                   previous_pointer=(destination / project / 'current_build.json').relative_to(ROOT).as_posix(),
                   next_action='Await any later user issue report' if nana else 'User tests jacket before capsule and swimsuit after acquisition')
        if not nana:
            cur['ultimate_native_command'] = session_path + '/ultimate_native_command.json'
        cfg.update(active_task='ultimate_costume_swap', active_substage=stage,
                   latest_integrated_build=build.relative_to(ROOT).as_posix(), latest_integrated_bin_sha256=digest,
                   ultimate_costume_policy='pre_capsule_jacket__acquired_swimsuit')
        pending[project] = cur, cfg
        summaries[project] = {'cue': cur['cue'], 'sha256': digest, 'user_checked': nana,
                              'test_session': session_path, 'stage': stage}
    destination.mkdir(exist_ok=True)
    for project in SOURCES:
        backup = destination / project
        require(not backup.exists(), 'Pointer backup already exists')
        backup.mkdir()
        for name in ('current_build.json', 'project.json'):
            shutil.copyfile(ROOT / 'projects' / project / name, backup / name)
    for project, (cur, cfg) in pending.items():
        write_json(ROOT / 'projects' / project / 'current_build.json', cur)
        write_json(ROOT / 'projects' / project / 'project.json', cfg)
    for path, expected in protected.items():
        require(file_hash(ROOT / path) == expected, 'Protected input changed during activation')
    write_json(destination / 'applied.json', {'passed': True, 'approval': '적용 부탁할게',
               'projects': summaries, 'protected_hashes': protected, 'F1_written': False, 'cards_written': False,
               'process_memory_written': False, 'automatic_sprite_runtime_verified': False,
               'user_test_handoff': True})
    print(json.dumps({'applied': summaries, 'protected_files': len(protected)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
