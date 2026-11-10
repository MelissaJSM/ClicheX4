"""Bind completed parent-run v15 evidence without editing frozen art or runtime files."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent;R=D/'rin_extension';W=ROOT/'work/sprite_style_unification_20261107'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sp=W/'runtime/rin_checkpoint15_summary.json'
assert sha(sp)=='06e6efc4dad4423090f140d592dc38647780abd27b26f6b2d3809f2e1bd485f1'
summary=read(sp)
assert summary['disc_sha256']=='66b808fc2f37a93eefd915ab7199934bbed62dcef4500ee087b75daa80324989'
bodypath=R/'prepared_burst_remaining02/PL01_U.ARC';body=bodypath.read_bytes()
assert sha(bodypath)=='1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9'
checked=[]
def binding(q):
    p=ROOT/q['path'];assert sha(p)==q['sha256'],p
    checked.append({'path':q['path'],'sha256':q['sha256']})
    return p
observer_rows=[];current_observed=set();pages=[]
for r in summary['runs']:
    binding(r['record'])
    for p in r['root_viewed_pages']:
        binding(p);assert p['root_actually_viewed'] is True;pages.append(p)
    if 'observer' not in r:continue
    watch=read(binding(r['observer']))
    assert watch['disc_sha256']==summary['disc_sha256'] and watch['watch_end_utc']
    asset=next(v for v in watch['resident_assets'] if v['archive']=='PL01_U.ARC')
    assert asset['archive_sha256']==sha(bodypath)
    for typ in (2,3,9):
        assert hashlib.sha256(entry(body,typ)).hexdigest()==asset['entries'][str(typ)]['sha256']
        assert watch['resident_assets_still_exact']['PL01_U.ARC'][str(typ)] is True
    assert watch['verified_bank_frames']==r['verified_bank_frames']
    assert [watch['events'][i]for i in watch['unverified_events']]==r['unverified_events']
    live={tuple(v)for v in watch['verified_bank_frames']};targets={tuple(v)for v in r['new_targets_verified']}
    assert targets<=live
    current_observed.update(f'b{b}_{n:03}'for b,n in live)
    observations=[]
    for b,n in sorted(targets):
        events=[e for e in watch['events']if e['bank']==b and e['frame']==n]
        passed=[e for e in events if e['verified']]
        assert passed
        observations.append({'ref':f'b{b}_{n:03}','verified_event_count':len(passed),'verified_facing_raw':sorted({e['facing_raw']for e in passed}),
                             'separate_unverified_events':[e for e in events if not e['verified']]})
    observer_rows.append({'name':r['name'],'watch':r['observer'],'resident_body_entries_exact':[2,3,9],
                          'targets':observations,'verified_unique_references':len(live),'unverified_events':r['unverified_events']})
assert sum(len(r['targets'])for r in observer_rows)==19
assert len(pages)==42
close=read(binding(summary['close']));assert close['exited'] is True
protect=read(binding(summary['protection']));assert protect['passed'] is True and protect['protected_files']==80 and protect['epsxe_process_count']==0
oldscope=read(R/'validation_scope303/runtime_scope.json')
old_unverified=set(oldscope['current_changed_since_all_historical_observations'])
assert len(old_unverified)==19 and old_unverified<=current_observed
own_names=('burst_0_00.png','burst_0_02.png','burst_0_04.png')
own_pages=[p for p in pages if Path(p['path']).name in own_names]
assert len(own_pages)==3
report={
    'scope':'부모 담당이 완료한 정상색 린 v15 실기 증거의 해시·상주자원·안정 관측 목록을 읽어 최신303 장부에 연결했다. 이 담당은 게임 입력/메모리 접근을 하지 않았다.',
    'summary':str(sp.relative_to(ROOT)),'summary_sha256':sha(sp),'disc_sha256':summary['disc_sha256'],'body_sha256':sha(bodypath),
    'fresh_boot':summary['fresh_boot'],'save_route':summary['save_route'],'run_counts':[{'name':r['name'],'captures':r['captures'],'root_viewed_sheets':len(r['root_viewed_pages'])}for r in summary['runs']],
    'observer_results':observer_rows,'current_observed_unique_references':sorted(current_observed),
    'previously_changed_19_now_have_current_stable_samples':sorted(old_unverified),
    'root_actual_visual_review_sheets':42,'this_agent_actual_visual_review_sheets':own_pages,
    'this_agent_visual_finding':'burst_0_00/02/04 실제창3판에서 구체 준비·낮은 발동·복귀 대기와 흰 부츠/파란 발등 역할을 확인했다. 이3판에 새 확정 절단은 찾지 못했다. 전체42판은 부모 담당의 실제 열람 기록이며 이 담당의 열람으로 대체하지 않는다.',
    'arrival':'319개 실제창과10판은 등장/대기 연결의 시각 근거다.247..253 개별 업로드를 관측한 기록이 없어7개 RAM/GPU 검증으로 세지 않는다.',
    'unverified_events_preserved':sum(len(r['unverified_events'])for r in observer_rows),
    'unverified_events_meaning':'질풍아 b0_155/164는 해당 사건 안정 표본0, b0_168 및 용염인 b1_148은 해당 사건 GPU불일치다. 다른 안정 성공 표본과 양립하며 전체 통과나 확정 게임 결함으로 치환하지 않는다.',
    'source_bindings_checked':checked,'normal_session_closed':True,'protection_report_passed':True,'protected_files':80,'test_card_pairs_reported':len(protect['test_cards']),
    'still_outside_scope':['레드 린 실기','차량/조종석 실제 가림','사다리 검격197/212','승리/회복 전체 실기','부분 VRAM42..49의 실제 선행 업로드','모든60Hz 프레임/전장면 회귀'],
    'all_character_runtime_complete':False,'user_accepted':False,'frozen_art_files_modified':False
}
out=R/'validation_scope303/runtime15_delta.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
ledger=read(R/'progress_ledger.json')
ledger['latest_actual_runtime']={'report':str(out.relative_to(ROOT)),'sha256':sha(out),'source':'부모 담당 실기 및 실제 캡처판 열람','normal_only':True,'latest_burst9_verified':True,'latest_ground_dash10_verified':True,'arrival_visual_only':True,'unverified_events':4,'all_runtime_complete':False}
ledger['current_runtime_scope']='validation_scope303/runtime15_delta.json'
ledger['previous_runtime_scope']='validation_scope303/runtime_scope.json'
ledger['next_page_scope']='현재303 정상색 낙봉파9·지상 질풍아10의 안정 실기 표본 확보. 레드·탑승·사다리·승리/회복 전체와4개 미확정 전환사건은 별도 남음. 추가 확정 미술 문제가 생기면 새 후속 경로로 수정한다.'
(R/'progress_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n','utf8')
(R/'progress_ledger303_runtime15_snapshot.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha(out),'checked_bindings':len(checked),'current_observed':len(current_observed),'root_viewed':42,'own_viewed':3,'unverified_events':report['unverified_events_preserved'],'cards':len(protect['test_cards'])}))
