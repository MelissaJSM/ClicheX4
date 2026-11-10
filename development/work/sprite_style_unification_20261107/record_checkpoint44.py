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
H=W/'shibuki_audit';files=[H/f'hover_ultimate_body5_contacts01/body_comparison_{i:02}.png'for i in range(3)]+[H/f'hover_ultimate_shot_composed03/comparison_{i:02}.png'for i in range(3)]+[H/f'hover_ultimate_body5_contacts01/jet_{n}.png'for n in(221,223,225,227,229)]
write(W/'root_review_checkpoint158.json',{'checkpoint':158,'scope':'시부키 Ultimate 호버10 패킹 전 새 몸5·사격5·제트 정적판','actually_viewed_files':[stamp(p,True)for p in files],'observations':['대기 기준의 머릿결·얼굴·의상 명암이 종전보다 세밀하며 두 팔의 읽힘과 높은 손 자세를 확인했다.','중립 제트15위상판에서 추가 확정 큰 발/불꽃 분리는 찾지 못했다.','사격222의 어두운 총-손목 연결과228 굽힌 팔은 최종 밝은 바탕/재추출/탄환 합성판에서 추가 검토한다. 이 중간판으로 수용 완료를 주장하지 않는다.'],'native_arc_review':False,'runtime_verified':False,'whole_project_complete':False})
R=W/'runtime';prev=json.loads((R/'br29_nova_summary.json').read_text('utf8'))
prev.update(project='ver_rin_nana',bin_sha256='e751a82bc3d1e228d26389d911ca4b46efa12612dcea69b6c99fdeb3ba3ca637',source_asset_sha256='2822a9387a69119e6a3f6ba0f3cc830676280309b139494221940e0e9a005c59',session='work/ver_rin_nana/emulator_sessions/20261108T001155467574Z',encoded_frames=112)
del prev['copied_card_DATA3_acquired_ultimate'];prev['copied_card_DATA3_fourth']=True
files=[R/'rn43_stage_play/last.png',R/'rn43_attack_play/contact.png']+[R/f'rn43_attack_review01/{side}_nova_{i:02}.png'for side in('right','left')for i in range(2)]
prev['actually_viewed_files']=[stamp(p,True)for p in files]
prev['observations']=['새 부팅·복사 카드 DATA3 포스아머에서 오른쪽 노바 1회 발동을 확인했다.','준비·새 돌진 몸·효과·복귀가 관찰됐고 직접 본 표본에서 추가 확정 몸 절단이나 큰 크기 도약은 보이지 않았다.','3.5초 두 번째 입력에서는 노바가 발동하지 않았다. 왼쪽 발동 성공으로 세지 않으며 4.4초 폭발/푸른 외곽은 피격 장면으로 구분한다.']
prev['limits']=['약16Hz 창 캡처이며 60Hz 전수·참조별RAM/GPU 추적은 미실행이다.','오른쪽 포스아머 1회이며 기본/부분 아머 및 왼쪽 노바 실기 성공을 주장하지 않는다.','적 효과가 가린 신체 픽셀을 모두 관측한 것은 아니다.']
prev['evidence']=[stamp(R/p)for p in('rn43_attack_play/evidence.json','rn43_attack_review01/manifest.json','rn43_load_fourth.json','rn43_hq.json')];prev['protection']=stamp(W/'protection_checkpoint52.json')
write(R/'rn43_nova_summary.json',prev)
write(R/'rn43_arrival_summary.json',{'project':'ver_rin_nana','bin_sha256':prev['bin_sha256'],'session':prev['session'],'fresh_boot':True,'copied_card_DATA3_fourth':True,'recorded_captures':319,'encoded_frames':285,'actually_viewed_files':[stamp(R/'rn43_stage_play/contact.png',True)]+[stamp(R/f'rn43_arrival_review01/arrival_{i:02}.png',True)for i in range(3)],'observations':['READY→ビーム 이동→착지→등장 준비→포스 대기 연결을 확인했다.','140의 새 의상 섬광 자체는 이번 약16Hz 표본에서 직접 포착하지 못했다. 8.844초 준비 뒤 8.906초에는 포스 대기/잔여광선이다.','8.281초 구형 효과 속 실루엣은 다른 단계이며 새140 관측 근거로 바꿔 세지 않는다.'],'flash140_runtime_verified':False,'evidence':[stamp(R/'rn43_stage_play/evidence.json'),stamp(R/'rn43_arrival_review01/manifest.json')],'protection':prev['protection'],'session_closed':True,'memory_written':False,'F1_F3_sent':False,'whole_project_complete':False})
for p in(W/'root_review_checkpoint158.json',R/'rn43_nova_summary.json',R/'rn43_arrival_summary.json'):print(stamp(p))
