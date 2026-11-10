"""검토한 호버50층을 고정 은행 안에 손실 없이 패킹하는 후보 도구."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';H=W/'shibuki_audit';U=N/'ultimate_hover_repaint'
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore'),str(N/'base_run_repaint'),str(H),str(U)]
from preview_restore import Archive,need,helper
from repack_part_records_lossless import repack as global_parts
from scripts.prepare_shibuki_ultimate_production import repack_parts
from pack_shibuki_hurt import repack_fixed_global
from native_pose_pack import shared_components
from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
SHA='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
REFS=tuple(range(221,231));PBS=(0,5,6,7,8);sha=lambda b:hashlib.sha256(b).hexdigest()
def build(parent,targets,meta,all_rgba=True,shared=False):
 need(sha(parent)==SHA,'Parent hash')
 source=(U/'pack_native.py').read_text('utf8')
 patches=[("count=f['tile_count'];need","old_count=f['tile_count'];count=32;need"),("'original_tile_count':count","'original_tile_count':old_count"),("need(q['tile_count']==b.banks[gb]['frames'][n]['tile_count'],'Original tile count')","need((32 if new else q['tile_count'])==b.banks[gb]['frames'][n]['tile_count'],'Target bounded tile count')")]
 for old,new in patches:need(source.count(old)==1,'Unique guarded adaptation');source=source.replace(old,new)
 spec=importlib.util.spec_from_file_location('shibuki_base_hover_encoder01',U/'pack_native.py');m=importlib.util.module_from_spec(spec)
 exec(compile(source,str(U/'pack_native.py'),'exec'),m.__dict__);m.BEFORE=SHA;m.REFS=REFS;m.KEYS=REFS[::2]
 def fit(c,pb,changes):
  try:return repack_parts(c,pb,changes)
  except ValueError:
   nc,slack,_=global_parts(c,pb,changes);return nc,slack
 m.repack_parts=fit
 m.repack_variable=lambda g,replacements,counts:repack_fixed_global(Archive(parent),replacements,counts)
 if shared:
  def exact_pieces(raw,count,images,pool,limits):
   pieces,owners=shared_components(images)
   nr,rr=pack_many_patterns(raw,count,pieces,pool,[24]*len(pieces))
   assignments=[[part for k in own for part in rr[k]]for own in owners]
   need(all(len(q)<=24 for q in assignments),'Component part cap24')
   return nr,assignments
  m.pack_planes=exact_pieces
 result,report=m.build(parent,targets,meta,all_rgba)
 report.update(adapter_sha256=sha(source.encode('utf8')),scope='시부키 PL00 기본/포스 호버50층. 기존5공유쌍/고정은행과 비대상raw/층/조립/팔레트 보존. 호버는 다리bit8 필수이며 Ultimate 강제15와 구분한다.')
 return result,report
def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='packed_hover_candidate01');ap.add_argument('--probe',action='store_true');ap.add_argument('--shared',action='store_true');a=ap.parse_args()
 out=D/a.output;need(not out.exists() and out.resolve().is_relative_to(D.resolve()),'Fresh output');out.mkdir()
 parent=H/'prepared_nova_strike_base01/PL00_U.ARC';targets={};meta={'targets':{},'sources':{}}
 for n in REFS:
  source=D/('body_layers_probe04'if n%2 else'shot_composed01');meta['targets'][str(n)]={};meta['sources'][str(n)]={}
  for pb in PBS:
   f=source/f'layer{pb}_{n:03}.png';z=np.array(Image.open(f));targets[n,pb]=z;meta['targets'][str(n)][str(pb)]=sha(z.tobytes());meta['sources'][str(n)][str(pb)]={'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f.read_bytes())}
 for n in REFS[::2]:need(np.array_equal(targets[n,8],targets[n+1,8]),'Pair legs exact')
 (out/'input_lock.json').write_text(json.dumps(meta,indent=2)+'\n','utf8')
 try:result,report=build(parent.read_bytes(),targets,meta,not a.probe,a.shared)
 except Exception as e:
  (out/'failed.json').write_text(json.dumps({'failed':True,'reason':str(e),'game_written':False},indent=2)+'\n','utf8');raise
 (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 if not a.probe:
  (out/'PL00_U.ARC').write_bytes(result);b=Archive(result);old=Archive(parent.read_bytes())
  for n in REFS:
   helper.grid([(str(n),[('idle basic',b.composite(0,8)[0]),('before basic',old.composite(n,8)[0]),('new basic',b.composite(n,8)[0]),('idle Fourth',b.composite(0,15)[0]),('new Fourth',b.composite(n,15)[0])])],out/f'readback_{n}.png',5)
 print(json.dumps({'after':sha(result),'layers':report['target_layers_exact'],'combinations':report['rgba_combinations'],'packed':not a.probe}))
if __name__=='__main__':main()
