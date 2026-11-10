"""Reproduce the final candidate and reject malformed native inputs."""
from pathlib import Path
import json,hashlib,copy,tempfile,shutil,io,contextlib
import numpy as np
from PIL import Image
import pack_final02 as pack
D=Path(__file__).resolve().parent;ROOT=D.parents[2];out=D/'packed_hover_final01';td=D/'final_targets01'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 report=out/'reproduction.json';assert not report.exists();m=json.loads((td/'manifest.json').read_text('utf8'));parent=(ROOT/m['parent']['path']).read_bytes();wanted=(out/'PL00_U.ARC').read_bytes()
 with contextlib.redirect_stdout(io.StringIO()):rebuilt,r=pack.build(parent,td,False)
 assert rebuilt==wanted;print('Final source reproduced exactly',flush=True);failures=[]
 def reject(name,data,folder):
  try:pack.build(data,folder)
  except(AssertionError,ValueError,KeyError,FileNotFoundError)as e:failures.append({'case':name,'error':str(e)})
  else:raise AssertionError('Invalid input accepted: '+name)
 bad=bytearray(parent);bad[0]^=1;reject('wrong_parent_hash',bytes(bad),td)
 with tempfile.TemporaryDirectory(prefix='final_refusals_',dir=D)as tmp:
  test=Path(tmp).resolve();assert test.is_relative_to(D.resolve())
  for f in td.glob('layer*.png'):shutil.copyfile(f,test/f.name)
  def write(z):(test/'manifest.json').write_text(json.dumps(z),'utf8')
  for name,fn in [('wrong_manifest_parent',lambda z:z['parent'].update(sha256='0'*64)),('missing_ref',lambda z:z['frames'].pop()),('duplicate_ref',lambda z:z['frames'][0].update(ref=222)),('missing_layer',lambda z:z['frames'][0]['layer_hashes'].pop('8')),('wrong_layer_hash',lambda z:z['frames'][0]['layer_hashes'].update({'0':'0'*64}))]:
   z=copy.deepcopy(m);fn(z);write(z);reject(name,parent,test)
  write(m);f=test/'layer0_221.png';old=f.read_bytes();a=np.array(Image.open(f))
  for name,v in [('invalid_index',np.full_like(a,16)),('wrong_size',a[:383]),('changed_pixels',np.roll(a,1,0)),('RGB_instead_of_index',np.repeat(a[:,:,None],3,axis=2))]:
   Image.fromarray(v).save(f);reject(name,parent,test);f.write_bytes(old)
  f.unlink();reject('missing_layer_file',parent,test)
 report.write_text(json.dumps({'passed':True,'candidate_sha256':sha(wanted),'parent_sha256':sha(parent),'reproductions':[{'exact':True,'sha256':sha(rebuilt)}],'refusals':failures,'all_rgba_in_original_pack':7296,'target_rgba_in_reproduction':r['rgba_combinations'],'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'passed':True,'candidate':sha(wanted),'refusals':len(failures)}))
if __name__=='__main__':main()
