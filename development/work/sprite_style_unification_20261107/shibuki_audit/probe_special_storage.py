"""95/97 새 도트 불변인 타일 공유/순열 압축의 절감량을 조사한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from scripts.export_x_consistency import Archive
from scripts.overhaul_sprites_costume_pack import pack_planes
from src.psx_compress import encode_stream
from pack_shibuki_hurt import raw,repack_fixed_global
from optimize_hurt_tile_storage import optimize
PBS=(0,5,6,7,8)
def main():
 o=H/'standing_special_storage01';need(not o.exists(),'Fresh storage probe');o.mkdir();a=Archive((H/'prepared_hurt_base01/PL00_U.ARC').read_bytes());s=H/'standing_special_layers01';images={n:[crop(np.array(Image.open(s/f'{n:03}_bank{b}_indices.png')))for b in PBS]for n in(95,97)};rows=[];raws={};rrs={}
 for mode,ns in(('separate95',[95]),('separate97',[97]),('joint95_97',[95,97])):
  try:r,rr=pack_planes(bytes(4096),32,[im for n in ns for im in images[n]],set(range(1,32)),[24]*(5*len(ns)))
  except ValueError as e:rows.append({'mode':mode,'fit':False,'error':str(e)});write(o/'progress.json',rows);continue
  nr,mapping,opt=optimize(r,{0,16},steps=6);parts=[[(mapping[t],x,y,fl)for t,x,y,fl in ps]for ps in rr];(o/f'{mode}.raw').write_bytes(nr);rec={'mode':mode,'fit':True,'refs':ns,'optimization':opt,'parts':parts,'raw_sha256':sha(nr),'old_codes':{str(n):len(encode_stream(raw(a,0,n)))for n in ns}};rows.append(rec);write(o/'progress.json',rows);print(json.dumps({'mode':mode,'cost':opt['after'],'saved':opt['saved']}),flush=True)
  if len(ns)==1:raws[ns[0]]=nr;rrs[ns[0]]=parts
  else:
   try:_,gr=repack_fixed_global(a,{95:nr,96:nr,97:nr},{95:32,96:32,97:32});rec['fixed_bank_trial']={'passed':True,'graphics':gr}
   except ValueError as e:rec['fixed_bank_trial']={'passed':False,'error':str(e)}
 if len(raws)==2:
  try:_,gr=repack_fixed_global(a,{95:raws[95],96:raws[95],97:raws[97]},{95:32,96:32,97:32});sep={'passed':True,'graphics':gr}
  except ValueError as e:sep={'passed':False,'error':str(e)}
 else:sep=None
 write(o/'report.json',{'rows':rows,'separate_optimized_trial':sep,'art_indices_unchanged':True,'arc_written':False,'bank_boundary_changed':False});print(json.dumps({'separate':sep,'joint':[r.get('fixed_bank_trial')for r in rows if r['mode']=='joint95_97']}))
if __name__=='__main__':main()
