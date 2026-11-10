import sys,json
from pathlib import Path
sys.path.insert(0,'.')
from scripts.export_x_consistency import *
from scripts.fix_x_idle_return import patch_return_idle
from scripts.fix_shibuki_ladder_top import patch_ladder
from scripts.fix_shibuki_arrival_terminal import patch_terminal,INPUT_SHAS
D=TASK/'arrival141_history/prepared_v1';base=(TASK/'shibuki/PL00_U.ARC').read_bytes();tonepath=ROOT/'work/sprite_consistency_20261105/coverage/shibuki_special/prepared_v1/PL00_U.ARC';tone=tonepath.read_bytes();tonehash='f1c3ae2c4f11fec6275abd4e33205abf0ca350f37febcd53a35d6e4136e7c118';need(sha(tone)==tonehash,'tone frozen source')
linked,lp=patch_return_idle(tone,base,'shibuki','PL00_U.ARC',expected_input_sha=tonehash);ladder,dp=patch_ladder(linked,base,expected_input_sha=sha(linked));a,ap=patch_terminal(ladder,'PL00_U.ARC',expected_input_sha=INPUT_SHAS['PL00_U.ARC']);need(a==(D/'PL00_U.ARC').read_bytes(),'PL00 reproduction')
bas2=(TASK/'shibuki/PL02_U.ARC').read_bytes();link2,p=patch_return_idle(bas2,bas2,'shibuki','PL02_U.ARC');b,bp=patch_terminal(link2,'PL02_U.ARC',expected_input_sha=INPUT_SHAS['PL02_U.ARC']);need(b==(D/'PL02_U.ARC').read_bytes(),'PL02 reproduction')
checks=[]
def rejects(label,fn):
 try:fn()
 except ValueError:checks.append(label)
 else:raise ValueError('Rejected test accepted:'+label)
def corrupt(v):return bytes([v[0]^1])+v[1:]
rejects('link corrupt baseline',lambda:patch_return_idle(base,corrupt(base),'shibuki','PL00_U.ARC'))
rejects('link corrupt input',lambda:patch_return_idle(corrupt(tone),base,'shibuki','PL00_U.ARC',expected_input_sha=tonehash))
rejects('link double application',lambda:patch_return_idle(linked,base,'shibuki','PL00_U.ARC',expected_input_sha=sha(linked)))
rejects('ladder corrupt input',lambda:patch_ladder(corrupt(linked),base,expected_input_sha=sha(linked)))
rejects('ladder double application',lambda:patch_ladder(ladder,base,expected_input_sha=sha(ladder)))
for name,value,h in [('PL00_U.ARC',ladder,INPUT_SHAS['PL00_U.ARC']),('PL02_U.ARC',link2,INPUT_SHAS['PL02_U.ARC'])]:
 rejects('terminal wrong hash '+name,lambda n=name,v=value,h=h:patch_terminal(corrupt(v),n,expected_input_sha=h))
for name,value in [('PL00_U.ARC',a),('PL02_U.ARC',b)]:
 rejects('terminal double application '+name,lambda n=name,v=value:patch_terminal(v,n,expected_input_sha=INPUT_SHAS[n]))
write(D/'reproduction.json',{'passed':True,'outputs':{'PL00_U.ARC':sha(a),'PL02_U.ARC':sha(b)},'rejected_inputs':checks,'reproducible_from_fixed_tone_and_immutable_baseline':True,'sources_unchanged':sha(tonepath.read_bytes())==tonehash,'runtime_verified':False});print('reproduced final 2ARC; rejected',len(checks),'inputs')
