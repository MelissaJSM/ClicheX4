import gzip,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_checkpoint import refresh
from scripts.discover_inputs import psx_arc,sha256
from scripts.prepare_nana_idle_shot import write
src=ROOT/'work/ver_rin_nana/checkpoints/before_nana_hurt_20261030/current/SLUS_005.61.000';out=ROOT/'work/ver_rin_nana/checkpoints/nana_hurt_preview_20261030/SLUS_005.61.000'
state=gzip.decompress(src.read_bytes());old=(ROOT/'out/ver_rin_nana/nana_wall_20261029T224356693137Z/modified.arc').read_bytes();new=(ROOT/'out/ver_rin_nana/nana_hurt_20261029T225358832150Z/modified.arc').read_bytes();ram=442;result,report=refresh(state,old,new,ram);assert result==gzip.decompress(out.read_bytes());rows=[]
for case in ('wrong_character','non_idle','armor','wrong_active_buffer','palette_changed','parent_bank_changed'):
 s=bytearray(state);b=bytearray(new)
 if case=='wrong_character':s[ram+0x1418c8+2]=1
 elif case=='non_idle':s[ram+0x1418c8+0x17]=33
 elif case=='armor':s[ram+0x1418c8+0xa7]=1
 elif case=='wrong_active_buffer':s[ram+0x16dea8]^=1
 elif case=='parent_bank_changed':s[1543002+1000]^=1
 else:
  e=next(e for e in psx_arc(new)if int(e['type'],16)==9);b[e['offset']+2]^=1
 try:refresh(bytes(s),old,bytes(b),ram)
 except ValueError as e:rows.append({'case':case,'rejected':True,'reason':str(e)})
 else:raise AssertionError('Accepted '+case)
write(Path(__file__).parent/'checkpoint_checks.json',{'reproduction_equal':True,'original_source_sha256':sha256(src.read_bytes()),'changed_bytes':report['changed_bytes'],'checks':rows});print(json.dumps({'reproduced':True,'rejections':len(rows)}))
