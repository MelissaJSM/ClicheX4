from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parent;W=R.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
from scripts.prepare_riko_ui import entry
sha=lambda b:hashlib.sha256(b).hexdigest()
session=ROOT/'work/ver_rin_nana/emulator_sessions/20261107T202945604284Z';rec=json.loads((session/'session.local.json').read_text('utf8'));assert rec['pid']==61576 and rec['bin_sha256']=='d000e91019a02ec0fee18d6b6a76a2460cd886eb4fe3df7cefe8a51a9fb0c560'
p=ReadOnlyProcess(rec)
try:ram=p.read(17374752,0x200000)
finally:p.close()
ui=(W/'nana_selection_sync34_03/ST0E_U1.ARC').read_bytes();assert sha(ui)=='a577566919c4dad695950347151ce3a57af8c3247172b04c1f36c5ec6f7101b5'
rows=[]
for typ in (0x10102,10):
 data=entry(ui,typ);hits=[];start=0
 while True:
  at=ram.find(data,start)
  if at<0:break
  hits.append(hex(0x80000000+at));start=at+1
 rows.append({'entry_type':hex(typ),'size':len(data),'sha256':sha(data),'exact_resident_addresses':hits})
report={'session':session.relative_to(ROOT).as_posix(),'disc_sha256':rec['bin_sha256'],'candidate_ui_sha256':sha(ui),'entries':rows,'any_exact_resident_resource':any(q['exact_resident_addresses']for q in rows),'gpu_readback_verified':False,'memory_written':False,'save_keys_sent':False}
dest=R/'rn35_selection_resident.json';assert not dest.exists();dest.write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(rows))
