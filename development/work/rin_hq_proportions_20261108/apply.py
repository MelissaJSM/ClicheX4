from pathlib import Path
import json,sys,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from src.psx_disc import file_hash
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
build=json.loads((W/'build.json').read_text('utf8'));out=(ROOT/build['cue']).parent;manifest=json.loads((out/'manifest.json').read_text('utf8'));runtime=json.loads((W/'runtime_v2/verification.json').read_text('utf8'))
assert file_hash(out/'rin_nana.bin')==build['sha256']==manifest['modified_bin']['sha256']==runtime['bin_sha256']
assert {n for g in runtime['observed_appearances']for n in g['frames']}==set(range(13))
assert runtime['fresh_boot_from_memory_card'] and not runtime['process_memory_written'] and not runtime['F1_F3_used']
protected=json.loads((W/'protection_before.json').read_text('utf8'))['files'];before={n:file_hash(ROOT/n)for n in protected};assert all(before[n]==v['sha256']for n,v in protected.items())
pointer=ROOT/'projects/ver_rin_nana/current_build.json';backup=W/'current_build_before.json';assert not backup.exists();backup.write_bytes(pointer.read_bytes());current=json.loads(pointer.read_text('utf8'))
current.update({'task':'rin_hunter_proportions','stage':'RIN_HUNTER_PROPORTIONS_APPLIED_REVIEW','build':out.relative_to(ROOT).as_posix(),'cue':build['cue'],'sha256':build['sha256'],'status_report':'docs/RIN_HUNTER_PROPORTIONS_20261108.md','user_accepted':False,'previous_pointer':backup.relative_to(ROOT).as_posix(),'current_session':'work/ver_rin_nana/emulator_sessions/20261108T061320858449Z','running_bin_sha256':build['sha256'],'current_runtime_state':'회색 어깨/검은 프릴 수정본을 새 CUE로 부팅. 린 카드 사본을 읽어 HQ 대화 0..12 외형 일치 확인 후 대화 화면 유지. F1/F3 사용 없음.','next_action':'수정된 헌터베이스 체형·회색 어깨/검은 프릴 사용자 디자인 확인. 출격13은 조립 검증 완료, 실제 화면 일치 포착 미완료.','hunter_proportions_report':'docs/RIN_HUNTER_PROPORTIONS_20261108.md','hunter_static_verified_frames':list(range(14)),'hunter_runtime_verified_frames':list(range(13)),'hunter_departure_runtime_verified':False,'hunter_gray_shoulders_black_frill':True,'hunter_review':(out/'review/all14.png').relative_to(ROOT).as_posix(),'hunter_runtime_report':'work/rin_hq_proportions_20261108/runtime_v2/verification.json'})
current['last_test_session']=current['current_session'];current['art_review']='docs/RIN_HUNTER_PROPORTIONS_20261108.md'
write(pointer,current)
after={n:file_hash(ROOT/n)for n in protected};changed=[n for n in protected if before[n]!=after[n]];assert changed==['projects/ver_rin_nana/current_build.json']
cards={}
for n in('test0.mcr','test1.mcr'):
 f=ROOT/'work/ver_rin_nana/rin_hunter_proportions_20261108/cards'/n;h=file_hash(f);assert h=='b0a596dba2e0e6ba6cdaaf87a894990365f0a33ee2b8d6536f6a5eb2298d77f9';cards[f.relative_to(ROOT).as_posix()]=h
manifest.update({'runtime_verified':True,'runtime_scope':'fresh boot, full opaque-pixel matches for HQ frames0..12; departure13 static only','runtime_verified_frames':list(range(13)),'departure_runtime_verified':False,'runtime_report':'work/rin_hq_proportions_20261108/runtime_v2/verification.json','gray_shoulders_black_frill':True});write(out/'manifest.json',manifest)
report={'build':build,'protected_files_unchanged':len(protected)-len(changed),'intentional_pointer_changes':changed,'pointer_backup':str(backup.relative_to(ROOT)),'test_cards_unchanged':cards,'other_mode_pointer_preserved':True,'original_and_release_files_preserved':True,'runtime_scope':manifest['runtime_scope'],'session_left_open':current['current_session'],'user_accepted':False}
write(W/'application.json',report);write(out/'verification.json',report);print(json.dumps(report))
