from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;W=R.parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
rec=json.loads((R/'rn39_selection_play/evidence.json').read_text('utf8'));view=json.loads((R/'rn39_selection_review01/manifest.json').read_text('utf8'))
assert rec['bin_sha256']=='8eb84afaa7c201dfcaee8e5cbf4c2fef152d423b10b501e8238362f9b5cca5b2'
pics=[R/'rn39_selection_play/contact.png']+[Path(x['path'])for x in view['pages']];assert len(pics)==4
r={'project':'ver_rin_nana','disc_sha256':rec['bin_sha256'],'source_asset_sha256':'55b5d04d9a3452f2f12fe5ab21024de58c61f43eaa8b078f873ce4c7d2182f52','session':rec['session'],'fresh_boot':True,'recorded_captures':240,'encoded_webp_frames':237,'actually_viewed_files':[dict(bound(p),actually_viewed=True)for p in pics],'observations':['선택 화면에서 나나의 자동 차지사격·반동·복귀를 실제 시간대응3판과 흐름판으로 열람했다.','이번 화면에서 추가 확정 절단·큰 크기 도약은 찾지 못했다.'],'limits':['선택1..8 각각의 실행참조/GPU추적을 수행하지 않았으며 모든60Hz프레임을 본 결과는 아니다.','게임 내 호버 검증은 별도다.'],'evidence':[bound(R/p)for p in('rn39_selection_ram.json','rn39_selection_open.json','rn39_selection_play/evidence.json','rn39_selection_review01/manifest.json')],'protection':bound(W/'protection_checkpoint46.json'),'session_closed':True,'memory_written':False,'F1_F3_sent':False,'whole_project_complete':False}
p=R/'rn39_selection_summary.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
