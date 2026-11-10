from pathlib import Path
W=Path(__file__).resolve().parent
t=(W/'review_nana_run14.py').read_text('utf8')
old="groups={'run_right':(.9,2.6),'run_left':(3.9,5.6),'fire_right':(6.9,8.6),'fire_left':(9.9,11.6),'dash_right':(12.9,14),'dash_left':(15.9,17.1)}"
assert old in t
t=t.replace(old,"groups={'charge_right':(3.8,5.2),'charge_left':(9.3,10.7)}")
p=W/'review_shibuki_aux15.py';assert not p.exists();p.write_text(t,'utf8')
