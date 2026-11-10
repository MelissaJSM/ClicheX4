"""정밀 벽12참조를 동결 정면/저체력 준비본에 누적 패킹한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,need,sha,write
from src.psx_disc import file_hash
import pack_lowhp_return as backend
from review_wall_partial import targets,compose

PARENT_SHA='c430ba90992f7a4ee7851e0670cac01bfbc9410df9007da63cb409b9b284af87'
SELECTION_SHA='80da6cbfa706a3fce1f79133390ed12b719940046e7670eebda81977d1e2325b'

def pack(data,desired):
 need(sha(data)==PARENT_SHA,'Wrong frozen front/lowHP parent')
 old_sha,old_selected=backend.ARC_SHA,backend.SELECTED
 try:
  backend.ARC_SHA=PARENT_SHA;backend.SELECTED=set(range(55,67));return backend.pack(data,desired)
 finally:backend.ARC_SHA=old_sha;backend.SELECTED=old_selected

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');original=read_disc(SOURCE,('PL00_U.ARC','ST0E_U1.ARC'))[0];parent=H/'prepared_front_return01';data=(parent/'PL00_U.ARC').read_bytes();selection=(parent/'ST0E_U1.ARC').read_bytes();need(sha(selection)==SELECTION_SHA,'Selection parent changed');desired=targets();out=H/'prepared_wall_front01';need(not out.exists(),'Output exists');out.mkdir()
 try:result,proof=pack(data,desired)
 except ValueError as exc:
  write(out/'capacity_failure.json',{'passed':False,'reason':str(exc),'art_not_simplified':True,'arc_not_written':True});raise
 after=Archive(result);before=Archive(data);(out/'PL00_U.ARC').write_bytes(result);(out/'ST0E_U1.ARC').write_bytes(selection)
 proof.update({'source_bin_sha256':SOURCE_SHA,'source_original_arc_sha256':sha(original['PL00_U.ARC']),'source_parent_arc_sha256':PARENT_SHA,'result_arc_sha256':sha(result),'new_body_and_accepted_idle_head':False,'new_heads_and_new_outfit_art':True,'selected_refs':list(range(55,67)),'includes_frozen_lowhp120_125_front156_158_selection19_21':True,'selection_unchanged_from_frozen_front':True,'old_head_body_sleeve_overwrite':False,'art_target_hashes':{str(n):{str(b):sha(v.tobytes())for b,v in layers.items()}for n,layers in desired.items()},'runtime_verified':False})
 write(out/'verification.json',proof)
 write(out/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{name:{'path':(out/name).relative_to(ROOT).as_posix(),'before':sha(original[name]),'after':sha(value)}for name,value in(('PL00_U.ARC',result),('ST0E_U1.ARC',selection))}})
 for mask,label in((0,'base'),(15,'fourth')):
  items=[]
  for n in range(55,67):
   im=after.composite(n,mask)[0];im.save(out/f'{label}_{n:03}.png');need(im.tobytes()==compose(before,desired[n],mask,2).tobytes(),'Actual target mismatch');items.extend([(f'{n} current',before.composite(n,mask)[0]),(f'{n} actual new ARC',im)])
  for k in(0,12):page(items[k:k+12],after.composite(0,mask)[0],out/f'{label}_comparison{k//12:02}.png',cols=2,scale=4)
 for n in range(55,67):page([(f'{n} mask{m:X}',after.composite(n,m)[0])for m in range(16)],after.composite(0,15)[0],out/f'partial_{n:03}.png',cols=4,scale=3)
 print(json.dumps({'sha256':sha(result),'groups':proof['groups'],'parts_slack':proof['parts_slack'],'gfx_slack':proof['graphics']['remaining_slack'],'checks':proof['partial_mask_arm_comparisons']}))

if __name__=='__main__':main()
