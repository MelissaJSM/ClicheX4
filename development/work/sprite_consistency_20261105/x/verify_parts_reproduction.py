import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.fix_nana_consistency_parts import *
project,stem,expected=SOURCES['nana'];source=ROOT/f'out/{project}/ultimate_costumes_swapped_20261105_v1/{stem}.bin';need(digest(source)==expected,'source hash')
with source.open('rb') as f:
 d=DiscReader(f,source.stat().st_size);rr={q['name'].split(';')[0]:q for q in d.inspect()['files']};data={n:d.read(rr[n]['lba'],rr[n]['size']) for n in SOURCE_ASSETS}
rejected=[]
for name in SOURCE_ASSETS:
 bad=dict(data);bad[name]=bytes([bad[name][0]^1])+bad[name][1:]
 try:
  if name=='PL00_U.ARC':patch_player(bad[name])
  else:patch_save(bad['MOJIPAT.ARC'],bad['LOAD_U.ARC'],bad['SLUS_005.61'])
 except ValueError:rejected.append(name)
 else:raise ValueError('Modified source accepted')
for name in ('PL00_U.ARC','MOJIPAT.ARC','LOAD_U.ARC'):
 bad=dict(data);bad[name]=(D/name).read_bytes()
 try:
  if name=='PL00_U.ARC':patch_player(bad[name])
  else:patch_save(bad['MOJIPAT.ARC'],bad['LOAD_U.ARC'],bad['SLUS_005.61'])
 except ValueError:rejected.append('already_patched_'+name)
 else:raise ValueError('Double patch accepted')
pl,checks=patch_player(data['PL00_U.ARC']);mo,lo,uichecks=patch_save(data['MOJIPAT.ARC'],data['LOAD_U.ARC'],data['SLUS_005.61']);reproduced={n:sha(v) for n,v in [('PL00_U.ARC',pl),('MOJIPAT.ARC',mo),('LOAD_U.ARC',lo)]}
for n,h in reproduced.items():need(h==sha((D/n).read_bytes()),'Reproduction mismatch')
write(D/'reproduction.json',{'passed':True,'reproduced_sha256':reproduced,'invalid_sources_rejected':rejected,'native_mask_checks':checks['rendered_mask_checks'],'save_mask_checks':uichecks['mask_checks'],'input_bin_unchanged':digest(source)==expected,'source_and_output_disjoint':True})
print('reproduction + 7 rejection tests passed')
