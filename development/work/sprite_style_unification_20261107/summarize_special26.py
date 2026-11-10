from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
cases=[];boards=[];targets={88,89,95,96,97,98,99}
for name in ('charge','cyclone','frost'):
 stem=f'nana_fourth_{name}26';e=read(R/(stem+'_watch')/'evidence.json');p=read(R/(stem+'_play')/'evidence.json');m=read(R/(stem+'_review')/'manifest.json')
 assert p['actual_window_recording'] and not p['simulated_video'] and not p['memory_written'] and not p['save_keys_sent'] and not p['error']
 dirs={str(n):sorted({q['facing_raw'] for q in e['events']if q['verified']and q['bank']==0 and q['frame']==n})for n in targets}
 views=[bound(Path(q['path']))for q in m['pages']];boards.extend(views)
 cases.append({'name':name,'frames':p['frames'],'target_observed_directions':{k:v for k,v in dirs.items()if v},'verified_bank_frames':e['verified_bank_frames'],'unverified_events':e['unverified_events'],'resident_assets_still_exact':e['resident_assets_still_exact'],'watch':bound(R/(stem+'_watch')/'evidence.json'),'recording':bound(R/(stem+'_play')/'evidence.json'),'actual_video':bound(R/(stem+'_play')/'play.webp'),'review_manifest':bound(R/(stem+'_review')/'manifest.json'),'root_actually_viewed_boards':views})
assert len(boards)==22
r={'disc':e['disc'],'disc_sha256':e['disc_sha256'],'session':e['session'],'form':'Nana full Fourth armor, both directions','resident_assets':e['resident_assets'],'cases':cases,'captured_windows':sum(q['frames']for q in cases),'root_actually_viewed_board_count':22,'findings':['차지샷88/89, 더블 사이클론97/98/99, 프로스트 타워95/96의 새 자세를 게임에서 관측했다.','검토한22개 실제 화면 비교판에서 추가 확정 몸체 분리나 크기 급변을 발견하지 못했다.'],'limits':['나나 포스아머 전파츠 상태의 제한된 동작 검증이다. 기본형/부분파츠/전체 캐릭터 전수 실기를 뜻하지 않는다.','차지 기록의 frame29 한 전환은 안정 표본이 없어 미검증이다. 이후 사이클론에서29 검증은 그 앞선 순간을 대신하지 않는다.','RN26의138/139는 이전 그림이다. RN27에서 추가한 새138/139의 실제 검증 근거가 아니다.','815개 캡처 전체를 직접 열람한 것은 아니며22개 시간순 비교판을 직접 검토했다. 원래 무기 이펙트가 몸을 가리는 프레임이 있다.'],'protection_before':bound(W/'protection_checkpoint35.json'),'protection_after':bound(W/'protection_checkpoint36.json'),'original_save_keys_sent':False,'process_memory_written':False,'session_closed':True,'whole_project_complete':False,'final_user_accepted':False}
assert r['captured_windows']==815
out=R/'nana_fourth_special26_summary.json';assert not out.exists();out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
cp=W/'root_review_checkpoint120.json';assert not cp.exists();cp.write_text(json.dumps({'reviewer':'root','kind':'actual game window chronological crop boards','summary':bound(out),'actually_viewed':boards,'finding':r['findings'],'limits':r['limits']},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'summary_sha256':sha(out),'root_review_sha256':sha(cp),'windows':815,'reviewed_boards':22}))
