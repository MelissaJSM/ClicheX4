from pathlib import Path
D=Path(__file__).resolve().parent;S=D.parent/'root_nana_shot85'
s=(S/'pack_shot.py').read_text('utf8')
for a,b in [('29f7b9a054ede30562bc4c3a88da96f70a909ad05262b3fd184c566e980454db','d2566605170954eebfeb37938dbea8abb611ac265dae572fe8c4b6c2128ceb61'),('(85,86)','(87,92)'),('across85/86','across87/92'),('packed_shot01','packed_settle01'),('joint_targets03','joint_targets02')]:
 assert a in s,a;s=s.replace(a,b)
p=D/'pack_settle.py';assert not p.exists();p.write_text(s,'utf8')
