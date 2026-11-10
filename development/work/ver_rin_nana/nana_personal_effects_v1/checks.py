import json,sys,shutil
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.prepare_nana_personal_effects import ART,sources,player,head_from_accepted,clone_effect,preserve_rin_death,entry,replace_entry,all_compositions
from scripts.build_nana_personal_effects import validate
_,_,old=sources();raw=old['PL00_U.ARC'];head=head_from_accepted(raw);passed=[]
def rejects(name,f):
 try:f()
 except ValueError:passed.append(name);return
 raise AssertionError('Unsafe candidate accepted: '+name)
rejects('wrong_head_size',lambda:player(raw,head[:15]))
rejects('head_index_overflow',lambda:player(raw,np.full((16,16),16,np.uint8)))
rejects('head_float',lambda:player(raw,head.astype(float)))
rejects('effect_changes_transparency',lambda:clone_effect(raw,{(1,105)},bytes([1]*16)))
parts=bytearray(entry(old['PL01_U.ARC'],3));off=all_compositions(parts)[1,105]['parts'][0]['record_offset'];parts[off]&=~12
rejects('rin_wrong_source_clut',lambda:preserve_rin_death(replace_entry(old['PL01_U.ARC'],3,bytes(parts))))
rejects('same_reproduction',lambda:validate(ART/'native02',ART/'native02'))
for label,file,offset in [('exe_extra_byte','SLUS_005.61',0x100),('other_stage_row','COL00_0X.ARC',2500)]:
 pair=ART/('negative_'+label);pair.mkdir()
 for side in ('a','b'):
  dst=pair/side;shutil.copytree(ART/'native02',dst);p=dst/file;b=bytearray(p.read_bytes());b[offset]^=1;p.write_bytes(b)
 rejects(label,lambda:validate(pair/'a',pair/'b'))
validate(ART/'native02',ART/'repro02')
(ART/'checks.json').write_text(json.dumps({'negative_cases':passed,'count':len(passed),'valid_candidate_passed':True},indent=2)+'\n','utf8');print(passed)
