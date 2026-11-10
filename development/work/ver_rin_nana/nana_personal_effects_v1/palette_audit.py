import sys,struct,json
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.prepare_nana_personal_effects import sources,entry
_,_,d=sources();p=entry(d['COL00_0X.ARC'],5)
for row in range(2,6):
 print(row,[[i,[(w>>s&31)*255//31 for s in(0,5,10)]] for i,w in enumerate(struct.unpack('<16H',p[row*32:(row+1)*32]))])
