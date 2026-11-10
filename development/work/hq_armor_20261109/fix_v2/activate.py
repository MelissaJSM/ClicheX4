"""Activate verified v2 loader fixes without touching emulator or saved progress."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime import ROOT, H
from src.psx_disc import file_hash

F = H / 'fix_v2'
def load(p): return json.loads(p.read_text('utf8'))
def save(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', 'utf8')

results = load(F/'builds.json')
protected = load(F/'protection_before.json')['files']
for n, q in protected.items(): assert file_hash(ROOT/n) == q['sha256'], n
updates = set()
for result in results:
    mode = result['mode']; cp = ROOT/'projects'/mode/'current_build.json'; pj = cp.with_name('project.json')
    old = load(cp); assert old == load(F/'baseline'/mode/'current_build.json')
    cue = ROOT/result['cue']; assert file_hash(cue.with_suffix('.bin')) == result['sha256']
    mf = load(cue.parent/'manifest.json')
    assert mf['only_resource12_loader_changed'] and mf['native_cpu']['native_task_tables_preserved']
    new = {**old, 'task': 'hq_armor_crash_fix_20261109', 'stage': 'HQ_LOADER_FIX_APPLIED_RUNTIME_PENDING',
           'build': cue.parent.relative_to(ROOT).as_posix(), 'cue': result['cue'], 'sha256': result['sha256'],
           'previous_pointer': (F/'baseline'/mode/'current_build.json').relative_to(ROOT).as_posix(),
           'status_report': 'docs/HQ_ARMOR_LOAD_CRASH_20261109.md',
           'hunter_armor_review': (cue.parent/'review/index.html').relative_to(ROOT).as_posix(),
           'hunter_armor_loader_fix_report': 'docs/HQ_ARMOR_LOAD_CRASH_20261109.md',
           'hunter_armor_runtime_verified': False, 'hunter_armor_user_accepted': False,
           'hunter_armor_loader_regression_passed': True, 'current_session': None, 'running_bin_sha256': None,
           'current_runtime_state': 'v1의 나나 얼티밋 획득 전 카드 불러오기 오류를 실메모리에서 확인. v2 수정본 준비, 에뮬레이터 조작 없음.',
           'runtime_verification_scope': '실제 손상된 호출 주소 9개를 v1에서 동일 재현. v2의 작업 관리 영역·1 KiB 스택·자원 보호, 상태19·보호15 및 경계 거부 검사 통과. v2 실제 게임 재실행은 미실행.',
           'next_action': 'v2 CUE로 새로 부팅한 뒤 게임 내 메모리카드에서 얼티밋 획득 전 나나 저장을 불러와 HQ 진입 확인.',
           'user_accepted': False}
    save(cp, new)
    meta = load(pj); meta.update(active_task=new['task'], active_substage=new['stage'], latest_integrated_build=new['build'],
                                latest_integrated_bin_sha256=new['sha256'], hunter_armor_loader_fix_report=new['status_report'])
    save(pj, meta); updates.update([cp.relative_to(ROOT).as_posix(), pj.relative_to(ROOT).as_posix()])
for n, q in protected.items():
    if n not in updates: assert file_hash(ROOT/n) == q['sha256'], n
save(F/'application.json', {'builds': results, 'protected_files_unchanged': len(protected)-len(updates),
                           'metadata_updates': [{'file': n, 'before': protected[n]['sha256'], 'after': file_hash(ROOT/n)} for n in sorted(updates)],
                           'originals_references_accepted_releases_saves_preserved': True,
                           'emulator_keys_sent': False, 'process_memory_written': False, 'actual_gameplay_verified': False})
print('Activated v2 for both modes. Protected files:', len(protected)-len(updates))
