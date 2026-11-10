"""87/92 고유 검수 경로와 입력을 잠그며 옛 138/139 reader 참조를 거부한다."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;D=R.parent;ROOT=D.parents[2];N=D/'nana_base_settle87_92_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
report=N/'report.json';visual=N/'visual.json';reader=D/'verify_nana_base_settle87_92_independent.py'
assert sha(report)=='ab899d91a95b290b8afa5bcd9fcf9afe4e278c40d6b9de15bcc3c8b2f675dcd6'
assert sha(visual)=='cf4c19def725b840184397c6ed47422ee2a7942bf9ed091b0ee02b16a76576be'
assert sha(reader)=='e622cab6717d2baefef99d700fad85d4e3587304e5c755788f16fea20b1231c2'
data=json.loads(report.read_text('utf8'));inputs=dict(data['inputs'])
dependencies=[reader,D/'verify_shibuki_ultimate_hurt13_independent.py',ROOT/'scripts/export_x_consistency.py',ROOT/'scripts/discover_inputs.py',ROOT/'src/psx_player.py']
for p in dependencies:inputs[rel(p)]=sha(p)
for p,h in inputs.items():assert sha(ROOT/p)==h,p
for p in (reader,report,visual):
 text=p.read_text('utf8');assert 'nana_base_settle2_independent01'not in text and 'verify_nana_base_settle2_independent.py'not in text
assert "O.mkdir(exist_ok=False)"in reader.read_text('utf8')
assert json.loads(visual.read_text('utf8'))['report_sha256']==sha(report)
assert (R/'new87_reproduced_report.json').read_bytes()==report.read_bytes()
old=D/'nana_base_settle2_independent01/report.json';assert sha(old)=='bc5269ec1e23fb2823b254303da1a83b4b21724d33fa48c989c1e060d621489c'
payload={'scope':'Nana 기본/포스 87/92 독립 검수 전용. 기존 138/139 검수와 별개다.','final_paths':True,'reader':{'path':rel(reader),'sha256':sha(reader),'existing_output_directory_rejected':True},'report':{'path':rel(report),'sha256':sha(report)},'visual':{'path':rel(visual),'sha256':sha(visual)},'input_files':inputs,'readback_sheets':data['readback_sheets'],'unique_reader_reproduction':{'report_byte_exact':True,'four_png_byte_exact':True,'output_only_rerouted_to_separate_scratch':True,'report_output_paths_normalized_back_to_unique_destination':True,'proof_report':rel(R/'new87_reproduced_report.json')},'old_138_139_reader_or_report_referenced_as_new_evidence':False,'collision_recovery':{'path':rel(R/'restoration.json'),'sha256':sha(R/'restoration.json'),'old_report_restored_sha256':sha(old)},'new_MIPS_executed':False,'runtime_verified':False,'overall_complete':False}
p=N/'READER_INPUT_LOCK.json';assert not p.exists();p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'input_files':len(inputs),'lock_sha256':sha(p),'reader_sha256':sha(reader),'report_sha256':sha(report),'visual_sha256':sha(visual)}))
