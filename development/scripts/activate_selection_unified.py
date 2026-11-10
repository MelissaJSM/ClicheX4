"""검증한 선택 화면 v4를 두 프로젝트의 다음 실행 대상으로 연결한다."""
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.hud_frame_fix import require
WORK=ROOT/'work/selection_unify_20261105'
TARGETS={
 'ver_buki_riko':('shibuki_riko','92ab09adf0284c0581a6993c88f64b2348f4e2bdc886e4ca9df1e1bc8c2bdb50','15b6eec0ff23decff4f42133e20f0d0b33efed40c4ecf3f245905ef2a5357aea'),
 'ver_rin_nana':('rin_nana','2ed8c388fafe4122aee301bf932632f1fef4ca80fff9cb8c93ea93ffc99bc29f','8c5c7ba9bb2fd6d04080db453c2890c6446350fe19b896013661dc97b21b5bc1'),
}

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')

def main():
 proof=json.loads((WORK/'independent.json').read_text('utf8'))
 require(proof['passed'],'Independent verification required')
 snapshots={};new={}
 protection=json.loads((ROOT/'work/hud_frame_fix_20261105/shibuki_runtime_review/preservation_before.json').read_text('utf8'))
 expected={p:v['sha256']for p,v in protection.items()}
 expected.update({
  'MegaMan X4.bin':'3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b',
  'Rockman X4.bin':'a8fcc59d1d934c8601389bccc26f7a110b74f8fc025f1c73ebe63a46c547c9a1',
  'out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin':'8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a',
  'projects/ver_buki_riko/final_release.json':digest(ROOT/'projects/ver_buki_riko/final_release.json'),
 })
 def protect():
  for p,h in expected.items():require(digest(ROOT/p)==h,'Protected file changed: '+p)
 protect()
 destination=WORK/'application';require(not destination.exists(),'Already applied')
 for project,(stem,old,sha)in TARGETS.items():
  folder=ROOT/'projects'/project;build=ROOT/'out'/project/'selection_unified_20261105_v4'
  cur=json.loads((folder/'current_build.json').read_text('utf8'));cfg=json.loads((folder/'project.json').read_text('utf8'))
  require(cur['sha256']==old and cfg['latest_integrated_bin_sha256']==old,'Active pointer changed')
  require(proof['projects'][project]['BIN_sha256']==sha and digest(build/(stem+'.bin'))==sha,'Wrong verified build')
  require(json.loads((build/'manifest.json').read_text('utf8'))['modified_bin']['sha256']==sha,'Manifest differs')
  snapshots[project]=(cur,cfg)
  cur={**cur,'task':'selection_screen_unification','stage':'SELECTION_UI_REVIEW','build':build.relative_to(ROOT).as_posix(),
   'cue':(build/(stem+'.cue')).relative_to(ROOT).as_posix(),'sha256':sha,'user_accepted':False,
   'status_report':'docs/SELECTION_SCREEN_UNIFICATION.md','selection_ui_report':'docs/SELECTION_SCREEN_UNIFICATION.md',
   'art_review':'out/selection_screen_review_20261105','current_session':None,'running_bin_sha256':None,
   'current_runtime_state':'isolated_selection_verification_in_progress; main session not yet relaunched',
   'runtime_verification_scope':'independent static/disc checks complete; actual screenshots recorded separately',
   'previous_pointer':(destination/project/'current_build.json').relative_to(ROOT).as_posix()}
  if project=='ver_rin_nana':cur['rin_optical_alignment_report']='docs/RIN_HUD_OPTICAL_ALIGNMENT.md'
  cfg={**cfg,'active_task':'selection_screen_unification','active_substage':'SELECTION_UI_REVIEW',
   'latest_integrated_build':build.relative_to(ROOT).as_posix(),'latest_integrated_bin_sha256':sha}
  new[project]=(cur,cfg)
 destination.mkdir()
 for project in TARGETS:
  backup=destination/project;backup.mkdir()
  for name in ('current_build.json','project.json'):shutil.copyfile(ROOT/'projects'/project/name,backup/name)
 for project,(cur,cfg)in new.items():
  write(ROOT/'projects'/project/'current_build.json',cur);write(ROOT/'projects'/project/'project.json',cfg)
 protect()
 write(destination/'applied.json',{'passed':True,'projects':{p:sha for p,(_,_,sha)in TARGETS.items()},'protected_hashes':expected,
  'F1_written':False,'memory_cards_written':False,'main_emulator_started':False,'user_accepted':False})
 print(json.dumps({'applied':list(TARGETS),'protected_files':len(expected),'saved_progress_preserved':True}))

if __name__=='__main__':main()
