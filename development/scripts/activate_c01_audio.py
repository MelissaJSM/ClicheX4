"""독립 검증된 C01 새 효과 BIN을 다음 실행 포인터로 연결한다."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import BASES, WORK, require
from scripts.project import working_cue
from src.psx_disc import file_hash

BUILD = 'c01_x6_sfx_20261105_v1'


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', 'utf8')


def main():
    independent = json.loads((WORK / 'independent.json').read_text('utf8'))
    require(independent['passed'], 'Independent review must pass')
    destination = WORK / 'application'
    require(not destination.exists(), 'Application already recorded')
    protection = {
        'MegaMan X4.bin': '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b',
        'Rockman X4.bin': 'a8fcc59d1d934c8601389bccc26f7a110b74f8fc025f1c73ebe63a46c547c9a1',
        'Rockman X5 (Japan).bin': '15b17f44fc461ae04c64c83b9b5b0c294e2eb16bed6c6ede9461c27743aa6323',
        'MegaManX6.bin': 'e0b5e6b6349bb0f0f487234f52cda43f26754a3d67764b7c306ba75c01e76e1f',
        'out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin': '8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a',
    }
    release = 'projects/ver_buki_riko/final_release.json'
    protection[release] = file_hash(ROOT / release)
    preserved = list(ROOT.glob('*.cue'))
    for emulator in (ROOT / 'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator',
                     ROOT / 'work/ver_rin_nana/emulator'):
        preserved.extend((emulator / 'memcards').glob('*.mcr'))
        preserved.extend((emulator / 'sstates').glob('SLUS_005.61.000*'))
    for path in preserved:
        if path.is_file():
            protection[path.relative_to(ROOT).as_posix()] = file_hash(path)
    for path, expected in protection.items():
        require(file_hash(ROOT / path) == expected, 'Protected input changed: ' + path)
    pending, summaries = {}, {}
    for project, (stem, old_sha) in BASES.items():
        folder, build = ROOT / 'projects' / project, ROOT / 'out' / project / BUILD
        cur = json.loads((folder / 'current_build.json').read_text('utf8'))
        cfg = json.loads((folder / 'project.json').read_text('utf8'))
        require(cur['sha256'] == old_sha and cfg['latest_integrated_bin_sha256'] == old_sha,
                'Current pointer changed during preparation')
        report = json.loads((build / 'manifest.json').read_text('utf8'))
        new_sha = report['modified_bin']['sha256']
        require(file_hash(build / (stem + '.bin')) == new_sha and report['parent_sha256'] == old_sha,
                'Wrong target image')
        require(independent['projects'][project]['bin_sha256'] == new_sha,
                'Independent verification belongs to another image')
        old_cue = ROOT / 'out' / project / 'selection_unified_20261105_v4' / (stem + '.cue')
        require((build / (stem + '.cue')).read_text('ascii') == working_cue(old_cue.read_text('ascii'), stem + '.bin'),
                'Target CUE differs from verified source track layout/reference')
        require(json.loads((build / 'post_review_verification.json').read_text('utf8'))['bin_sha256'] == new_sha,
                'Strict post-review sound identity check missing')
        cur.update(task='c01_nonvoice_sfx_revision', stage='C01_SFX_APPLIED_REVIEW',
                   build=build.relative_to(ROOT).as_posix(),
                   cue=(build / (stem + '.cue')).relative_to(ROOT).as_posix(), sha256=new_sha,
                   status_report='docs/C01_NONVOICE_SFX_REVISION.md',
                   c01_audio_report='docs/C01_NONVOICE_SFX_REVISION.md',
                   c01_audio_source='provided X6 SLPM_885.09; separate nonvoice hurt17/death14',
                   c01_audio_user_accepted=False, user_accepted=False,
                   current_runtime_state='Previous selection-v4 session, if running, preserved; new C01 requires fresh boot; active F1 unchanged',
                   runtime_verification_scope='Two full discs and native MIPS/SPU SDK checked in isolation; live sound listening pending',
                   previous_pointer=(destination / project / 'current_build.json').relative_to(ROOT).as_posix(),
                   next_action='fresh boot from new CUE and load memory card; verify damage/death without old F3 audio cache')
        cfg.update(active_task='c01_nonvoice_sfx_revision', active_substage='C01_SFX_APPLIED_REVIEW',
                   latest_integrated_build=build.relative_to(ROOT).as_posix(), latest_integrated_bin_sha256=new_sha)
        pending[project] = (cur, cfg)
        summaries[project] = {'cue': cur['cue'], 'sha256': new_sha}
    destination.mkdir()
    for project in BASES:
        backup = destination / project
        backup.mkdir()
        for name in ('current_build.json', 'project.json'):
            shutil.copyfile(ROOT / 'projects' / project / name, backup / name)
    for project, (cur, cfg) in pending.items():
        write(ROOT / 'projects' / project / 'current_build.json', cur)
        write(ROOT / 'projects' / project / 'project.json', cfg)
    for path, expected in protection.items():
        require(file_hash(ROOT / path) == expected, 'Protected input changed after activation')
    write(destination / 'applied.json', {'passed': True, 'projects': summaries, 'protected_hashes': protection,
          'F1_written': False, 'cards_written': False, 'emulator_input_sent': False,
          'live_session_restarted': False, 'user_accepted': False})
    print(json.dumps({'applied': summaries, 'live_session_preserved': True}))


if __name__ == '__main__':
    main()
