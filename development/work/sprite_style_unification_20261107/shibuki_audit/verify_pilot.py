"""새 등록 패커의 재현/거부 검사. 실제 게임 실행 검사가 아니다."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from native_pose_pack import H,ROOT,SOURCE,SOURCE_SHA,packing,read_disc,load
from src.psx_disc import file_hash
def main():
 refs=[11,13,17,33,71];p=ROOT/'work/sprite_style_unification_20261107/shibuki/pilot01/native_preview'
 b={n:load(p/f'{n:03}_indices.png')for n in refs};a={n:load(H/'after_registered02'/f'{n:03}_indices.png')for n in refs}
 raw=read_disc(SOURCE,('PL02_U.ARC',))[0]['PL02_U.ARC'];out,proof=packing(raw,b,a)
 expected=(H/'prepared_pilot01/PL02_U.ARC').read_bytes();assert out==expected
 cases=[]
 tests=[('wrong_source',lambda:packing(raw[:-1]+bytes([raw[-1]^1]),b,a)),
        ('missing_after',lambda:packing(raw,b,{n:v for n,v in a.items()if n!=11})),
        ('accepted_idle',lambda:packing(raw,{0:b[11]},{0:a[11]})),
        ('wrong_canvas',lambda:packing(raw,{11:b[11][:-1]},{11:a[11]})),
        ('wrong_scope',lambda:packing(raw,{120:b[11]},{120:a[11]}))]
 bad={n:v.copy()for n,v in a.items()};bad[11][150,130]=5
 tests.append(('after_outside_coat',lambda:packing(raw,b,bad)))
 for name,fn in tests:
  try:fn()
  except ValueError as e:cases.append({'name':name,'rejected':True,'reason':str(e)})
  else:raise AssertionError(name+' accepted')
 assert file_hash(SOURCE)==SOURCE_SHA
 result={'passed':True,'reproduced_arc_sha256':hashlib.sha256(out).hexdigest(),'reproduced_byte_identical':True,'input_rejection_cases':cases,'source_bin_preserved':True,'runtime_verified':False,'production_complete':False}
 (H/'prepared_pilot01/repro_and_rejections.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(result))
if __name__=='__main__':main()
