from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_base_run_relocated import STORAGE,PARENT,TARGET_LOCK,chosen_storage
o=H/'base_run_storage_inputs01';need(not o.exists(),'Storage inputs already locked');choices,idle=chosen_storage();need(len(choices)==16,'Missing pairs');a=json.loads((H/STORAGE[-2]).read_text('utf8'));b=json.loads((H/STORAGE[-1]).read_text('utf8'));saved=a['saved']+b['saved'];o.mkdir()
write(o/'LOCK.json',{'parent_sha256':PARENT,'target_lock_sha256':TARGET_LOCK,'files':{p:sha((H/p).read_bytes())for p in STORAGE},'last_local_search_saved':saved,'remaining_fixed_bank_deficit_unaligned':942-saved,'selected_refs':list(range(1,33)),'all_art_preserved':True,'root_test_implementation_scope':'정해진 고정186228B entry2·최대944B 내부이동 안의 가역 시험. 실제 새offset 사용자직접승인 주장이 아님.'})
print(json.dumps({'storage_lock_sha256':sha((o/'LOCK.json').read_bytes()),'saved':saved,'remaining':942-saved}))
