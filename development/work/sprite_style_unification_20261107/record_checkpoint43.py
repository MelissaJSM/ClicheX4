from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
def stamp(p,seen=False):
 p=Path(p);r={'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 if seen:r['actually_viewed']=True
 return r
def write(p,data):
 assert not p.exists(),p
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
D=W/'nana_audit/base_flash140_restore01';candidate=D/'packed_flash_candidate_v1/PL00_U.ARC'
assert stamp(candidate)['sha256']=='2822a9387a69119e6a3f6ba0f3cc830676280309b139494221940e0e9a005c59'
write(W/'root_review_checkpoint157.json',{
 'checkpoint':157,'candidate':stamp(candidate),
 'actually_viewed_files':[stamp(D/p,True)for p in('packed_flash_candidate_v1/readback.png','packed_flash_candidate_v1/partial.png','native_cycle_v1/timeline_2_landing.png')],
 'observations':['기본 섬광과 원래 양옆 광선은 유지되고 포스의 머리 베일과 의상 실루엣이 현재 대기에 맞게 추가된 것을 직접 확인했다.','부분 아머 여섯 조합과 원표 등장 착지 순서판을 확인했다. mask8 계열 뒤 베일 끝 분리는 현재 대기의 동일한 알파에도 존재하며 이번 수정으로 새로 생긴 것으로 세지 않는다.','추가 확정 섬광 외곽 누락·큰 크기 변화는 관찰하지 못했다.'],
 'decision':'최종 정적 후보 적합. 독립 검사 및 동결 결속 후 시험본 통합 가능.',
 'limits':['3판의 정적 열람이며 실제 게임의 3틱 섬광을 관측한 것은 아니다.','208..212는 귀환이 아니라 아머를 그리지 않는 소울보디 분신 소멸 상태다. 이번 변경 범위에서 보존한다.'],
 'runtime_verified':False,'whole_project_complete':False})
R=W/'runtime';prev=json.loads((R/'br28_nova_summary.json').read_text('utf8'))
prev.update(bin_sha256='753928a3cf2101caabf05cbe112217aa6d4b95b6320674632692831297a52252',source_asset_sha256='01997c949968d5a1a12d89e09c5eb46448bbcf245009feb9953e3d9e9356efd7',session='work/ver_buki_riko/emulator_sessions/20261107T235133479125Z',recorded_captures=112,encoded_frames=111)
for key in('actually_viewed_files','evidence'):
 prev[key]=[stamp(ROOT/item['path'].replace('br28','br29'),key=='actually_viewed_files')for item in prev[key]]
prev['protection']=stamp(W/'protection_checkpoint51.json')
prev['observations']=['새 부팅·복사 카드 DATA3 획득 후 Ultimate에서 양방향 노바의 준비·새 돌진 몸·점멸·복귀를 확인했다.','직접 본 6판에서는 추가 확정 손발/머리 절단이나 큰 크기 도약이 보이지 않았다.','0.875/1.0초 및 3.875..4.125초 새 몸과 실제 노바 효과색, 4.187초 효과와 이후 복귀를 구분했다.','1.88초의 어두운 적 원형 효과가 캐릭터를 가리는 장면은 이전 빌드에도 존재한다. 이것을 새 노바 결함이나 해당 픽셀의 검증 완료로 세지 않는다.','112캡처 중 동일한 이웃 그림이 합쳐져 WebP는 111프레임이다. 비교판은 실제 캡처시간에 대응한다.']
write(R/'br29_nova_summary.json',prev)
v=json.loads((ROOT/'out/sprite_style_unification_20261107/review_v34/browser_checks.json').read_text('utf8'))
assert v['passed']and len(v['modified_pixel_checks'])==2914 and len(v['full_loop_playback'])==4 and not v['errors']
for p in(W/'root_review_checkpoint157.json',R/'br29_nova_summary.json'):print(stamp(p))
print('album34: 2914 pixel checks, 4 loops, passed')
