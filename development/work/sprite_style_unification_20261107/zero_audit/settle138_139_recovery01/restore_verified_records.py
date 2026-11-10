"""동결 해시가 일치한 검증본만 복원하고 충돌 산출물은 별도 보존한다."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;D=R.parent;ROOT=D.parents[2]
OLD=D/'nana_base_settle2_independent01';NEW=D/'nana_base_settle87_92_independent01';S=NEW/'collision_snapshot'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
expected_report='bc5269ec1e23fb2823b254303da1a83b4b21724d33fa48c989c1e060d621489c'
expected_visual='f6c67b2270092bdd06ad7a5c23aa563296b6a5f72df39c813792f0eee5ae6951'
frozen=D.parent/'nana_audit/base_settle_repaint/packed_settle_candidate_v1/FROZEN.json'
assert sha(frozen)=='122e43d6fe8b57d03943834b7a4e153145fe5540846aab2550a729b070e73a34'
assert sha(R/'restored_report_candidate.json')==expected_report
assert sha(OLD/'visual_review.json')==expected_visual
for name in ('readback.png','partial.png'):
 assert sha(OLD/name)==sha(R/'reproduction01'/name)
reader=D/'verify_nana_base_settle2_independent.py'
assert reader.read_bytes()==(S/reader.name).read_bytes()
assert (OLD/'report.json').read_bytes()==(S/'report.json').read_bytes()
added=('visual.json','full_87.png','full_92.png','partial_87.png','partial_92.png')
for name in added:
 assert (OLD/name).resolve().parent==OLD.resolve()
 assert (OLD/name).read_bytes()==(S/name).read_bytes()
before={rel(p):sha(p) for p in [reader,OLD/'report.json',*(OLD/n for n in added)]}
# 정확히 일치한 보고서와 세션 원문으로 재구성한 reader만 복원한다.
reader.write_bytes((R/'recovered_reader.py.txt').read_bytes())
(OLD/'report.json').write_bytes((R/'restored_report_candidate.json').read_bytes())
for name in added:
 (OLD/name).unlink()
assert sha(OLD/'report.json')==expected_report
assert sha(OLD/'visual_review.json')==expected_visual
assert sha(frozen)=='122e43d6fe8b57d03943834b7a4e153145fe5540846aab2550a729b070e73a34'
assert sorted(p.name for p in OLD.iterdir())==['partial.png','readback.png','report.json','visual_review.json']
evidence={'restored':True,'cause':'87/92 신규 검수에서 기존 138/139 reader와 출력 폴더 이름을 재사용하여 두 파일을 덮어썼다.','recovery':'세션 FileChange 원문과 당시 삽입 명령으로 reader를 재구성했다. 별도 출력에서 재실행한 보고서가 기존 FROZEN 해시와 일치한 후 복원했다.','original_reader_source':'session_source_provenance.json','original_reader_ascii_lines_compared_with_historical_GetContent':158,'old_report_sha256':sha(OLD/'report.json'),'old_visual_sha256':sha(OLD/'visual_review.json'),'old_frozen_sha256':sha(frozen),'restored_reader_sha256':sha(reader),'reader_historical_byte_hash_available':False,'note':'reader 바이트 자체의 과거 잠금 해시는 없으며, 세션 원문/당시 ASCII 본문/동결 보고서 재현 일치로 출처를 입증한다.','before_restore':before,'collision_snapshot':rel(S),'new87_92_folder':rel(NEW),'old_images_byte_reproduced':{n:sha(OLD/n)for n in('readback.png','partial.png')},'original_art_arc_bin_frozen_files_modified':False,'deleted_only_new_collision_files_after_exact_backup':list(added)}
p=R/'restoration.json';assert not p.exists();p.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'restored':True,'report_sha256':sha(OLD/'report.json'),'restoration_sha256':sha(p)}))
