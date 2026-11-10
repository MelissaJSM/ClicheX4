"""수용 대기/1·2는 보존하고 새 이동/사격 3..32를 동시에 정확 패킹."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from native_pose_pack import SOURCE,SOURCE_SHA,sha,load,packing,write
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from src.psx_disc import file_hash
assert file_hash(SOURCE)==SOURCE_SHA
raw=read_disc(SOURCE,('PL02_U.ARC',))[0]['PL02_U.ARC'];before={};after={}
out=H/'prepared_run_complete03';out.mkdir(exist_ok=False)
for n in range(3,33):
 folder=H/('run_registered02'if n%2 else'shot_registered05')
 before[n]=load(folder/'before'/f'{n:03}_indices.png');after[n]=load(folder/'after'/f'{n:03}_indices.png')
result,proof=packing(raw,before,after)
(out/'PL02_U.ARC').write_bytes(result);a=Archive(result);old=Archive(raw)
proof.update({'passed':True,'source_bin_sha256':SOURCE_SHA,'source_arc_sha256':sha(raw),'after_arc_sha256':sha(result),'selected_refs':list(range(3,33)),'preserved_run_start_refs':[1,2],'art_target_hashes':{str(n):{'before':sha(before[n].tobytes()),'after':sha(after[n].tobytes())}for n in before}})
write(out/'verification.json',proof)
write(out/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':sha(raw),'after':sha(result)}}})
for name,mask in [('before',15),('after',0)]:
 folder=out/name;folder.mkdir();items=[]
 for n in range(1,33):
  im=a.composite(n,mask)[0];im.save(folder/f'{n:03}.png');items.append((f'{n:03} actual ARC',im))
 for k in range(0,len(items),8):page(items[k:k+8],a.composite(0,mask)[0],folder/f'actual_{k//8:02}.png',cols=4,scale=4)
 for k in range(0,30,8):
  ns=list(range(3,33))[k:k+8];page([(f'{n} OLD',old.composite(n,mask)[0])for n in ns]+[(f'{n} NEW',a.composite(n,mask)[0])for n in ns],a.composite(0,mask)[0],folder/f'old_new_{k//8:02}.png',cols=4,scale=3)
print(json.dumps({'sha256':sha(result),'parts_slack':proof['parts_slack'],'graphics_slack':proof['graphics']['remaining_slack'],'display_targets':proof['selected_display_targets'],'preserved_display':proof['preserved_display_targets']}))
