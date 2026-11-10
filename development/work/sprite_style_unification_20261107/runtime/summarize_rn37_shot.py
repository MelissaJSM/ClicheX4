from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;W=R.parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
rec=json.loads((R/'rn37_shot_play/evidence.json').read_text('utf8'))
review=json.loads((R/'rn37_shot_review01/manifest.json').read_text('utf8'))
assert rec['bin_sha256']=='8a7ee9c47d170c8869f5415e18dc23e920157e28e9d49d7762a7acebc416a01e'
files=[R/'rn37_shot_play/first.png',R/'rn37_shot_play/contact.png']+[Path(p['path'])for p in review['pages']]
assert len(files)==9
proof={'project':'ver_rin_nana','disc_sha256':rec['bin_sha256'],'source_asset_sha256':'8951948879773266cae0bebd408b411f4806b5652257bba3c50df0212b3c6e10','session':rec['session'],'fresh_boot':True,'copied_card_DATA3_loaded':True,'actual_window_recording':True,'captures':review['mapping']['recorded_frames'],'encoded_webp_frames':review['mapping']['encoded_frames'],'recording_plan':rec['plan'],'actually_viewed_files':[dict(bound(p),actually_viewed=True)for p in files],'findings':['실제 포스아머 일반 사격·차지샷·대기 복귀를 양방향으로 기록하고 시간 대응된7판 및 첫화면·흐름판을 직접 열람했다.','이번 표시에서 팔이 몸과 분리되거나 큰 크기 도약·추가 확정 잘림은 찾지 못했다.'],'limitations':['기록은 약16Hz 창 캡처이며 모든60Hz프레임이나 가려진 세부를 확인한 것은 아니다.','실행 참조별 RAM/GPU 대응은 이 녹화에서 수행하지 않았다. 기본형·부분아머는 정적 검사이며 이번 실기 결과로 확대하지 않는다.'],'evidence':[bound(R/n)for n in('rn37_ram_discovery.json','rn37_continue.json','rn37_load_fourth.json','rn37_hq.json','rn37_shot_play/evidence.json','rn37_shot_review01/manifest.json')],'protection':bound(W/'protection_checkpoint44.json'),'session_closed':True,'memory_written':False,'F1_F3_sent':False,'whole_project_complete':False}
dest=R/'rn37_shot_summary.json';assert not dest.exists();dest.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
