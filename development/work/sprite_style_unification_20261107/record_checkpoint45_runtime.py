from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
def entry(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
names=['br30_stage_play/last.png','br30_hover_move_play/contact.png','br30_hover_shot_play/contact.png']
names += ['br30_hover_move_review01/'+n+'_00.png' for n in('forward_move','backward_move','stationary_hover')]
names += ['br30_hover_shot_review01/'+n+'_00.png' for n in('forward_shot','backward_shot','stationary_shot')]
names += ['br30_hover_shot_wide_review01/'+n+'_00.png' for n in('forward_shot','backward_shot')]
evidence=[R/(n+s) for n in('br30_hover_move','br30_hover_shot') for s in('_play/evidence.json','_review01/manifest.json')]
evidence += [R/'br30_hover_shot_wide_review01/manifest.json',R/'br30_load_ultimate.json',R/'br30_hq.json']
recs=[read(R/(n+'_play/evidence.json'))for n in('br30_hover_move','br30_hover_shot')]
assert all(r['frames']==144 and r['error'] is None and r['keys_released'] and not r['memory_written'] and not r['save_keys_sent'] for r in recs)
assert read(ROOT/'work/ver_buki_riko/emulator_sessions/20261108T003336758819Z/close.local.json')['exited']
assert read(W/'protection_checkpoint53.json')['passed']
data={'project':'ver_buki_riko','bin_sha256':'ccdf6058c2f105057dbb105c71988d683ffca604492b60c665e5f2eab2f69875','source_asset_sha256':'3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba','session':'work/ver_buki_riko/emulator_sessions/20261108T003336758819Z','fresh_boot':True,'recorded_captures':288,'encoded_frames':288,'actually_viewed_files':[dict(entry(R/n),actually_viewed=True)for n in names],'observations':['새 부팅·복사 카드 DATA3의 획득 후 Ultimate로 호버 전진/후진/정지와 사격을 확인했다.','직접 본 표본에서 발·추진 불꽃 접점과 어깨·팔·버스터가 연결되며 추가 확정 절단이나 큰 크기 도약은 보이지 않았다.','앞으로 이동하는 자세와 뒤로 이동하는 자세에서 원래 발사점 차이가 유지된다. 모든 관찰은 오른쪽을 바라보며 수행했다.','처음 좁은 사격 크롭의 가장자리에서 총구가 잘린 것은 크롭 범위였다. 넓은 두 판으로 확인했다.'],'limits':['약16Hz 창 캡처이며 60Hz 전수·참조별 RAM/GPU 추적은 미실행이다.','왼쪽을 바라보는 방향과 기본/포스 호버 실기는 이번 검증 범위가 아니다.','불꽃·발사 섬광이 가린 모든 픽셀을 관측한 것은 아니다.'],'evidence':[entry(p)for p in evidence],'protection':entry(W/'protection_checkpoint53.json'),'session_closed':True,'memory_written':False,'F1_F3_sent':False,'all_character_work_complete':False}
p=R/'br30_hover_summary.json';assert not p.exists();p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
