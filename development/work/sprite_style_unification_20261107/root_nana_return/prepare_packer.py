from pathlib import Path
D=Path(__file__).resolve().parent;S=D.parent/'root_nana_victory'
s=(S/'pack_victory.py').read_text('utf8')
for a,b in [('victory-pose','return-pose'),('9599ca5fc21828df5ef4d865eafab4d27aa06a7b2391873a063c887120e70f91','90c614a7996d65ff71381ccc1f673cbfa13b84eccafec83c2e919010310b9239'),('(204,205,206,207)','(156,157,158)'),('across204/205/206/207','across156/157/158'),('packed_victory01','packed_return01'),('joint_targets01','joint_targets02'),("f'victory {n}'","f'return {n}'")]:
 assert a in s,a;s=s.replace(a,b)
p=D/'pack_return.py';assert not p.exists();p.write_text(s,'utf8')
