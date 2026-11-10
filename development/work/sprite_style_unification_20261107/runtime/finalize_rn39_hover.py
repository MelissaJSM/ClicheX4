from pathlib import Path
import json, hashlib
R=Path(__file__).resolve().parent
ROOT=R.parents[2]
def record(p):
    return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
paths=[R/'rn39_hover_shot_play/first.png',R/'rn39_hover_shot_play/contact.png',R/'rn39_hover_move_play/contact.png']
paths += [R/f'rn39_hover_shot_review01/stationary_shot_{i:02}.png' for i in range(2)]
paths += sorted((R/'rn39_hover_shot_review02').glob('*.png'))
paths += sorted((R/'rn39_hover_move_review01').glob('*.png'))
assert len(paths)==14
evidence=[R/n for n in ['rn39_hover_ram.json','rn39_load_ultimate.json','rn39_hq.json','rn39_hover_shot_play/evidence.json','rn39_hover_move_play/evidence.json','rn39_hover_shot_review01/manifest.json','rn39_hover_shot_review02/manifest.json','rn39_hover_move_review01/manifest.json']]
recs=[json.loads((R/f'rn39_hover_{n}_play/evidence.json').read_text('utf8')) for n in ['shot','move']]
assert sum(len(x['capture_times']) for x in recs)==336
assert all(x['bin_sha256']=='8eb84afaa7c201dfcaee8e5cbf4c2fef152d423b10b501e8238362f9b5cca5b2' for x in recs)
out=R/'rn39_hover_summary.json';assert not out.exists()
result={'project':'ver_rin_nana','disc_sha256':recs[0]['bin_sha256'],'source_asset_sha256':'e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff','session':recs[0]['session'],'fresh_boot':True,'recorded_captures':336,'recordings':[{'name':'shot','captures':144,'encoded':144},{'name':'move','captures':192,'encoded':192}],'actually_viewed_files':[dict(record(p),actually_viewed=True) for p in paths],'observations':['새 부팅과 복사 카드 DATA3에서 획득 후 Ultimate 호버를 일반 조작으로 실행했다.','전진·후진·정지 호버와 각각의 사격에서 손/총구 및 발/추진 불꽃의 추가 확정 분리·큰 크기 도약은 찾지 못했다.','원래 좁은 전후진 사격 크롭의 일부 손이 범위 밖이어서 넓은 review02로 다시 제작하고 4판 모두 열람했다.'],'limits':['약16Hz 실제 창 캡처이며 전체60Hz프레임 및 모든 효과 가림의 검증이 아니다.','이번 녹화에서는 실행 참조별 RAM/GPU 추적을 하지 않아 10참조 전부의 실기 커버리지로 세지 않는다.','move 계획의 마지막 네 번째 점프는 앞 호버가 끝나지 않은 상태라 별도 새 호버 성공으로 세지 않는다.','이 검사는 획득 후 Ultimate이며 기본/포스 호버와 모든 부분 조건의 실제 검증이 아니다.'],'evidence':[record(p) for p in evidence],'protection':record(R.parent/'protection_checkpoint47.json'),'session_closed':True,'memory_written':False,'F1_F3_sent':False,'whole_project_complete':False}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(record(out)))
