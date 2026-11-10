from pathlib import Path
D=Path(__file__).resolve().parent;source=D.parent/'root_nana_ladder/pack_ladder.py'
t=source.read_text('utf8').replace('Pack new ladder art','Pack new low-HP art')
t=t.replace("str(H)]","str(H),str(W/'root_nana_ladder')]")
t=t.replace('978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f','509cc9785cb5eb3dca9f7a8a3fd1d3ea334887a98d3834b9f327266b3c6bbdce')
t=t.replace("tuple(range(143,156))+(183,)","tuple(range(120,126))")
t=t.replace("'target_layers_exact':70","'target_layers_exact':30")
t=t.replace("default='packed_ladder01'","default='packed_lowhp01'").replace("default='joint_layers02'","default='joint_layers03'")
t=t.replace("f'ladder{n}'","f'low HP {n}'")
p=D/'pack_lowhp.py';assert not p.exists();p.write_text(t,'utf8');print(p)
