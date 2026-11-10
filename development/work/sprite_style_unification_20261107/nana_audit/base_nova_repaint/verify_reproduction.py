"""고정입력 변경거부 및 별도프로세스 동일패킹을 확인한다."""
from pack_candidate import *
from lock_candidate import validate_inputs
def main():
 p=D/'packed_nova_candidate_v1';lock=validate_inputs(PARENT.read_bytes());bad=[];parent=PARENT.read_bytes()
 try:validate_inputs(bytes([parent[0]^1])+parent[1:])
 except ValueError as e:bad.append({'case':'부모변경','rejected':True,'reason':str(e)})
 else:raise ValueError('부모변경 수용')
 files=[D/'a_v1/generated.png',D/'b_v1/generated.png',D/'preparation_effect_probe_v2/layer0_213.png',D/'dash_layers_probe_v1/layer8_220.png',D/'preparation_effect_probe_v2/effect214_indices.png',D/'head_templates_probe_v2/choices.json',D/'pack_candidate.py',p/'PL00_U.ARC']
 for changed in files:
  def read(f):
   z=f.read_bytes();return bytes([z[0]^1])+z[1:]if f.resolve()==changed.resolve()else z
  try:validate_inputs(parent,read)
  except ValueError as e:bad.append({'case':changed.relative_to(ROOT).as_posix(),'rejected':True,'reason':str(e)})
  else:raise ValueError('입력변경 수용')
 out=D/'reproduction_v1';need(not out.exists(),'신규재현경로');out.mkdir();r=build(out,False);need((out/'PL00_U.ARC').read_bytes()==(p/'PL00_U.ARC').read_bytes(),'별도재현exact');validate_inputs(parent)
 write(p/'reproduction.json',{'passed':True,'candidate_sha256':r['after'],'parent_sha256':BEFORE,'input_lock_sha256':digest(p/'INPUT_FROZEN.json'),'input_files_checked':len(lock['files']),'separate_process_reproduction_exact':True,'reproduction_target_RGBA':r['target_rgba_combinations'],'prior_all_RGBA':7296,'rejected_cases':bad,'original_inputs_unchanged':True,'scope':'변경입력은 메모리read대체만 사용하고 원파일은수정하지않음.첫전체검사와별도대상192조합 재현을구분.실기미실행.'});print(json.dumps({'passed':True,'rejected':len(bad),'reproduced':r['after']}))
if __name__=='__main__':main()
