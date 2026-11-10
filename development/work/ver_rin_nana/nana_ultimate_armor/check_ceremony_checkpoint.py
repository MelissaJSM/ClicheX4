import json,sys,gzip
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R))
from scripts.prepare_nana_fourth_checkpoint import refresh
from scripts.prepare_nana_ultimate_ceremony_reference import PARENT
D=R/'work/ver_rin_nana/nana_ultimate_armor';s=json.loads((D/'ceremony_saved_progress.json').read_text('utf8'));b=json.loads((D/'ceremony_build.json').read_text('utf8'));data=gzip.decompress((R/s['source']).read_bytes());old=(PARENT/'PL02_U.ARC').read_bytes();new=(R/b['build']/'PL02_U.ARC').read_bytes();report=json.loads((R/'work/ver_rin_nana/checkpoints/nana_ultimate_ceremony_v1/refresh.json').read_text('utf8'));pos=report['ram_offset']+0x1418c8;cases=[]
for name,off,value,enabled in [('explicit_support_required',None,None,False),('wrong_animation',0x17,30,True),('wrong_frame',0x47,146,True),('not_full_armor',0xa7,0,True),('dead_player',0x5c,0,True)]:
 test=bytearray(data)
 if off is not None:test[pos+off]=value
 try:refresh(bytes(test),old,new,allow_unchanged_ladder=enabled)
 except ValueError as error:cases.append(dict(case=name,rejected=True,reason=str(error)))
 else:raise AssertionError('Unsupported state accepted: '+name)
(D/'ceremony_checkpoint_negative_checks.json').write_text(json.dumps(cases,indent=2),encoding='utf8');print(json.dumps(cases))
