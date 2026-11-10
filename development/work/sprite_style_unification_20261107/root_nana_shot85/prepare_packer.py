from pathlib import Path
D=Path(__file__).resolve().parent
s=(D.parent/'root_nana_return/pack_return.py').read_text('utf8')
for a,b in [('90c614a7996d65ff71381ccc1f673cbfa13b84eccafec83c2e919010310b9239','29f7b9a054ede30562bc4c3a88da96f70a909ad05262b3fd184c566e980454db'),('(156,157,158)','(85,86)'),('common across156/157/158','common across85/86'),('packed_return01','packed_shot01'),("default='joint_targets02'","default='joint_targets03'"),("f'return {n}'","f'shot {n}'")]:assert a in s,a;s=s.replace(a,b)
p=D/'pack_shot.py';assert not p.exists();p.write_text(s,'utf8')
