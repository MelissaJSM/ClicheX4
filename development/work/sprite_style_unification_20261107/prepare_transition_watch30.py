from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;R=W/'runtime';ROOT=W.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=(R/'observe_rn30.py').read_text('utf8')
a="  if a.seconds:need(len(active)==1,'Start watch only after one authenticated active player archive is loaded')"
b="  if a.seconds:need(len(active)<=1,'Ambiguous active player archive')"
assert a in s;s=s.replace(a,b)
a="  while active and(time.monotonic()-start<a.seconds or attempt_cycles==0):"
b="""  # Stage-selection begins without a player resource. Authenticate the exact
  # newly loaded archive read-only before any frame check; never use old RAM.
  report['transition_initially_active']=bool(active)
  while not active and time.monotonic()-start<a.seconds:
   fresh=read(a.ram_base,2097152);found=identify(fresh,assets);active=[r for r in found if r[4]]
   need(len(active)<=1,'Ambiguous active player archive during load')
   if not active:time.sleep(.03)
  report['transition_asset_ready_seconds']=time.monotonic()-start if active else None
  if active:
   report['resident_assets']=[{'archive':n,'archive_sha256':sha(assets[n]),'entries':{str(t):{'ram_offset':addr[t],'size':len(es[t]),'sha256':sha(es[t])}for t in es},'active_banks':matched}for n,es,addr,cand,matched in found]
  while active and(time.monotonic()-start<a.seconds or attempt_cycles==0):"""
assert a in s;s=s.replace(a,b)
out=R/'observe_transition_rn30.py';assert not out.exists();out.write_text(s,'utf8')
s=(R/'play_watch_rn30.py').read_text('utf8').replace("'observe_rn30.py'","'observe_transition_rn30.py'")
out=R/'play_transition_rn30.py';assert not out.exists();out.write_text(s,'utf8')
p=R/'tools_binding_transition_rn30.json';assert not p.exists()
p.write_text(json.dumps({'disc_sha256':'2701578993e0e5db5f0c6285026622066a49d9d9e080b42270bc329f436a9a79','helpers':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in (R/'observe_transition_rn30.py',R/'play_transition_rn30.py')],'reason':'Wait for exact native archive loading from stage selection before frame checks; read-only memory. Prior strict watch rejected selection before sending game keys.','memory_written':False},indent=2)+'\n','utf8')
print('transition observer prepared')
