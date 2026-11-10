from pathlib import Path
import sys,json,hashlib
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sys.path.insert(0,str(W/'nana_audit/native_restore'));from preview_restore import helper
D=W/'root_nana_recoil';D.mkdir(exist_ok=True)
p=W/'root_nana_standing/packed_standing03/PL00_U.ARC';data=p.read_bytes();assert hashlib.sha256(data).hexdigest()=='87cc15efefedd475e0de972587995ad351d3ded1bd38a5c5096d5a3ab441748e';a=Archive(data)
for form,mask in (('base',0),('fourth',15)):
 out=D/f'{form}_review.png';assert not out.exists()
 helper.grid([(f'recoil {n}',[('idle',a.composite(0,mask)[0]),('standing85',a.composite(85,mask)[0]),('current',a.composite(n,mask)[0])]) for n in (86,90,91)],out,6)
print('comparison boards created without changing sources')
