from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;ROOT=R.parents[2];read=lambda p:json.loads(p.read_text('utf8'))
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
meta=[]
for name in('shot','move'):
 e=read(R/f'rn41_hover_{name}_play/evidence.json');m=read(R/f'rn41_hover_{name}_review01/manifest.json')
 assert e['bin_sha256']=='e765577ac65cff3348a76ab0d2719ea96471b2c7895a35ac5a3c428db87385b3';assert len(e['capture_times'])==m['mapping']['encoded_frames']==144
 meta.append({'name':name,'recorded_captures':144,'encoded_frames':144})
seen=[R/'rn41_stage_play/last.png',R/'rn41_hover_shot_play/contact.png',R/'rn41_hover_move_play/contact.png',*sorted((R/'rn41_hover_shot_review01').glob('*.png')),*sorted((R/'rn41_hover_move_review01').glob('*.png'))];assert len(seen)==12
session=ROOT/e['session'];assert read(session/'close.local.json')['exited']
proofs=[R/'rn41_load_fourth.json',R/'rn41_hq.json',R/'rn41_ram.json',R/'tools_binding_rn41.json',R/'rn41_stage_play/evidence.json']
proofs += [R/f'rn41_hover_{name}_{folder}/{file}'for name in('shot','move')for folder,file in[('play','evidence.json'),('review01','manifest.json')]]
r={'project':'ver_rin_nana','bin_sha256':e['bin_sha256'],'source_asset_sha256':'9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c','session':e['session'],'fresh_boot':True,'copied_card_DATA3_full_Fourth_authenticated':True,'recorded_captures':288,'recordings':meta,'actually_viewed_files':[dict(bound(p),actually_viewed=True)for p in seen],'observations':['오른쪽을 보는 포스아머에서 정지·전진·후진 호버와 사격을 일반키로 실행했다. 새 머리/베일/팔/다리 표시와 기존 점프/대기로의 전환을 확인했다.','직접 본 표본에서 새 확정 신체절단·권총/손 분리·발/불꽃 분리·큰 크기 도약을 찾지 못했다.','229/230의 굽힌 뒤신발 보완은 정지 호버·정지 호버 사격에서도 확인했다. 원래 파란 추진불꽃과 탄환/발사광을 유지한다.'],'limits':['약16Hz 창 캡처. 모든60Hz/모든10참조의RAM·GPU 업로드 추적을 수행한 것은 아니다.','전진/후진 모두 오른쪽을 본 시험이다. 왼쪽을 본 호버 및8부분아머 조합 전수 실기는 별도다.','최초20초 스테이지 진입318캡처는 호버288에 합산하지 않았다.'],'evidence':[bound(p)for p in proofs],'protection':bound(R.parent/'protection_checkpoint50.json'),'session_closed':True,'memory_written':False,'F1_F3_sent':False,'whole_project_complete':False}
p=R/'rn41_hover_summary.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(bound(p)))
