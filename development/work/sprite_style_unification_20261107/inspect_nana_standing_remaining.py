from pathlib import Path
import sys,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive,helper
D=W/'root_nana_standing';D.mkdir(exist_ok=False);p=W/'root_nana_special/packed_special02/PL00_U.ARC';assert hashlib.sha256(p.read_bytes()).hexdigest()=='f2a968791b3411642a64bec9eb384a7f4b6a6d4e45be928a17b39262676f3648';a=Archive(p.read_bytes())
for name,mask in(('base',0),('fourth',15)):
 helper.grid([(f'{name} {n}',[('idle',a.composite(0,mask)[0]),('current',a.composite(n,mask)[0]),('new special98',a.composite(98,mask)[0])])for n in(85,89,97)],D/f'{name}_review.png',6)
print('standing references prepared')
