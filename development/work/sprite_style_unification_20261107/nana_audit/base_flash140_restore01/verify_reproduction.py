"""140 고정후보 변경입력 거부와 별도프로세스 동일바이트 재현."""
from prepare_validation import *
def main():
 p=D/'packed_flash_candidate_v1';lock=validate(P.read_bytes());bad=[];parent=P.read_bytes()
 try:validate(bytes([parent[0]^1])+parent[1:])
 except ValueError as e:bad.append({'case':'부모변경','rejected':True,'reason':str(e)})
 else:raise ValueError('부모변경미거부')
 for changed in(p/'layer0_140.png',p/'layer5_140.png',p/'layer8_140.png',D/'pack_flash.py',p/'PL00_U.ARC',W/'zero_audit/nana_base_effect_callers01/conclusions.json'):
  def read(f):
   z=f.read_bytes();return bytes([z[0]^1])+z[1:]if f.resolve()==changed.resolve()else z
  try:validate(parent,read)
  except ValueError as e:bad.append({'case':changed.relative_to(ROOT).as_posix(),'rejected':True,'reason':str(e)})
  else:raise ValueError('입력변경미거부')
 result,target,r=build(parent,False);need(result==(p/'PL00_U.ARC').read_bytes(),'재현exact');validate(parent);write(p/'reproduction.json',{'passed':True,'candidate_sha256':sha(result),'parent_sha256':BEFORE,'input_lock_sha256':digest(p/'INPUT_FROZEN.json'),'verified_input_files':len(lock['files']),'separate_process_reproduction_exact':True,'rejected_inputs':bad,'target_RGBA':32,'prior_all_RGBA':7296,'source_and_candidate_files_modified':False});print(json.dumps({'reproduced':sha(result),'rejected':len(bad)}))
if __name__=='__main__':main()
