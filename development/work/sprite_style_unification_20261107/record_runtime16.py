from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bind=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,obj):
 assert not p.exists();p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n','utf8')
for name,checkpoint in [('shibuki_selection14',58),('red_rin15',59)]:
 play=R/(name+'_play');rec=read(play/'evidence.json');review=read(R/(name+'_review')/'manifest.json');session=ROOT/rec['session'];close=session/'close.local.json'
 assert read(close)['exited'] and not rec['error'] and rec['keys_released'] and not rec['memory_written'] and not rec['save_keys_sent']
 pages=[{**bind(ROOT/p['path']),'root_actually_viewed':True} for p in review['pages']]
 report={'disc_sha256':rec['bin_sha256'],'session':rec['session'],'fresh_boot':True,'recording':bind(play/'evidence.json'),'review':bind(R/(name+'_review')/'manifest.json'),'actual_captures':rec['frames'],'encoded_frames':review['encoded_frames'],'root_reviewed_pages':pages,'close':bind(close),'protection':bind(W/'protection_checkpoint24.json'),'final_user_accepted':False}
 if name=='shibuki_selection14':
  assert review['full_atlas_exact'] and review['atlas_bytes']==26624
  report['findings']=['선택 확정·복귀·빛기둥을128창/4비교판에서 직접 검토. 보라색 빛기둥은1.500~1.625초에 관측했으며 추가 확정 깨짐을 찾지 못했다.','X 선택 atlas26,624바이트가 실제VRAM의 byte x1280/y0/176행분할 배치와 전부 일치했다.']
  report['limits']=['개별23 조립 명령의 실행을 추적한 증거와 구분한다.','최초FMV 중 프레임버퍼 규격검사가 중단됐고, Start로 넘긴 후 재검사했다. 잘못 지정한 report.json 캐시는 파일 부재로 중단된 후 실제 새 검색으로 완료했다.']
 else:
  obs=read(R/(name+'_watch')/'evidence.json');cmd=read(session/'black_zero_native_command.json');assert cmd['activated']
  report.update(observer=bind(R/(name+'_watch')/'evidence.json'),native_black_command=bind(session/'black_zero_native_command.json'),verified_bank_frames=obs['verified_bank_frames'],unverified_events=[obs['events'][i] for i in obs['unverified_events']])
  report['findings']=['새 부팅의 원작 커맨드로 레드 린을 활성화했다. 세이브/F3를 사용하지 않았다.','인트로 대기·양방향 이동/점프·지상/공중베기·대시272창과14비교판을 직접 검토했다.64고유참조의 RAM/GPU 일치 표본을 확보했고 추가 확정 분리나 윤곽 깨짐을 찾지 못했다.']
  report['limits']=['특수기·차량·사다리·등장승리의 레드 전수 실기를 뜻하지 않는다.','62/223의 각 비동기 순간은 안정표본0으로 미확정이다.','약16fps 창 기록/비동기 관측은 전체60Hz 전환 전수검증과 다르다.']
 dest=R/(name+'_summary.json');write(dest,report)
 write(W/f'root_review_checkpoint{checkpoint}.json',{'summary':bind(dest),'root_actually_viewed_pages':pages,'findings':report['findings'],'limits':report['limits'],'final_user_accepted':False})
 print(json.dumps({'name':name,'sha256':sha(dest),'pages':len(pages)}))
