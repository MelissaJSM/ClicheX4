from pathlib import Path
import json, hashlib
W=Path(__file__).resolve().parent; ROOT=W.parents[1]; R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
entry=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
session=ROOT/'work/ver_buki_riko/emulator_sessions/20261108T014333879732Z'
assert read(session/'close.local.json')['exited']
assert read(W/'protection_checkpoint55.json')['passed']
assert read(R/'br31_vehicle_load_fourth.json')['source_record_authenticated']
assert read(R/'br31_vehicle_resident01.json')['passed']
clips=[read(R/f'br31_vehicle{n:02}_play/evidence.json') for n in (1,2)]
assert [x['frames'] for x in clips]==[128,96]
assert all(x['error'] is None and x['keys_released'] and not x['memory_written'] and not x['save_keys_sent'] for x in clips)
assert all(read(R/f'br31_vehicle{n:02}_play/pause_boundary.json')['paused_after'] for n in (1,2))
folders=['br31_vehicle_review01','br31_vehicle_wide_review01','br31_vehicle_transition_review01']
manifests=[read(R/d/'manifest.json') for d in folders]
assert [x['mapping']['encoded_frames'] for x in manifests]==[126,126,96]
images=[R/'br31_direct86.png']+[R/f'br31_vehicle{n:02}_play/contact.png' for n in (1,2)]
images += [Path(page['path']) for m in manifests for page in m['pages']]
assert len(images)==17 and all(x.exists() for x in images)
navigation=[]
for n in range(1,87):
    p=R/f'br31_direct{n:02}.json'; a=read(p)
    assert a['paused_after'] and a['keys_released'] and not a['memory_written'] and not a['F1_F3_sent']
    navigation.append({'record':entry(p),'capture':entry(p.with_suffix('.png'))})
evidence=[R/f'br31_vehicle{n:02}_play/evidence.json' for n in (1,2)]
evidence += [R/d/'manifest.json' for d in folders]
evidence += [R/n for n in ('br31_vehicle_load_fourth.json','br31_vehicle_ram_discovery.json','br31_vehicle_resident01.json','br31_gate_probe01.json','br31_gate_probe02.json','br31_gate_play01/evidence.json','br31_gate_play02/evidence.json')]
data={
 'project':'ver_buki_riko','bin_sha256':clips[0]['bin_sha256'],
 'source_asset_sha256':'8b4cc387a59c5cc04b365bac7bc31cacfca79a02054e891e90049e2943b53397',
 'session':session.relative_to(ROOT).as_posix(),'fresh_boot':True,
 'recorded_vehicle_captures':224,'encoded_vehicle_frames':222,
 'actually_viewed_vehicle_files':[dict(entry(p),actually_viewed=True) for p in images],
 'observations':[
  '새 부팅·복사 카드 DATA3 포스아머로 마그마 드라군 구역1→2를 정상 조작하여 실제 라이드 아머에 탑승했다.',
  '왼쪽/오른쪽 방향 전환·짧은 이동·공격, 오른쪽 점프/공중공격/착지, 양방향 하차→재탑승 표본을 직접 확인했다.',
  '가려지지 않은 표본에서 작은 머리가 조종석과 함께 움직이며 추가 확정 부유·잘림·큰 크기 도약을 찾지 못했다.',
  '상주 PL00 그래픽/조립/팔레트 3항목 전체와 활성 포인터가 BR31과 일치했다. 스냅샷의 활성 프레임은188이었다.',
  '첫 비교판의 후반2구간은 카메라 높이 변화로 크롭이 머리를 잘랐다. 같은 녹화의 더 넓은2판으로 구분했고 가린 표본은 머리 검증 근거에서 제외한다.',
 ],
 'navigation_and_failed_attempts':[
  '앞선 일반 조작에서 피격/낙하 후 재시도가 있었다. 조작 실패를 스프라이트 결함이나 탑승 검증 성공으로 세지 않는다.',
  '구형 조작 도구의 메뉴 해제 후 캡처/저장 지연을 줄인 직접입력 도구를 만들었다. 연속 벽 점프는 실제 진행 중 버튼을 떼는 구간을 넣었다.',
  '구역1 끝 문은 원본 gate_core 구조와 일치하는 피격/파괴 상태를 가진다. 사격 높이를 맞춰 파괴한 뒤 구역2에 진입했다. 문 앞 정체는 해결되어 현재 차단 요인이 아니다.',
  '게이트 두 번째 녹화의 마지막 일시정지는 READY 중이라 실패했다. 이후 읽기 전용으로 구역2/일반 진행을 확인한 다음 별도로 일시정지했다.',
 ],
 'limits':[
  '약16Hz 창 녹화와 선택 구간 직접 검토이며 모든60Hz·19참조 전수의 RAM/GPU 추적은 아니다.',
  '이번 실제 탑승은 시부키 포스아머만이다. 기본/부분 아머·Ultimate 전후·다른 세 캐릭터의 이번 변경분 전체 탑승 실기를 대신하지 않는다.',
  '라이드 아머는 작은 머리만 외부로 보이는 구간이다. 라이드 체이서의 손잡이/발판과 전신 탑승 그림 검증을 대신하지 않는다.',
  '낙석·피격 섬광·펀치 효과에 가려진 모든 픽셀을 확인한 것은 아니다.',
 ],
 'navigation_records':navigation,'evidence':[entry(p) for p in evidence],
 'protection':entry(W/'protection_checkpoint55.json'),
 'session_closed':True,'memory_written':False,'F1_F3_sent':False,
 'game_art_or_bin_changed_this_validation':False,'all_character_work_complete':False,
}
p=R/'br31_vehicle_summary.json'; assert not p.exists()
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'summary':str(p),'sha256':sha(p),'captures':224,'viewed_files':17}))
