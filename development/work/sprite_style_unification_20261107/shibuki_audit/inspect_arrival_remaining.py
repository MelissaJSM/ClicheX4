"""승리 후 남은 등장 그림·공유와 원래 일시적 아머 전환을 구분한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from native_pose_pack import sha,need,write
from src.psx_player import composition_frame

def main():
 data=(H/'prepared_victory_ladder01/PL00_U.ARC').read_bytes();need(sha(data)=='02f092d7b0ed67ce1174fd30250b86f73c81b42dbfa08c8c3ca06fc638b89acf','Source changed');a=Archive(data);out=H/'arrival_remaining01';need(not out.exists(),'Output exists');out.mkdir();refs=list(range(126,143));rows=[]
 for n in refs:
  f=a.banks[0]['frames'][n];v=a.layer(n)[0];row=dict(ref=n,shared_gfx=[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],parts={str(b):len(composition_frame(a.c,b,n)['parts'])for b in(0,5,6,7,8)},opaque={str(b):int(np.count_nonzero(a.layer(n,b)[0]))for b in(0,5,6,7,8)})
  row['base_exact_aliases']=[k for k in refs if k!=n and np.array_equal(a.layer(k)[0],v)];rows.append(row)
  for mask,label in((0,'base'),(15,'fourth')):a.composite(n,mask)[0].save(out/f'{label}_{n:03}.png')
 for mask,label in((0,'base'),(15,'fourth')):
  for i in range(0,len(refs),6):page([(f'{n} all mask{mask:X}',a.composite(n,mask)[0])for n in refs[i:i+6]],a.composite(0,mask)[0],out/f'{label}_{i//6:02}.png',cols=3,scale=4)
 meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/art_review/fourth_arrival_native.json').read_text('utf8'))
 write(out/'inventory.json',dict(source_sha256=sha(data),rows=rows,previous_native_armor_proof=meta,note='133..139의 일시적 기본 의상은 원래 아머0 전환이다. 미술 세부 부족과 아머누락을 혼동하지 않는다.141/142는 수용idle 연결 유지.',review_complete=False))
 print(json.dumps(rows))
if __name__=='__main__':main()
