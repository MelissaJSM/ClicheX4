"""고정 입력과 잘못된8입력 거부·별도 프로세스 바이트 재현을 검사한다."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import sha,digest,write,need
from pack_native import build,PARENT,BEFORE,REFS,PBS
def main():
 out=D/'packed_recoil_candidate_v1';lock=json.loads((out/'INPUT_FROZEN.json').read_text('utf8'))
 for q in lock['files']:need(digest(ROOT/q['path'])==q['sha256'],'입력변경 '+q['path'])
 td=D/'targets_v1';m=json.loads((td/'manifest.json').read_text('utf8'));t={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS};parent=PARENT.read_bytes();bad=[]
 def reject(name,p,z,mm):
  try:build(p,z,mm,False)
  except(ValueError,AssertionError,KeyError)as e:bad.append({'case':name,'rejected':True,'reason':str(e)})
  else:raise AssertionError('잘못된 입력 수용 '+name)
 reject('부모해시',bytes([parent[0]^1])+parent[1:],t,m)
 z=dict(t);del z[90,0];reject('목표누락',parent,z,m)
 z=dict(t);z[95,0]=t[90,0];reject('비대상참조추가',parent,z,m)
 z=dict(t);z[90,0]=t[90,0][:-1];reject('크기',parent,z,m)
 z=dict(t);z[90,0]=t[90,0].astype(np.int16);reject('자료형',parent,z,m)
 z=dict(t);z[90,0]=t[90,0].copy();z[90,0][0,0]=16;reject('색인범위',parent,z,m)
 z=dict(t);z[90,0]=t[90,0].copy();z[90,0][0,0]=1;reject('목표픽셀해시',parent,z,m)
 mm=copy.deepcopy(m);mm['targets']['90']['0']='0'*64;reject('매니페스트해시',parent,t,mm)
 result,r=build(parent,t,m,False);need(result==(out/'PL02_U.ARC').read_bytes(),'별도프로세스바이트재현');write(out/'reproduction.json',{'passed':True,'candidate_sha256':sha(result),'parent_sha256':BEFORE,'input_lock_sha256':digest(out/'INPUT_FROZEN.json'),'input_files_verified':len(lock['files']),'separate_process_rebuild':True,'reproduction_exact':True,'rejected_inputs':bad,'target_rgba_rechecked':r['rgba_combinations'],'full_rgba_previous':7296,'scope':'최초전체7296RGBA와이번64대상RGBA 재현을구분. 모든raw/층/비대상조립도재대조. 미술최종/독립/실기아님.','runtime_verified':False});print(json.dumps({'passed':True,'reproduced':sha(result),'rejected':len(bad)}))
if __name__=='__main__':main()
