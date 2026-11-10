"""Record RN17 Ultimate Rising actual play and its explicit limits."""
from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
proof=read(W/'protection_checkpoint26.json');assert proof['passed'] and proof['protected_files']==80
cards=read(ROOT/'work/ver_rin_nana/sprite_style_checkpoint16/cards/copies.json')
for c in cards:assert sha(ROOT/c['source'])==sha(ROOT/c['copy'])==c['sha256']
name='nana_ultimate_rising17';watch=read(R/(name+'_watch')/'evidence.json');record=read(R/(name+'_play')/'evidence.json')
review=read(R/(name+'_review')/'manifest.json');pages=review['pages'];expected=[100,101,102,103,104,231,232]
assert all([0,n] in watch['verified_bank_frames'] for n in expected)
assert not watch['unverified_events'] and record['frames']==351 and not record.get('error')
assert watch['weapon']==4 and watch['character']==0 and watch['ultimate_or_black']==1
assert all(watch['resident_assets_still_exact']['PL02_U.ARC'].values())
for q in pages:assert sha(ROOT/q['path'])==q['sha256']
assert len(pages)==12
report={'project':'ver_rin_nana','test_build':'sprite_style_unification_20261107_v17',
 'disc_sha256':'13da8bfc9cb6968028300ff362975826c1d6f08f3a009b623fa26fe529e5b124',
 'new_asset_sha256':'4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9',
 'session':record['session'],'fresh_boot':True,'save_load_route':'시험카드 사본 DATA3를 게임 메뉴에서 불러오기',
 'actual_captures':351,'encoded_frames':review['encoded_frames'],'verified_unique_references':len(watch['verified_bank_frames']),
 'new_references_verified':expected,'unverified_events':watch['unverified_events'],'root_viewed_pages':pages,
 'watch':bound(R/(name+'_watch')/'evidence.json'),'record':bound(R/(name+'_play')/'evidence.json'),
 'session_closed_normally':True,
 'root_visual_findings':['Ultimate 후폼의 지상/공중 일반 발사·차지 상승 양방향을 실제로 관측했다. 새 머리/팔/다리의 묘사와 대기 복귀에 추가 확정 절단은 찾지 못했다.'],
 'limits':['약16fps 실제 창 기록이며 모든60Hz 전환을 샘플링한 것은 아니다.',
           '획득 후 수영복 폼의 실기다. 재킷 폼·부분224조합 전체실기를 마친 것은 아니다.',
           '원래 불꽃이 캐릭터를 가리는 구간은 정적 원화/메모리 검사와 함께 판단했으며 원효과·판정·코드를 바꾸지 않았다.',
           '다른 동작과 네 캐릭터 전체 미술 작업은 계속 진행 중이다.'],
 'disc_and_native_checks':[bound(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v17/manifest.json'),bound(W/'staging_rn_v17_native_checks.json')],
 'album':bound(ROOT/'out/sprite_style_unification_20261107/review_v17/manifest.json'),
 'browser_checks':bound(ROOT/'out/sprite_style_unification_20261107/review_v17/browser_checks.json'),
 'protection':bound(W/'protection_checkpoint26.json'),'additional_test_cards_unchanged':cards,
 'f1_f3_used':False,'process_memory_written':False,'active_build_pointers_changed':False,
 'all_character_runtime_complete':False,'final_user_accepted':False}
p=R/'nana_ultimate_rising17_summary.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
r={'root_actually_viewed':pages,'runtime_summary':bound(p),'findings':report['root_visual_findings'],'limits':report['limits'],'final_user_accepted':False}
p=W/'root_review_checkpoint76.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'summary':sha(R/'nana_ultimate_rising17_summary.json'),'root76':sha(p),'actual_captures':351,'root_viewed_pages':12,'all_new_seven_observed':True}))
