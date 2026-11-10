from pathlib import Path
import hashlib
D=Path(__file__).resolve().parent
for label in ('a','b'):
 source=D/f'art_{label}01/generated.png'
 if not source.exists():continue
 s=(D.parent/'root_nana_victory/register_a.py').read_text('utf8')
 for a,b in [('inputs_a01',f'inputs_{label}01'),('art_a01',f'art_{label}01'),('registered_a01',f'registered_{label}01'),('855aca5daa799c8377bec2ccb99e90e0a194877c1b5c7e4e52a17c6c5581ccc4',hashlib.sha256(source.read_bytes()).hexdigest()),('victory pose','ride chaser pose')]:
  assert a in s,a;s=s.replace(a,b)
 p=D/f'register_{label}.py'
 if p.exists():assert p.read_text('utf8')==s
 else:p.write_text(s,'utf8')
