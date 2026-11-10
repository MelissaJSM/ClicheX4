"""검증된 통합본 포인터와 자원 갱신 F1을 적용한다. 출시 승인 기록은 변경하지 않는다."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work/overhaul_20261105'
BUILDS = {
    'ver_buki_riko': ('shibuki_riko', 'bcdc219a1fa90ed277eecdf7b28ac196489d3297f49914470bf45e0844db2171'),
    'ver_rin_nana': ('rin_nana', '1a2d97272bb0dde2395aa7f1daa9136dd247125456090ff519fe3c484e3be2e2'),
}

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def read(path):
    return json.loads(path.read_text('utf8'))

def write(path, data):
    temporary = path.with_suffix(path.suffix + '.overhaul.tmp')
    with temporary.open('x', encoding='utf8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)

def main():
    destination = WORK / 'application'
    if destination.exists():
        raise ValueError('Application receipt already exists; inspect before repeating')
    original = WORK / 'baseline/current_progress/SLUS_005.61.000'
    active = ROOT / 'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000'
    clone = WORK / 'audio/nana_user_progress_candidate04_final_v1/SLUS_005.61.000'
    source_sha = '736cdc2dc277767d2e4c8b935137bc9ad5ab07ff8074323e0b2f710070657719'
    clone_sha = '57977106f9bf2a8fae08834c94225fdcdf477d895e82256510e7a745f5259440'
    if digest(original) != source_sha or digest(active) != source_sha or digest(clone) != clone_sha:
        raise ValueError('User progress or final clone changed')
    # An actual F3 trial and independent live cache comparison must precede activation.
    trial = read(WORK / 'runtime/nana_final_checkpoint_trial/evidence.json')
    live = read(WORK / 'runtime/nana_final_checkpoint_trial/live_verification.json')
    if not trial['original_F1_restored'] or trial['clone_sha256'] != clone_sha or not live['passed']:
        raise ValueError('Final checkpoint runtime verification incomplete')
    prepared = []
    for project, (stem, expected) in BUILDS.items():
        build = ROOT / 'out' / project / 'overhaul_20261105_candidate04'
        report = read(build / 'integration.json')
        if digest(build / (stem + '.bin')) != expected or report['modified_bin']['sha256'] != expected:
            raise ValueError('Final BIN changed')
        if not all(report[k] for k in ('all_changes_declared', 'edc_ecc_verified', 'resource_readback_verified', 'baseline_preserved')):
            raise ValueError('Integration verification incomplete')
        if (build / (stem + '.cue')).read_text('ascii').count(stem + '.bin') != 1:
            raise ValueError('CUE target differs')
        for name in ('project.json', 'current_build.json'):
            if digest(ROOT / 'projects' / project / name) != digest(WORK / 'baseline/pointers' / project / name):
                raise ValueError('Existing pointer changed: ' + project + '/' + name)
        settings = read(ROOT / 'projects' / project / 'project.json')
        settings.update(active_task='integration_overhaul', active_substage='ISSUES_PATCH_APPLIED_REVIEW',
            latest_integrated_build=build.relative_to(ROOT).as_posix(), latest_integrated_bin_sha256=expected,
            current_build_pointer=f'projects/{project}/current_build.json',
            black_zero_policy='shared_bitmap_normal_character_palette_no_separate_design',
            ultimate_code_before_capsule_design='provided_jacketless_swimsuit_then_existing_jacket_after_capsule')
        pointer = dict(project=project, task='integration_overhaul', stage='ISSUES_PATCH_APPLIED_REVIEW',
            build=build.relative_to(ROOT).as_posix(), cue=(build / (stem + '.cue')).relative_to(ROOT).as_posix(),
            sha256=expected, baseline_build=report['parent'], baseline_sha256=report['parent_sha256'],
            gameplay_voice_muted=True, gameplay_voice_mode='protagonists_muted_boss_NPC_missing_voices_only',
            status_report='docs/OVERHAUL_STATUS.md', art_review='docs/OVERHAUL_ART_REVIEW.md',
            runtime_verification_scope='See per-issue evidence; representative tests, not every animation or whole story',
            user_accepted=False, accepted_baseline_preserved=True,
            previous_pointer=f'work/overhaul_20261105/baseline/pointers/{project}/current_build.json')
        if project == 'ver_rin_nana':
            pointer.update(active_checkpoint=active.relative_to(ROOT).as_posix(), active_checkpoint_sha256=clone_sha,
                original_checkpoint=original.relative_to(ROOT).as_posix(), original_checkpoint_sha256=source_sha,
                progress_preserved=True)
        prepared.append((project, settings, pointer))
    protected = read(WORK / 'baseline/preservation.json')
    fixed = [v for v in protected if '/sstates/' not in v['path']]
    if any(digest(ROOT / v['path']) != v['sha256'] for v in fixed):
        raise ValueError('Protected input changed before activation')
    destination.mkdir()
    shutil.copyfile(active, destination / 'nana_before_application.000')
    shutil.copyfile(clone, active)
    if digest(active) != clone_sha:
        shutil.copyfile(original, active)
        raise ValueError('Final checkpoint installation failed')
    for project, settings, pointer in prepared:
        write(ROOT / 'projects' / project / 'project.json', settings)
        write(ROOT / 'projects' / project / 'current_build.json', pointer)
    receipt = dict(builds={p:s for p,(_,s) in BUILDS.items()}, checkpoint_before=source_sha,
        checkpoint_after=clone_sha, source_progress_backup=original.relative_to(ROOT).as_posix(),
        cards_written=False, original_games_written=False, final_release_v1_0_0_written=False,
        user_acceptance_claimed=False, fixed_inputs_verified_before_write=len(fixed))
    write(destination / 'receipt.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False))

if __name__ == '__main__':
    main()
