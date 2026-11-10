"""Input refusal and exact authored effects on the fixed candidate."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path.insert(0,str(D))
from pack_dash_native import validate_source,validate_output,validate_targets,REFS,PBS
from preview_restore import Archive,sha,digest,need,write
def main():
 o=D/'packed_dash_candidate_v1';t=D/'joint_layers_candidate_v1';m=json.loads((t/'manifest.json').read_text('utf8'));data=(D.parent/'air_repaint/packed_air_candidate_v1/PL00_U.ARC').read_bytes();targets={(n,pb):np.array(Image.open(t/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS};tests=[]
 def rejects(name,fn):
  try:fn()
  except(ValueError,KeyError):tests.append(name);return
  raise AssertionError('Accepted invalid input '+name)
 bad=bytearray(data);bad[100]^=1;rejects('wrong_parent_sha',lambda:validate_source(bytes(bad)));rejects('output_outside_scope',lambda:validate_output(ROOT/'out/forbidden_audio_agent'));rejects('existing_output',lambda:validate_output(o))
 q=targets.copy();q.pop((67,0));rejects('missing_target',lambda:validate_targets(q,m));q=targets.copy();q[999,0]=targets[67,0];rejects('unexpected_target',lambda:validate_targets(q,m));q=targets.copy();q[67,0]=targets[67,0].astype(np.uint16);rejects('wrong_dtype',lambda:validate_targets(q,m));q=targets.copy();q[67,0]=targets[67,0][:-1];rejects('wrong_dimensions',lambda:validate_targets(q,m));q=targets.copy();q[67,0]=targets[67,0].copy();q[67,0][0,0]=16;rejects('out_of_palette',lambda:validate_targets(q,m));q=targets.copy();q[67,0]=targets[67,0].copy();q[67,0][0,0]=1;rejects('altered_target_checksum',lambda:validate_targets(q,m));mm=copy.deepcopy(m);mm['source_arc_sha256']='0'*64;rejects('wrong_manifest_parent',lambda:validate_targets(targets,mm))
 packed=(o/'PL00_U.ARC').read_bytes();reproduced=(D/'packed_dash_reproduction_v1/PL00_U.ARC').read_bytes();need(packed==reproduced,'Exact re-run');effects=[]
 for n,bn in((73,71),(74,72)):
  fx=np.array(Image.open(D/'effects'/f'effect_{n:03}.png'));expected=np.where(fx,fx,targets[bn,0]).astype(np.uint8);need(np.array_equal(targets[n,0],expected),'Original effect and new body');need(np.count_nonzero(fx)==54,'54 original effect pixels')
  for pb in(5,6,7,8):need(np.array_equal(targets[n,pb],targets[bn,pb]),'Same corresponding armor')
  effects.append({'ref':n,'body_ref':bn,'original_effect_pixels':54,'effect_sha256':sha(fx.tobytes())})
 write(o/'reproduction_and_guards.json',{'passed':True,'before':sha(data),'after':sha(packed),'exact_arc_reproduction':True,'rejected':tests,'effects':effects,'source_manifest_sha256':digest(t/'manifest.json'),'runtime_verified':False});print(json.dumps({'passed':True,'rejections':len(tests),'after':sha(packed)}))
if __name__=='__main__':main()
