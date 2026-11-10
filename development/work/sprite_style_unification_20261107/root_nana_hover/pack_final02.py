"""Reproducible fixed-bank hover encoder with guarded source and target inputs."""
from pathlib import Path
import sys,json,importlib.util,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';U=N/'ultimate_hover_repaint';H=W/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(H),str(D),str(U)]
from preview_restore import Archive,need
from pinned_head_pack import HeadPacker
from repack_part_records_lossless import repack as global_parts
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
SHA='8951948879773266cae0bebd408b411f4806b5652257bba3c50df0212b3c6e10'
REFS=tuple(range(221,231));PBS=(0,5,6,7,8);EMPTY=(128,129,132,140,159)
GEOM=[(1,69,48),(2,69,64),(3,85,48),(4,85,64),(5,85,80),(6,101,64)]
sha=lambda b:hashlib.sha256(b).hexdigest()
def load_targets(td):
 m=json.loads((td/'manifest.json').read_text('utf8'))
 need(m['parent']['sha256']==SHA,'Target parent SHA')
 need([q['ref'] for q in m['frames']]==list(REFS),'Exact ten target refs')
 targets={};meta={'targets':{}}
 for q in m['frames']:
  n=q['ref'];need(set(q['layer_hashes'])==set(map(str,PBS)),'Exact five target layers');meta['targets'][str(n)]={}
  for pb in PBS:
   f=td/f'layer{pb}_{n}.png';z=np.array(Image.open(f));need(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16,'Index format')
   need(sha(z.tobytes())==q['layer_hashes'][str(pb)],'Indexed target hash')
   need(sha(f.read_bytes())==q['sources'][str(pb)]['output_sha256'],'PNG target hash')
   targets[n,pb]=z;meta['targets'][str(n)][str(pb)]=sha(z.tobytes())
 for n in REFS[::2]:need(np.array_equal(targets[n,8],targets[n+1,8]),'Shared leg pair')
 return targets,meta
def build(parent,td,all_rgba=False):
 need(sha(parent)==SHA,'Parent SHA');targets,meta=load_targets(td);a=Archive(parent)
 for n in EMPTY:need(not a.layer(n,5)[0].any()and len(records(a.c,5,n))==4,'Transparent one-record head proof')
 spec=importlib.util.spec_from_file_location('final_hover_encoder',U/'pack_native.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);source=(U/'pack_native.py').read_text('utf8')
 patches=[("count=f['tile_count'];need","old_count=f['tile_count'];count=32;need"),("'original_tile_count':count","'original_tile_count':old_count"),("need(q['tile_count']==b.banks[gb]['frames'][n]['tile_count'],'Original tile count')","need((32 if new else q['tile_count'])==b.banks[gb]['frames'][n]['tile_count'],'Bounded target tile count')"),("need(records(a.c,pb,n)==records(b.c,pb,n),f'Composition{pb}/{n}');parts+=1","need((b'' if pb==5 and n in EMPTY_REFS else records(a.c,pb,n))==records(b.c,pb,n),f'Composition{pb}/{n}');parts+=1")]
 for before,after in patches:need(source.count(before)==1,'Unique guarded adapter');source=source.replace(before,after)
 exec(compile(source,str(U/'pack_native.py'),'exec'),p.__dict__);p.BEFORE=SHA;p.REFS=REFS;p.KEYS=REFS[::2];p.EMPTY_REFS=EMPTY
 def fit(c,pb,changes):
  if pb==5:
   changes=dict(changes)
   for n in EMPTY:changes[n]=b''
   nc,slack,_=global_parts(c,pb,changes);need(slack==0,'Expected head bank fit');return nc,slack
  try:return repack_parts(c,pb,changes)
  except ValueError:
   nc,slack,_=global_parts(c,pb,changes);return nc,slack
 hp=HeadPacker.__new__(HeadPacker);hp.geom=GEOM;hp.rects=[[x,y]for t,x,y in GEOM];p.pack_planes=hp;p.repack_parts=fit
 result,report=p.build(parent,targets,meta,all_rgba);b=Archive(result)
 for n in EMPTY:need(records(b.c,5,n)==b''and np.array_equal(a.layer(n,5)[0],b.layer(n,5)[0]),'Empty representation exact')
 report['nonselected_compositions_checked']=report['nonselected_compositions_exact'];report['nonselected_compositions_exact']-=5
 report.update(empty_head_refs=list(EMPTY),empty_head_storage_bytes_saved=20,source_adapter_sha256=sha(source.encode('utf8')),scope='PL00 기본/포스 50층. 투명 헤드5의 count1→0 저장변환만 예외로 명시하며 비대상 표시·raw·은행·팔레트·EXE는 보존한다. 호버 bit8 필수, Ultimate 강제mask15 규칙과 혼동하지 않는다.')
 return result,report
