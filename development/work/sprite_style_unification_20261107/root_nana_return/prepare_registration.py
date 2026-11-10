from pathlib import Path
D=Path(__file__).resolve().parent
s=(D.parent/'root_nana_victory/register_a.py').read_text('utf8')
for a,b in [('inputs_a01','inputs01'),('art_a01','art01'),('registered_a01','registered01'),('855aca5daa799c8377bec2ccb99e90e0a194877c1b5c7e4e52a17c6c5581ccc4','a666e247f3575ec0ee332356dcdb7b7c8a414c07bc60b1ad4d8930b4cde35cae'),('victory pose','return pose')]:
 assert a in s,a;s=s.replace(a,b)
p=D/'register.py';assert not p.exists();p.write_text(s,'utf8')
