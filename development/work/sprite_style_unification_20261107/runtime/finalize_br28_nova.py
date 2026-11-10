from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
rec=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
e=json.loads((R/'br28_nova_play/evidence.json').read_text('utf8'));m=json.loads((R/'br28_nova_review01/manifest.json').read_text('utf8'))
assert e['bin_sha256']=='13d52f8be48ef29962dd78fc94f236897d216ef6c56f39406bb2bb67bbea5c77'
assert len(e['capture_times'])==m['mapping']['encoded_frames']==112
seen=[R/'br28_stage_play/last.png',R/'br28_nova_play/contact.png',*sorted((R/'br28_nova_review01').glob('*.png'))];assert len(seen)==6
session=ROOT/e['session'];assert json.loads((session/'close.local.json').read_text('utf8'))['exited']
r={'project':'ver_buki_riko','bin_sha256':e['bin_sha256'],'source_asset_sha256':'687fb27b10b9a7c13dd6d0c9fd6976dbb04f88f9b3b775f3d33482ebb7efb86f','session':e['session'],'fresh_boot':True,'copied_card_DATA3_acquired_ultimate':True,'recorded_captures':112,'encoded_frames':112,'actually_viewed_files':[dict(rec(f),actually_viewed=True)for f in seen],'observations':['새 부팅·복사 카드 DATA3의 획득후Ultimate에서 양방향 R2 노바를 발동했다.','새213..216 준비 자세와 돌진·복귀를 직접 확인했고 관찰 표본에서 새 확정 신체분리/큰크기도약을 찾지 못했다.','217..220 돌진/점멸 본체는 이 빌드에서 기존그림으로 남아 있다. 이 부분의 새상세와 획득후 의상은 제작 중이며 이번 통과범위에 포함하지 않는다.'],'limits':['약16Hz 창 캡처,60Hz전수와 참조별RAM/GPU 추적 미실행.','기본/포스 또는 획득전 의상 실기를 수행한 것이 아니다.','점멸·피격·적 효과가 가린 모든 신체픽셀 검증을 주장하지 않는다.'],'evidence':[rec(R/f)for f in['br28_stage_play/evidence.json','br28_nova_play/evidence.json','br28_nova_review01/manifest.json','br28_load_ultimate.json','br28_hq.json']],'protection':rec(R.parent/'protection_checkpoint49.json'),'session_closed':True,'memory_written':False,'F1_F3_sent':False,'whole_project_complete':False}
p=R/'br28_nova_summary.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rec(p)))
