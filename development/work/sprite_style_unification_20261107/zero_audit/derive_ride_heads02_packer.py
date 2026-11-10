from pathlib import Path
p=Path(__file__).parent
s=(p/'pack_rin_ride_heads01.py').read_text('utf8')
s=s.replace("A=D/'ride_head_registered_v1';O=D/'prepared_ride_heads01'","A=D/'ride_head_registered_v3';O=D/'prepared_ride_heads02'")
s=s.replace('2283d7060f40e64730007807c86a166c0e40e5e072d6269ecffbf4945c2890b2','251194b9e4ab9f58983d41a1e81b3a1bd44978cff585e475c782c7e1764bfc7a')
s=s.replace("D/'ride_head01/generated.png'","D/'ride_head75_crown_fix02/generated.png'")
q=p/'pack_rin_ride_heads02.py';assert not q.exists();q.write_text(s,'utf8')
