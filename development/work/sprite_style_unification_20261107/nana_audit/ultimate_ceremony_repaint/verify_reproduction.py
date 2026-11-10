"""입력 잠금·오류 거부·별도 프로세스 재패킹 바이트 재현."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import sha,digest,write,need
from pack_native import build,PARENT,BEFORE,REFS,PBS
def main():
 out=D/'packed_arrival_candidate_v1';lock=json.loads((out/'INPUT_FROZEN.json').read_text('utf8'))
 for q in lock['files']:need(digest(ROOT/q['path'])==q['sha256'],'입력변조 '+q['path'])
 td=D/'arrival_targets_probe_v2';m=json.loads((td/'manifest.json').read_text('utf8'));t={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS};parent=PARENT.read_bytes();badcases=[]
 def reject(name,p,z,meta):
  try:build(p,z,meta,False)
  except(ValueError,KeyError,AssertionError)as e:badcases.append({'case':name,'rejected':True,'reason':str(e)})
  else:raise AssertionError('거부실패 '+name)
 reject('부모해시',bytes([parent[0]^1])+parent[1:],t,m)
 z=dict(t);del z[133,0];reject('목표누락',parent,z,m)
 z=dict(t);z[132,0]=t[133,0];reject('비대상추가',parent,z,m)
 z=dict(t);z[133,0]=t[133,0][:-1];reject('크기',parent,z,m)
 z=dict(t);z[133,0]=t[133,0].astype(np.int16);reject('자료형',parent,z,m)
 z=dict(t);z[133,0]=t[133,0].copy();z[133,0][0,0]=48;reject('색인범위',parent,z,m)
 z=dict(t);z[133,0]=t[133,0].copy();z[133,0][0,0]=1;reject('목표픽셀해시',parent,z,m)
 mm=copy.deepcopy(m);mm['targets']['133']['0']='0'*64;reject('매니페스트목표해시',parent,t,mm)
 result,r=build(parent,t,m,False);need(result==(out/'PL02_U.ARC').read_bytes(),'별도프로세스재현');write(out/'reproduction.json',{'passed':True,'candidate_sha256':sha(result),'parent_sha256':BEFORE,'input_files_verified':len(lock['files']),'reproduction_exact':True,'separate_process_rebuild':True,'rejected_inputs':badcases,'target_rgba_rechecked':r['rgba_combinations'],'full_rgba_previous':json.loads((out/'verification.json').read_text('utf8'))['rgba_combinations'],'scope':'최초패킹과별도프로세스의바이트동일재현.변하지않은전체7296조합은최초검사와연결,재현에서는320목표와모든raw/층/조립재대조.','runtime_verified':False});print(json.dumps({'reproduced':sha(result),'rejected':len(badcases)}))
if __name__=='__main__':main()
