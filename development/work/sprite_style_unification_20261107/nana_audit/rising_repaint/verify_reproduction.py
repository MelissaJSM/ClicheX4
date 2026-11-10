"""고정 입력에서 라이징 후보 재현 및 잘못된 입력의 조기 거부."""
from pathlib import Path
import sys,json,copy,importlib.util
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import digest,sha,write,need
spec=importlib.util.spec_from_file_location('nana_rising_producer',D/'pack_native.py');producer=importlib.util.module_from_spec(spec);spec.loader.exec_module(producer)

def main():
 out=D/'packed_base_candidate_v1';td=D/'joint_layers_probe_v2';data=producer.PARENT.read_bytes();candidate=(out/'PL00_U.ARC').read_bytes();meta=json.loads((td/'manifest.json').read_text('utf8'));targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in producer.REFS for pb in producer.PBS};rejected=[]
 def reject(name,fn):
  try:fn()
  except(ValueError,KeyError,TypeError):rejected.append(name)
  else:raise ValueError('Bad input accepted: '+name)
 bad=bytearray(data);bad[-1]^=1;reject('wrong_parent',lambda:producer.build(bytes(bad),targets,meta))
 for name,mut in(('wrong_manifest_parent',lambda m:m.update(source_arc_sha256='0'*64)),('duplicate_ref',lambda m:m['frames'].__setitem__(0,m['frames'][1])),('target_hash',lambda m:m['frames'][0].update(base_sha256='0'*64))):
  m=copy.deepcopy(meta);mut(m);reject(name,lambda m=m:producer.validate_targets(targets,m))
 t=dict(targets);t.pop((100,0));reject('missing_target',lambda:producer.validate_targets(t,meta))
 t=dict(targets);t[105,0]=t[100,0];reject('unexpected_target',lambda:producer.validate_targets(t,meta))
 for name,v in(('changed_texel',targets[100,0].copy()),('wrong_shape',np.zeros((383,384),np.uint8)),('wrong_depth',targets[100,0].astype(np.uint16)),('invalid_index',targets[100,0].copy())):
  if name=='changed_texel':v[160,160]^=1
  if name=='invalid_index':v[0,0]=16
  t=dict(targets);t[100,0]=v;reject(name,lambda t=t:producer.validate_targets(t,meta))
 t=dict(targets);t[100,0]=targets[100,0].copy();t[100,0][0,0]=1;m=copy.deepcopy(meta);m['frames'][0]['base_sha256']=sha(t[100,0].tobytes());reject('outside_registration_window',lambda:producer.validate_targets(t,m))
 t=dict(targets);t[232,0]=targets[232,0].copy();t[232,0][160,160]^=1;m=copy.deepcopy(meta);next(q for q in m['frames']if q['ref']==232)['base_sha256']=sha(t[232,0].tobytes());reject('broken231_232_identity',lambda:producer.validate_targets(t,m))
 lock=json.loads((out/'INPUT_FROZEN.json').read_text('utf8'))
 for q in lock['files']:need(digest(ROOT/q['path'])==q['sha256'],'Frozen input drift '+q['path'])
 rebuilt,verify=producer.build(data,targets,meta);need(rebuilt==candidate,'Byte-identical reproduction')
 write(out/'reproduction.json',{'passed':True,'candidate_sha256':sha(candidate),'parent_sha256':sha(data),'negative_cases':rejected,'input_files_verified':len(lock['files']),'same_process_rebuild_byte_identical':True,'full7296_recheck':verify['rgba_combinations'],'separate_process_reproduction':False,'runtime_verified':False})
 print(json.dumps({'passed':True,'negative_cases':len(rejected),'candidate_sha256':sha(candidate)}))
if __name__=='__main__':main()
