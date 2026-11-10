"""Record reviewed gameplay evidence; never promote a build or write a save."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

W = Path('work/sprite_style_unification_20261107')
R = W / 'runtime'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text('utf8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf8')


baseline = read(W / 'protection_before.json')['files']
now = {name: {'size': Path(name).stat().st_size, 'sha256': digest(name)} for name in baseline}
changed = [name for name in baseline if baseline[name] != now[name]]
write(W / 'protection_checkpoint11.json', {
    'passed': not changed, 'protected_files': len(baseline), 'mismatches': changed,
    'files': now, 'utc': datetime.now(timezone.utc).isoformat(),
})
if changed:
    raise RuntimeError('Protected inputs changed: ' + ', '.join(changed))

watches = [read(R / f'riko_allboss_watch{i:02d}/evidence.json') for i in (1, 2)]
records = [read(R / f'riko_allboss_play{i:02d}/evidence.json') for i in (1, 2)]
basic = read(R / 'riko_ground_watch01/evidence.json')
verified = set(tuple(ref) for watch in watches for ref in watch['verified_bank_frames'])
including_basic = verified | set(map(tuple, basic['verified_bank_frames']))
clips = []
for index, (watch, record) in enumerate(zip(watches, records), 1):
    assert record['error'] is None and record['keys_released']
    assert not record['memory_written'] and not record['save_keys_sent']
    assert watch['resident_assets_still_exact']
    anims = Counter(event['animation'] for event in watch['events'])
    failures = []
    for event_index in watch['unverified_events']:
        event = watch['events'][event_index]
        failures.append({
            'event_index': event_index,
            **{key: event[key] for key in ('bank', 'frame', 'animation', 'attempts', 'stable_samples', 'ram_mismatches', 'gpu_mismatches')},
            'same_reference_verified_elsewhere_in_all_three_clips': (event['bank'], event['frame']) in including_basic,
        })
    clips.append({
        'record': f'riko_allboss_play{index:02d}/evidence.json',
        'watch': f'riko_allboss_watch{index:02d}/evidence.json',
        'actual_window_frames': record['frames'],
        'verified_unique_references': len(watch['verified_bank_frames']),
        'observed_animations_event_counts': dict(sorted(anims.items())),
        'native_loop_counter': watch['native_main_loop_counter'],
        'unverified_transition_events': failures,
        'stage': watch['stage'], 'area': watch['area'], 'character': watch['character'],
        'resident_assets_still_exact': watch['resident_assets_still_exact'],
    })

manifest = read(R / 'riko_allboss_review_manifest.json')
assert len(manifest['pages']) == 18
# These 18 specific pages were actually opened and visually reviewed by root.
review = [{'path': page['path'], 'sha256': digest(page['path']), 'root_actually_viewed': True} for page in manifest['pages']]
report = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'disc_sha256': watches[0]['disc_sha256'],
    'disc_version': 'sprite_style_unification_20261107_v8',
    'riko_pl01_sha256': '026dd3d47ff05e7a7e9b6ef2330ab06d6be3c617586b6d3aa124a295aee74391',
    'same_riko_resource_in_v9': True,
    'session': records[0]['session'], 'pid': records[0]['pid'],
    'fresh_boot': True, 'save_load_route': 'In-game memory-card 1 DATA1, copied all-boss Riko save; no F3',
    'scene': 'Space Port, stage 10 area 0', 'clips': clips,
    'actual_window_frames': sum(row['actual_window_frames'] for row in clips),
    'verified_unique_references': len(verified), 'verified_bank_frames': sorted(verified),
    'including_earlier_basic_verified_unique_references': len(including_basic),
    'including_earlier_basic_actual_window_frames': sum(row['actual_window_frames'] for row in clips) + read(R / 'riko_ground_play01/evidence.json')['frames'],
    'root_actually_viewed': review,
    'findings': [
        '지상 1·2·3타, 공중 회전베기, 낙봉파, 뇌신격, 양방향 용염인과 종료/착지, 빙열참, 질풍아를 실제 입력으로 발생시키고 관측했다.',
        '실제 창 연속 캡처 18판에서 추가 확정 몸체/망토 분리, 외곽 깨짐 또는 대기 대비 갑작스러운 체형 축소를 찾지 못했다.',
        '용염인의 회전한 후면 자세와 검기 접점, 질풍아의 몸체와 잔상 연결, 낙봉파의 낮아진 자세에서 새 세부 묘사를 확인했다.',
    ],
    'input_corrections': [
        '첫 클립 R1/D 특수기 시도는 발동하지 않았다. 실제 이번 입력 설정의 특수기는 Triangle/V, 낙봉파는 R2/F였다.',
        '3연타는 약 0.2초 간격 입력으로 animation 88/89/90 발생을 확인했다. 앞선 기본 클립의 첫 타만 관측한 결과와 구분한다.',
    ],
    'limits': [
        '관측은 비동기 읽기다. 전환 중 실패 이벤트와 별도로 검증된 같은 참조를 구분했다. 0:170은 세 클립 어디서도 안정된 업로드 표본을 확보하지 못했다.',
        '창 캡처는 약 16fps이며 모든 60Hz 표시를 담지 못한다. 다른 시점과 이펙트에 가려진 픽셀의 전체 화면 일치를 주장하지 않는다.',
        '탑승·벽·등장/승리·블랙 및 다른 캐릭터의 전수 실기가 아니다. v9 전체 BIN의 실기 시험도 아니다.',
        '내부 미술 검토 결과이며 사용자 최종 수용이나 네 캐릭터 전체 완료가 아니다.',
    ],
    'session_closed_normally': True, 'f1_f3_used': False, 'process_memory_written': False,
    'active_build_pointers_changed': False,
    'protected_original_files_unchanged': True,
    'protection_report': (W / 'protection_checkpoint11.json').as_posix(),
    'user_accepted': False, 'all_character_runtime_complete': False,
}
write(R / 'riko_allboss_summary.json', report)
print(json.dumps({'protected': len(now), 'actual_frames': report['actual_window_frames'], 'verified_refs': len(verified), 'total_with_basic': len(including_basic), 'viewed_pages': len(review)}, ensure_ascii=False))
