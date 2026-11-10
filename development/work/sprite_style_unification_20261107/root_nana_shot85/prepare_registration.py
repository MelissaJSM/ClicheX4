from pathlib import Path
import hashlib
D=Path(__file__).resolve().parent
s=(D.parent/'root_nana_vehicle/register_a.py').read_text('utf8')
for a,b in [('inputs_a01','inputs01'),('art_a01','art01'),('registered_a01','registered01'),('b7e0fd751a53ae2538d36554338a8be4597238a3103684d4c500fc811b0e7820',hashlib.sha256((D/'art01/generated.png').read_bytes()).hexdigest()),('ride chaser pose','standing shot')]:assert a in s,a;s=s.replace(a,b)
p=D/'register.py';assert not p.exists();p.write_text(s,'utf8')
