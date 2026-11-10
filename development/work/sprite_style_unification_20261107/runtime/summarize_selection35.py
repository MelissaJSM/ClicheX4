from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
review=R/'rn35_selection_review01';m=read(review/'manifest.json');rec=read(R/'rn35_selection_play/evidence.json');resident=read(R/'rn35_selection_resident.json')
assert rec['error'] is None and not rec['memory_written'] and not rec['save_keys_sent'] and rec['keys_released']
assert m['mapping']['recorded_frames']==128 and m['mapping']['encoded_frames']==72 and m['mapping']['all_capture_intervals_contained']
files=[R/'rn35_selection_play/contact.png']+[Path(x['path'])for x in m['pages']]
assert len(files)==3
result={'disc_sha256':rec['bin_sha256'],'actual_window_recording':True,'capture_count':128,'encoded_frames':72,'input_plan':rec['plan'],'session':rec['session'],'session_closed':True,'resident_proof':resident,'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix()if p.is_absolute()else p.as_posix(),'sha256':sha(p),'actually_viewed':True}for p in files], 'findings':['실제 새 부팅 선택 화면에서 나나의 선택 확정·손을 올린 자세·귀환 윤곽·빛 상승·로딩 전환을 확인했다.','이번 캡처의 전환에서 확정된 몸체 절단이나 급격한 크기 도약을 찾지 못했다.'],'limitations':['참조 번호를 실행 중 추적하지 않았으므로 UI18~21 각각의 GPU 일치 검증으로 주장하지 않는다.','RAM에서 조립 항목0xa 전체 일치는 찾았으나 그래픽 항목0x10102 전체 일치는 찾지 못했다.','나나 게임 내 차량13·Ultimate특수4의 실제 발동 검사는 이번 녹화에 포함하지 않았다.'],'protection_checkpoint':{'path':(R.parent/'protection_checkpoint42.json').relative_to(ROOT).as_posix(),'sha256':sha(R.parent/'protection_checkpoint42.json')},'whole_project_complete':False}
p=R/'rn35_selection_summary.json';assert not p.exists();p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
