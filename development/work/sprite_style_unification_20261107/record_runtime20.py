"""Record only the actually reviewed RN18 base/Fourth hurt footage."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bind=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
proof=read(W/'protection_checkpoint28.json');assert proof['passed'] and proof['protected_files']==80
cards=read(ROOT/'work/ver_rin_nana/sprite_style_checkpoint16/cards/copies.json')
for c in cards:assert sha(ROOT/c['source'])==sha(ROOT/c['copy'])==c['sha256']
runs=[];pages=[]
for name,armor,targets,count in [('nana_base_hurt18_approach02',0,[106,110,111,112,113,114],5),('nana_base_hurt18_contact',0,list(range(106,110)),7),('nana_fourth_hurt18_approach',15,list(range(233,237)),12)]:
 obs=read(R/(name+'_watch')/'evidence.json');rec=read(R/(name+'_play')/'evidence.json');review=read(R/(name+'_hurt_review')/'manifest.json')
 assert rec['frames']==160 and rec['error'] is None and rec['keys_released'] and not rec['memory_written'] and not rec['save_keys_sent']
 assert obs['character']==0 and obs['ultimate_or_black']==0 and obs['player_armor']==armor and obs['weapon']==0
 assert all(obs['resident_assets_still_exact']['PL00_U.ARC'].values()) and not obs['unverified_events']
 assert all([0,n] in obs['verified_bank_frames'] for n in targets)
 assert len(review['pages'])==count
 normalized=[]
 for item in review['pages']:
  q=Path(item['path']);assert sha(q)==item['sha256'];normalized.append({**item,'path':q.relative_to(ROOT).as_posix()})
 session=ROOT/rec['session'];assert read(session/'close.local.json')['exited']
 runs.append({'name':name,'armor':armor,'actual_captures':rec['frames'],'encoded_webp_frames':review['encoded_webp_frames'],
 'fresh_boot':True,'session':rec['session'],'close':bind(session/'close.local.json'),'new_references_verified':targets,
 'verified_bank_frames':obs['verified_bank_frames'],'unverified_events':[],'watch':bind(R/(name+'_watch')/'evidence.json'),
 'record':bind(R/(name+'_play')/'evidence.json'),'review':bind(R/(name+'_hurt_review')/'manifest.json'),'root_actually_viewed':normalized})
 pages.extend(normalized)
new=sorted(set(n for run in runs for n in run['new_references_verified']));assert new==list(range(106,115))+list(range(233,237))
findings=['기본형 가벼운 피격33·강한 날림34, 포스 몸통아머 피격35를 실제 새 부팅에서 관측했다. 기본형106..114 및 포스233..236 모두 RAM/GPU 일치 표본을 확보했다.',
 '총480창·실제 피격 전후24판을 직접 열람했다. 새 머리결·옷 주름·발 형태가 대기/이동에 이어지며 추가 확정 몸체 분리·크기 변화는 찾지 못했다.',
 '포스의235/236 푸른 피격 효과도 새 몸체와 함께 실제로 표시됨을 확인했다. 기존 효과의 모양을 보존하며 충돌 성분만 국소 이동한 결과에서 추가 확정 잘림은 찾지 못했다.']
limits=['약16fps 창 기록과 비동기 RAM/GPU 관측이며 전체60Hz/모든 방향/부분아머 전조합/모든 피해원 실기를 뜻하지 않는다.',
 '기본형 강한 날림은 첫 병사 앞 폭발에서 발생했으나 정확한 피해원 객체ID는 추적하지 않았다. 가려진 부분은 정적 원화·공유층 검사와 함께 판단했다.',
 '포스106..114 및 기본233..236처럼 이 세션에서 실제로 발생하지 않은 다른 피해 유형·파츠 조합은 정적/원MIPS 검사 범위로만 남긴다.',
 '첫 기본형 접근 계획은3.8초 입력이 도구의3초 제한을 넘어서 입력 전 거부됐다. 제한을 유지한 짧은 입력 계획으로 다시 실행했고 실패 기록도 보존했다.',
 '기본형 첫 부팅 FMV의 다른 화면 크기는 캡처 규격 검사가 거부하여 원래 Start로 넘긴 뒤 재탐색했다.',
 '전체 캐릭터 미술 작업과 남은 재작화는 계속 진행 중이며 사용자 최종수용이 아니다.']
report={'project':'ver_rin_nana','test_build':'sprite_style_unification_20261107_v18',
 'disc_sha256':'0f40463b883e00a7e3acf268fd45052b905d0454440d8c5436ce24fe80f58c95',
 'asset_sha256':'978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f',
 'runs':runs,'new_references_verified_union':new,'root_visual_findings':findings,'limits':limits,
 'disc_and_native_checks':[bind(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v18/manifest.json'),bind(W/'staging_rn_v18_native_checks.json'),bind(W/'zero_audit/nana_hurt13_independent01/report.json')],
 'album':bind(ROOT/'out/sprite_style_unification_20261107/review_v19/manifest.json'),
 'browser_checks':bind(ROOT/'out/sprite_style_unification_20261107/review_v19/browser_checks.json'),
 'protection':bind(W/'protection_checkpoint28.json'),'additional_test_cards_unchanged':cards,
 'f1_f3_used':False,'process_memory_written':False,'active_build_pointers_changed':False,'all_character_runtime_complete':False,'final_user_accepted':False}
p=R/'nana_hurt18_summary.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
q=W/'root_review_checkpoint92.json';assert not q.exists();q.write_text(json.dumps({'root_actually_viewed':pages,'runtime_summary':bind(p),'findings':findings,'limits':limits,'final_user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'summary_sha256':sha(p),'root92_sha256':sha(q),'actual_captures':480,'root_reviewed_pages':len(pages)}))
