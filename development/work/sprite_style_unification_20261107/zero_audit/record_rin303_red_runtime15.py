"""Bind the parent's red-Rin live evidence without changing frozen art."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent;R=D/'rin_extension';W=ROOT/'work/sprite_style_unification_20261107'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sp=W/'runtime/red_rin15_summary.json'
assert sha(sp)=='2ed1302cf8e1ccb41b0714eebc6ebbb3f7f7336f2a8267d366e16e373065f4b0'
s=read(sp);checked=[]
def bind(q):
    p=ROOT/q['path'];assert sha(p)==q['sha256'];checked.append(q);return p
for k in ('recording','review','native_black_command'):bind(s[k])
for p in s['root_reviewed_pages']:bind(p);assert p['root_actually_viewed']
w=read(bind(s['observer']));assert w['disc_sha256']==s['disc_sha256']=='66b808fc2f37a93eefd915ab7199934bbed62dcef4500ee087b75daa80324989'
arcpath=R/'prepared_burst_remaining02/PL01_U.ARC';arc=arcpath.read_bytes()
a=next(v for v in w['resident_assets'] if v['archive']=='PL01_U.ARC')
assert a['archive_sha256']==sha(arcpath)
for t in (2,3,9):
    assert hashlib.sha256(entry(arc,t)).hexdigest()==a['entries'][str(t)]['sha256']
    assert w['resident_assets_still_exact']['PL01_U.ARC'][str(t)]
assert w['verified_bank_frames']==s['verified_bank_frames'] and len(s['verified_bank_frames'])==64
assert [w['events'][i] for i in w['unverified_events']]==s['unverified_events']
assert len(s['unverified_events'])==2
assert all(e['stable_samples']==0 for e in s['unverified_events'])
assert read(bind(s['close']))['exited']
pro=read(bind(s['protection']));assert pro['passed'] and pro['protected_files']==80 and pro['epsxe_process_count']==0
out=R/'validation_scope303/red_runtime15_delta.json'
report={'passed':True,'scope':'부모 담당 새 부팅 레드 린 실기 기록의 해시와 현재 PL01 연결을 읽어 장부에 추가. 이 담당은 게임/캡처 새 실행·14판 추가 미술열람을 하지 않았다.',
 'summary':str(sp.relative_to(ROOT)),'summary_sha256':sha(sp),'disc_sha256':s['disc_sha256'],'pl01_sha256':sha(arcpath),
 'palette_variant':'red_black_zero','fresh_boot':s['fresh_boot'],'actual_captures':272,'root_viewed_sheets':14,'this_agent_viewed_new_live_sheets':0,
 'resident_entries_exact':[2,3,9],'verified_bank_frames':s['verified_bank_frames'],'verified_unique_refs':64,'unverified_events':s['unverified_events'],
 'limits':s['limits'],'source_bindings_checked':checked,'session_closed':True,'protected_files':80,'test_card_pairs':len(pro['test_cards']),
 'findings_attributed_to_root':s['findings'],'new_game_access':False,'frozen_files_modified':False,'all_runtime_complete':False,'user_accepted':False}
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
ledger=read(R/'progress_ledger.json')
ledger['latest_red_runtime']={'report':str(out.relative_to(ROOT)),'sha256':sha(out),'actual_captures':272,'unique_refs':64,'root_viewed_sheets':14,'unverified_events':2,'all_runtime_complete':False}
ledger['next_page_scope']='現在303 정상색 낙봉파9·지상 질풍아10과 레드 인트로64참조의 안정 표본 확보. 차량/조종석·사다리·승리/회복·레드 특수기 전수 및 정상4/레드2 미확정 전환사건은 별도 남음. 추가 확정 미술 문제가 생기면 새 후속 경로로 수정한다.'.replace('現在','현재')
for p in (R/'progress_ledger.json',R/'progress_ledger303_red_runtime15_snapshot.json'):
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha256':sha(out),'bindings':len(checked),'verified_refs':64,'unverified_events':2}))
