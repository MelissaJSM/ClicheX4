"""Reproduce the selected native candidate and exercise input refusals."""
from pathlib import Path
import sys,json,hashlib,copy,shutil,tempfile,contextlib,io
import numpy as np
from PIL import Image
import pack_settle as pack
import scripts.prepare_shibuki_armor_remaining as remaining
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 out=D/'packed_settle01';target=D/'joint_targets02';report=out/'reproduction.json'
 assert not report.exists()
 m=read(target/'manifest.json');parent=(ROOT/m['parent_arc']).read_bytes();want=(out/'PL00_U.ARC').read_bytes()
 original_fit=remaining.fit
 def run(data,td):
  try:
   with contextlib.redirect_stdout(io.StringIO()):return pack.build(data,td)
  finally:remaining.fit=original_fit
 copies=[]
 for i in range(1):
  rebuilt,r=run(parent,target);assert rebuilt==want
  copies.append({'iteration':i+1,'sha256':sha(rebuilt),'exact':True})
  print('native reproduction',i+1,'passed',flush=True)
 refused=[]
 def reject(name,data,td):
  try:run(data,td)
  except (ValueError,AssertionError) as e:refused.append({'case':name,'reason':str(e)})
  else:raise AssertionError('Unexpected acceptance: '+name)
 bad=bytearray(parent);bad[0]^=1;reject('wrong_parent_hash',bytes(bad),target)
 with tempfile.TemporaryDirectory(prefix='verify_settle_',dir=D) as tmp:
  td=Path(tmp).resolve();assert td.is_relative_to(D.resolve())
  for p in target.glob('layer*.png'):shutil.copyfile(p,td/p.name)
  def write_manifest(x): (td/'manifest.json').write_text(json.dumps(x,indent=2)+'\n','utf8')
  for name,mutate in [('wrong_manifest_parent',lambda z:z.update(parent_sha256='0'*64)),('missing_ref',lambda z:z['refs'].pop()),('wrong_layer_hash',lambda z:z['frames'][0]['layer_hashes'].update({'0':'0'*64}))]:
   z=copy.deepcopy(m);mutate(z);write_manifest(z);reject(name,parent,td)
  write_manifest(m);q=td/'layer0_087.png';original=q.read_bytes();arr=np.array(Image.open(q))
  for name,z in [('invalid_index',np.full(arr.shape,16,np.uint8)),('wrong_dimensions',arr[:383]),('modified_pixels',np.roll(arr,1,0))]:
   Image.fromarray(z).save(q);reject(name,parent,td);q.write_bytes(original)
 report.write_text(json.dumps({'passed':True,'candidate_sha256':sha(want),'parent_sha256':sha(parent),'targets_manifest_sha256':sha((target/'manifest.json').read_bytes()),'reproductions':copies,'refusals':refused,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'passed':True,'reproductions':len(copies),'refusals':len(refused),'sha256':sha(report.read_bytes())}))
if __name__=='__main__':main()
