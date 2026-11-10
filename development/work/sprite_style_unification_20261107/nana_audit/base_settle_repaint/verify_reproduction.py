"""최종138/139의 입력 거부 및 별도 프로세스 바이트 재현."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore')]
from preview_restore import sha,digest,write,need
from pack_native import build,REFS,PBS
def main():
 out=D/'packed_settle_candidate_v1';lock=json.loads((out/'INPUT_FROZEN.json').read_text('utf8'));v=json.loads((out/'verification.json').read_text('utf8'))
 for q in lock['files']:need(digest(ROOT/q['path'])==q['sha256'],'입력변조 '+q['path'])
 td=D/'joint_layers_probe_v3';m=json.loads((td/'manifest.json').read_text('utf8'));t={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS};parent=(ROOT/v['parent_path']).read_bytes();badcases=[]
 def reject(name,p,z,meta):
  try:build(p,z,meta,v['before'],False)
  except(ValueError,KeyError,AssertionError)as e:badcases.append({'case':name,'rejected':True,'reason':str(e)})
  else:raise AssertionError('거부실패 '+name)
 reject('부모해시',bytes([parent[0]^1])+parent[1:],t,m)
 z=dict(t);del z[138,0];reject('목표누락',parent,z,m)
 z=dict(t);z[137,0]=t[138,0];reject('비대상추가',parent,z,m)
 z=dict(t);z[138,0]=t[138,0][:-1];reject('크기',parent,z,m)
 z=dict(t);z[138,0]=t[138,0].astype(np.int16);reject('자료형',parent,z,m)
 z=dict(t);z[138,0]=t[138,0].copy();z[138,0][0,0]=48;reject('색인범위',parent,z,m)
 z=dict(t);z[138,0]=t[138,0].copy();z[138,0][0,0]=1;reject('목표픽셀해시',parent,z,m)
 mm=copy.deepcopy(m);mm['frames'][0]['layer_hashes']['0']='0'*64;reject('매니페스트목표해시',parent,t,mm)
 mm=copy.deepcopy(m);z=dict(t);z[139,0]=t[138,0].copy();mm['frames'][1]['layer_hashes']['0']=sha(z[139,0].tobytes());reject('139 원래 y-1 관계',parent,z,mm)
 result,r=build(parent,t,m,v['before'],False);need(result==(out/'PL00_U.ARC').read_bytes(),'별도프로세스 재현')
 write(out/'reproduction.json',{'passed':True,'candidate_sha256':sha(result),'parent_sha256':v['before'],'input_files_verified':len(lock['files']),'reproduction_exact':True,'separate_process_rebuild':True,'rejected_inputs':badcases,'target_rgba_rechecked':r['rgba_combinations'],'full_rgba_previous':v['rgba_combinations'],'scope':'첫7296전체조합과별도 재현64목표조합/전체raw·층·조립을 분리한다.','runtime_verified':False});print(json.dumps({'reproduced':sha(result),'rejected':len(badcases)}))
if __name__=='__main__':main()
