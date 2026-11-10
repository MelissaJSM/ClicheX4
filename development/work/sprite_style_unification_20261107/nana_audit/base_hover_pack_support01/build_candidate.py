"""기존 새50층/6헤드사각 유지, 완전투명 head5만 기존count0 표현으로 저장."""
from pathlib import Path
import sys,json,importlib.util,struct,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1];R=W/'root_nana_hover';H=W/'shibuki_audit';U=N/'ultimate_hover_repaint'
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(H),str(R),str(U)]
from preview_restore import Archive,sha,digest,write,need
from pinned_head_pack import HeadPacker
from repack_part_records_lossless import repack as global_parts
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
EMPTY=(128,129,132,140,159)
GEOM=[(1,69,48),(2,69,64),(3,85,48),(4,85,64),(5,85,80),(6,101,64)]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='candidate01');args=ap.parse_args();out=(D/args.out).resolve();need(out.is_relative_to(D)and not out.exists(),'신규 소유경로');out.mkdir();audit=json.loads((R/'input_audit.json').read_text('utf8'));parent=ROOT/audit['input']['path'];need(digest(parent)==audit['input']['sha256'],'부모');a=Archive(parent.read_bytes());refs=tuple(range(221,231));pbs=(0,5,6,7,8);targets={};meta={'targets':{}};inputs=[]
 for n in refs:
  folder=R/('body_layers_probe01'if n%2 else'shoot_layers_probe02');m=json.loads((folder/'manifest.json').read_text('utf8'));q=next(q for q in m['frames']if q['ref']==n);meta['targets'][str(n)]={}
  for pb in pbs:
   f=folder/f'layer{pb}_{n}.png';z=np.array(Image.open(f));need(sha(z.tobytes())==q['layer_hashes'][str(pb)],'원새층 해시');targets[n,pb]=z;meta['targets'][str(n)][str(pb)]=sha(z.tobytes());inputs.append({'path':f.relative_to(ROOT).as_posix(),'sha256':digest(f)})
 for n in EMPTY:need(not a.layer(n,5)[0].any()and len(records(a.c,5,n))==4,'빈 한기록 근거')
 spec=importlib.util.spec_from_file_location('base_hover_support_encoder',U/'pack_native.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);source=(U/'pack_native.py').read_text('utf8')
 patches=[("count=f['tile_count'];need","old_count=f['tile_count'];count=32;need"),("'original_tile_count':count","'original_tile_count':old_count"),("need(q['tile_count']==b.banks[gb]['frames'][n]['tile_count'],'Original tile count')","need((32 if new else q['tile_count'])==b.banks[gb]['frames'][n]['tile_count'],'Bounded target tile count')"),("need(records(a.c,pb,n)==records(b.c,pb,n),f'Composition{pb}/{n}');parts+=1","need((b'' if pb==5 and n in EMPTY_REFS else records(a.c,pb,n))==records(b.c,pb,n),f'Composition{pb}/{n}');parts+=1")]
 for before,after in patches:need(source.count(before)==1,'Adapter patch unique');source=source.replace(before,after)
 adapter=out/'encoder_adapter.py';adapter.write_text(source,'utf8');exec(compile(source,str(adapter),'exec'),p.__dict__);p.BEFORE=audit['input']['sha256'];p.KEYS=refs[::2];p.REFS=refs;p.EMPTY_REFS=EMPTY
 def fit(c,pb,changes):
  if pb==5:
   changes=dict(changes,**{})
   for n in EMPTY:changes[n]=b''
   nc,slack,detail=global_parts(c,pb,changes);need(slack==0,'예측20B');return nc,slack
  try:return repack_parts(c,pb,changes)
  except ValueError:
   nc,slack,detail=global_parts(c,pb,changes);return nc,slack
 hp=HeadPacker.__new__(HeadPacker);hp.geom=GEOM;hp.rects=[[x,y]for t,x,y in GEOM];p.pack_planes=hp;p.repack_parts=fit
 result,report=p.build(parent.read_bytes(),targets,meta,True);b=Archive(result)
 for n in EMPTY:
  need(records(b.c,5,n)==b'','새count0');need(np.array_equal(a.layer(n,5)[0],b.layer(n,5)[0]),'빈층 exact')
 checked=report['nonselected_compositions_exact'];report['nonselected_compositions_checked']=checked;report['nonselected_compositions_exact']=checked-len(EMPTY)
 report.update(scope='새호버50층 무손실 패킹. 비대상128/129/132/140/159의 완전투명 head 단일기록만 기존count0 표현으로 바꿈. 나머지 비대상 records exact. 비대상raw/표시/팔레트와고정은행 보존.',parent_arc=audit['input']['path'],target_inputs=inputs,empty_head_refs=list(EMPTY),empty_head_record_bytes_saved=20,common_geometry=GEOM,new_MIPS_execution=False,runtime_verified=False,producer_root_files_modified=False)
 (out/'PL00_U.ARC').write_bytes(result);write(out/'verification.json',report);print(json.dumps({'passed':True,'after':sha(result),'slack':report['composition_slack'],'rgba':report['rgba_combinations'],'target_layers':report['target_layers_exact']}))
if __name__=='__main__':main()
