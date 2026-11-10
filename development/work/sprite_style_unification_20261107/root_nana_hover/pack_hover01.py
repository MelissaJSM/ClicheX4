"""Pack exact new PL00 hover layers through the proven pair-stream encoder."""
from pathlib import Path
import sys,json,hashlib,importlib.util,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';U=N/'ultimate_hover_repaint';H=W/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(U),str(H)]
spec=importlib.util.spec_from_file_location('ultimate_hover_packer_shared',U/'pack_native.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
from repack_part_records_lossless import repack as global_parts
from pack_air_targets_probe import pack_pinned
from preview_restore import Archive,helper
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda f:json.loads(f.read_text('utf8'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='packed_hover01');ap.add_argument('--probe',action='store_true');args=ap.parse_args()
 out=(D/args.out).resolve();assert out.is_relative_to(D.resolve())and not out.exists();out.mkdir()
 audit=read(D/'input_audit.json');parent=ROOT/audit['input']['path'];assert sha(parent.read_bytes())==audit['input']['sha256']
 p.BEFORE=audit['input']['sha256'];p.KEYS=(221,223,225,227,229);p.REFS=tuple(range(221,231));targets={};meta={'targets':{}};sources=[]
 for n in p.REFS:
  folder=D/('body_layers_probe01'if n%2 else'shoot_layers_probe02');source=read(folder/'manifest.json');row=next(x for x in source['frames']if x['ref']==n);meta['targets'][str(n)]={}
  for pb in p.PBS:
   f=folder/f'layer{pb}_{n}.png';z=np.array(Image.open(f));assert sha(z.tobytes())==row['layer_hashes'][str(pb)];targets[n,pb]=z;meta['targets'][str(n)][str(pb)]=sha(z.tobytes());sources.append({'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f.read_bytes())})
 old=p.repack_parts
 def fit_parts(c,pb,changes):
  try:return old(c,pb,changes)
  except ValueError:
   result,slack,details=global_parts(c,pb,changes);print(json.dumps({'bank':pb,'lossless_part_records':details}),flush=True);return result,slack
 p.repack_parts=fit_parts
 # PL00 currently uses only20 tiles here. The proven native player buffer is
 # 32 tiles; keep each shared pair and all external bank boundaries fixed.
 # Preserve the frozen encoder source and save this exact local adaptation.
 source=(U/'pack_native.py').read_text('utf8')
 for before,after in [("count=f['tile_count'];need", "old_count=f['tile_count'];count=32;need"),("'original_tile_count':count", "'original_tile_count':old_count"),("need(q['tile_count']==b.banks[gb]['frames'][n]['tile_count'],'Original tile count')", "need((32 if new else q['tile_count'])==b.banks[gb]['frames'][n]['tile_count'],'Bounded target tile count')")]:
  assert source.count(before)==1;source=source.replace(before,after)
 adapted=out/'encoder_adapter.py';adapted.write_text(source,'utf8');exec(compile(source,str(adapted),'exec'),p.__dict__)
 p.BEFORE=audit['input']['sha256'];p.KEYS=(221,223,225,227,229);p.REFS=tuple(range(221,231));p.repack_parts=fit_parts
 def pack_pair(raw,count,images,pool,limits):
  assert count==32 and all(z.max()<16 for z in images)
  nr,rr,method=pack_pinned(raw,images,pool);print(json.dumps({'pair_pack':method}),flush=True);return nr,rr
 from pinned_head_pack import HeadPacker
 head_packer=HeadPacker(targets,p.REFS,Archive(parent.read_bytes()));print(json.dumps({'common_head_rectangles':head_packer.rects}),flush=True)
 p.pack_planes=head_packer
 try:result,report=p.build(parent.read_bytes(),targets,meta,not args.probe)
 except Exception as error:
  (out/'failure.json').write_text(json.dumps({'error':str(error),'type':type(error).__name__,'inputs':sources},indent=2)+'\n','utf8');raise
 report['scope']='PL00 기본/포스 새 호버10참조/50층. 기존5공유스트림과 고정은행·모든비대상보존. 대상 저장타일은 검증된4096B 버퍼내20→32; 디코더·EXE·외부항목 변경없음. 다리는 layer8이며 가능한 호버 조건은 bit8 포함이다. 미술/원코드/실기 별도.'
 report['input_layers']=sources;report['parent_arc']=parent.relative_to(ROOT).as_posix();report['packer_source_sha256']=sha((U/'pack_native.py').read_bytes())
 (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 if not args.probe:
  (out/'PL00_U.ARC').write_bytes(result);a=Archive(result)
  for n in p.REFS:helper.grid([(f'hover {n}',[('idle',a.composite(0)[0]),('new basic with legs',a.composite(n,8)[0]),('Fourth idle',a.composite(0,15)[0]),('new Fourth',a.composite(n,15)[0])])],out/f'readback_{n}.png',6)
 print(json.dumps({'after':sha(result),'written_arc':not args.probe,'slack':report['composition_slack'],'packing':report['packing']}))
if __name__=='__main__':main()
