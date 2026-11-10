from pathlib import Path
import json, hashlib
from datetime import datetime, timezone

W = Path('work/sprite_style_unification_20261107')
R = W / 'runtime'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''): h.update(b)
    return h.hexdigest()
def write(p, obj):
    assert not p.exists(), str(p)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def evidence(p): return {'path':p.as_posix(), 'sha256':sha(p)}

protected = read(W/'protection_before.json')['files']
current = {p:{'size':Path(p).stat().st_size, 'sha256':sha(p)} for p in protected}
assert all(current[p] == protected[p] for p in protected)
cards = read('work/ver_rin_nana/sprite_style_checkpoint12/cards/copies.json')
for c in cards:
    assert sha(c['source']) == sha(c['copy']) == c['sha256']
write(W/'protection_checkpoint18.json', {'passed':True,'protected_files':len(current),'files':current,'test_cards':cards})

main = read(R/'nana_dash12_watch/evidence.json')
retry = read(R/'nana_dash12_left_retry_watch/evidence.json')
plays = [read(R/f'{n}_play/evidence.json') for n in ('nana_dash12','nana_dash12_left_retry')]
assert all(p['error'] is None and p['keys_released'] and not p['save_keys_sent'] and not p['memory_written'] for p in plays)
new = set(range(67,85)) | {93,94}
seen = {f for b,f in main['verified_bank_frames'] if b == 0}
assert new <= seen
samples72 = [e for e in retry['events'] if e['frame'] == 72]
assert all(e['verified'] and e['gpu_mismatches']==0 for e in samples72)
views = [evidence(p) | {'root_actually_viewed':True} for p in sorted((R/'nana_dash12_review').glob('*.png'))]
assert len(views)==12
summary = {
 'utc':datetime.now(timezone.utc).isoformat(),
 'disc_version':'sprite_style_unification_20261107_v12',
 'disc_sha256':main['disc_sha256'],
 'nana_pl02_sha256':main['resident_assets'][0]['archive_sha256'],
 'session':main['session'],'pid':main['pid'],'fresh_boot':True,
 'save_load_route':'시험카드 사본1 DATA3, 게임 내 불러오기',
 'costume':'Ultimate 캡슐 후 수영복',
 'actual_window_frames':[p['frames'] for p in plays],
 'verified_bank_frames':main['verified_bank_frames'],
 'all_new_dash20_verified':True,
 'main_unverified_events':main['unverified_events'],
 'retry_events':len(retry['events']),
 'retry_unverified_events':retry['unverified_events'],
 'retry_frame72_verified_events':len(samples72),
 'retry_frame72_stable_samples':sum(e['stable_samples'] for e in samples72),
 'retry_frame72_gpu_failures':sum(e['gpu_mismatches'] for e in samples72),
 'resident_assets_still_exact':retry['resident_assets_still_exact'],
 'root_actually_viewed':views,
 'raw_diagnostic_audit':evidence(W/'nana_audit/ultimate_dash_repaint/runtime72_review_v1/report.json'),
 'findings':[
  '지상/공중 대시·사격 양방향12캡처판을 직접 열람했다. 추가 확정 몸체분리·총구 깨짐은 발견하지 못했다.',
  '최초72 미검증 표본은 실패 raw를 저장하지 않아 원인을 확정하지 않는다. 재시도72는12표본 모두 일치했다.',
  '재시도의0/76 각1회 불일치는 독립 raw 대조에서 직전 프레임 전체 및 직전/목표 프레임 행 단위 혼합으로 확인했다. 각 event에는 정상 일치 표본도 있다.'
 ],
 'limits':[
  '이번 실제 검증은 Ultimate 후폼만 대상으로 하며 모든 의상과 모션의 전수 실기가 아니다.',
  '약16fps 창 캡처와 비동기 업로드 관측이며 모든60Hz 표시를 검사한 것은 아니다.',
  '최초 시험416장 중12비교판에 뽑힌 화면만 직접 열람했다. 재시도160장 전체를 직접 보았다고 보고하지 않는다.',
  '네 캐릭터의 전체 미술 통일과 최종 사용자 수용은 미완료다.'
 ],
 'session_closed_normally':True,'f1_f3_used':False,
 'process_memory_written':False,'active_build_pointers_changed':False,
 'protection_report':(W/'protection_checkpoint18.json').as_posix(),
 'user_accepted':False,'all_character_runtime_complete':False
}
write(R/'nana_checkpoint12_summary.json', summary)

rin=W/'zero_audit/rin_extension'
viewed=[rin/'bank1_special02_registered_v1'/n for n in ('normal_comparison.png','normal_effects_comparison.png')]
viewed += [rin/'prepared_bank1_special02'/f'{c}_readback_{i:02}.png' for c in ('normal','black') for i in range(2)]
viewed += [rin/'bank1_special236_review'/f'effects_normal_{i:02}.png' for i in range(3)]
viewed += [rin/'prepared_bank1_recovery128'/f'{c}_readback_00.png' for c in ('normal','black')]
viewed += [rin/'bank1_recovery240_review'/f'recovery_{c}_{i:02}.png' for c in ('normal','black') for i in range(2)]
write(W/'root_review_checkpoint32.json', {
 'utc':datetime.now(timezone.utc).isoformat(),
 'art_review_images':[evidence(p)|{'root_actually_viewed':True} for p in viewed],
 'findings':['린236의 새8참조 세부/색상과 효과접점,240의 회복4참조 및125→128→107→95 연결을 검토했다. 추가 확정 분리나크기 급변은 찾지 못했다.'],
 'limits':['검토15판은 정적 재추출/원시간표 오프라인 비교다. 실제 플레이 증거가 아니며 전체 완료를 뜻하지 않는다.'],
 'final_user_accepted':False
})
print(json.dumps({'protection':len(current),'runtime_frames':summary['actual_window_frames'],'review_images':len(viewed)}, ensure_ascii=False))
