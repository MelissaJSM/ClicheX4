"""Record completed RN16 live checks, without promoting either release pointer."""
from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def bound(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
proof=read(W/'protection_checkpoint25.json');assert proof['passed'] and proof['protected_files']==80
cards=read(ROOT/'work/ver_rin_nana/sprite_style_checkpoint16/cards/copies.json')
for c in cards:assert sha(ROOT/c['source'])==sha(ROOT/c['copy'])==c['sha256']
rows=[];pages=[]
for kind,expected,total in [('fourth',[100,101,102,103,104,231,232],352),('base',[103,104,231,232],176)]:
    name=f'nana_{kind}_rising16';watch=read(R/(name+'_watch')/'evidence.json');record=read(R/(name+'_play')/'evidence.json')
    review=read(R/(name+'_review')/'manifest.json');pages+=review['pages']
    assert all([0,n] in watch['verified_bank_frames'] for n in expected)
    assert not watch['unverified_events'] and record['frames']==total and not record.get('error')
    assert watch['weapon']==4 and watch['character']==0 and watch['ultimate_or_black']==0
    assert all(watch['resident_assets_still_exact']['PL00_U.ARC'].values())
    rows.append({'form':kind,'session':record['session'],'disc_sha256':record['bin_sha256'],
                 'actual_captures':total,'encoded_frames':review['encoded_frames'],
                 'verified_unique_references':len(watch['verified_bank_frames']),
                 'new_references_verified':expected,'unverified_events':watch['unverified_events'],
                 'root_viewed_pages':review['pages'],'watch':bound(R/(name+'_watch')/'evidence.json'),
                 'record':bound(R/(name+'_play')/'evidence.json'),'session_closed_normally':True})
for q in pages:assert sha(ROOT/q['path'])==q['sha256']
assert len(pages)==20
report={'project':'ver_rin_nana','test_build':'sprite_style_unification_20261107_v16',
 'disc_sha256':'c2972d3552214336316f0e2d85d96f8f66ac50b470a423dbba47cda994258e78',
 'new_asset_sha256':'3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42',
 'checks':rows,'root_visual_findings':['기본/포스 지상 및 공중 일반 발사의 양방향과 포스 차지 상승 양방향을 실제로 관측했다. 새 몸체의 머리·팔·다리 연결과 대기 복귀에 추가 확정 단절은 찾지 못했다.'],
 'limits':['약16fps 실제 창 기록이며 모든60Hz 전환을 샘플링한 것은 아니다.','부분 아머224조합은 정적 검증이며 전 조합 실기가 아니다.','원래 불꽃의 가림 구간은 원화/메모리 검사를 함께 보았으며 불꽃 이펙트·판정·코드를 변경하지 않았다.','다른 동작과 네 캐릭터 전체 미술 작업은 계속 진행 중이다.'],
 'disc_and_native_checks':[bound(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v16/manifest.json'),bound(W/'staging_rn_v16_native_checks.json')],
 'album':bound(ROOT/'out/sprite_style_unification_20261107/review_v16/manifest.json'),
 'browser_checks':bound(ROOT/'out/sprite_style_unification_20261107/review_v16/browser_checks.json'),
 'protection':bound(W/'protection_checkpoint25.json'),'additional_test_cards_unchanged':cards,
 'f1_f3_used':False,'process_memory_written':False,'active_build_pointers_changed':False,
 'all_character_runtime_complete':False,'final_user_accepted':False}
p=R/'nana_rising16_summary.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
r={'root_actually_viewed':pages,'runtime_summary':bound(p),'new_runtime_scope':rows,
   'findings':report['root_visual_findings'],'limits':report['limits'],'final_user_accepted':False}
p=W/'root_review_checkpoint68.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'summary':sha(R/'nana_rising16_summary.json'),'root68':sha(p),'actual_captures':528,'root_viewed_pages':20,'all_new_seven_observed':True}))
