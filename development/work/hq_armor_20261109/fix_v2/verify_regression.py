"""Reproduce the reported task-table corruption with the captured RAM layout."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_cpu import run,H,WORKSPACE
from src.psx_player import decode_stream
reports=[]
for mode in ['ver_rin_nana','ver_buki_riko']:
 d=H/mode;c=(d/'compiled/container.bin').read_bytes();meta=json.loads((d/'compiled/container.json').read_text());cache={q['offset']:decode_stream(c,q['offset'],len(c),q['raw']).data for q in meta['chunks']}
 args=dict(special=1,armor=0,decoder_cache=cache,base=0x1b93c4,arena_tail=0x1a00,stack_top=0x801fef88)
 old=run(mode,legacy=True,**args);new=run(mode,**args)
 assert not old['scheduler_preserved'] and new['scheduler_preserved']
 q={'mode':mode,'v1_corruption_reproduced':True,'v2_task_table_preserved':True,'workspace':[hex(new['workspace']),hex(new['workspace_end'])],'stack_low':hex(new['stack_low']),'actual_gameplay_verified':False}
 if mode=='ver_rin_nana':
  crash=(H/'error_report/ram_1791e20.bin').read_bytes();head=crash[0x1f8000:0x1f8024].hex();assert old['scheduler_head_after']==head,(old['scheduler_head_after'],head)
  q.update(v1_corruption_matches_live_crash_all_9_callback_words=True,live_crash_callback_bytes=head)
 guards=[]
 for tail in [-96,0x18000]:
  result=run(mode,special=1,armor=0,decoder_cache=cache,arena_tail=tail)
  assert not result['uploads'] and result['scheduler_preserved']
  guards.append({'arena_tail':tail,'no_upload_or_task_table_write':True})
 q['invalid_arena_guards']=guards;reports.append(q);print(mode,'regression PASS',flush=True)
(H/'fix_v2/regression.json').write_text(json.dumps(reports,indent=2))
