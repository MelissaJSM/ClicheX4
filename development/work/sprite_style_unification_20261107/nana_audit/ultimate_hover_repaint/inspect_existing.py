"""호버10의 실제 층/공유와 원순서를 읽는다. 새 그림·자원은 쓰지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,helper,need
from src.psx_player import composition_frame
from scripts.prepare_shibuki_ultimate_production import records
P=N/'ultimate_special_finish_repaint/packed_special_candidate_v1/PL02_U.ARC'
def main():
 need(digest(P)=='56a3aeb489229d85bb72205bd14f866b4444ff5daa8e1bc7f91c82e9b3c46fc0','동결부모');a=Archive(P.read_bytes());out=D/'existing_v1';out.mkdir(exist_ok=False);refs=list(range(221,231));frames=[];PBS=(0,5,6,7,8);rows=[]
 for n in refs:
  f=a.banks[0]['frames'][n];layers={}
  for pb in PBS:
   z,parts=a.layer(n,pb);Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png');rr=records(a.c,pb,n);layers[str(pb)]={'sha256':sha(z.tobytes()),'opaque':int((z>0).sum()),'records_hex':rr.hex(),'parts':parts,'identical_records_refs':[i for i in range(composition_frame(a.c,pb,0)['bank_frame_count'])if records(a.c,pb,i)==rr]}
  frames.append({'ref':n,'offset':f['offset'],'tile_count':f['tile_count'],'raw_owners':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],'layers':layers,'rgba_hashes':{str(mask):sha(a.composite(n,mask)[0].tobytes())for mask in(0,15)}});rows.append((str(n),[('idle mask15',a.composite(0,15)[0]),('hover mask15',a.composite(n,15)[0]),('hover mask0',a.composite(n)[0]),('layer5 only',a.rgba(a.layer(n,5)[0],16))]))
 for i in range(0,10,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 m=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));anim=m['characters']['nana']['forms']['ultimate_before']['animations'];animations=[q for q in anim if any(s['frame_ref']in refs for s in q['steps'])]
 write(out/'report.json',{'parent_arc':P.relative_to(ROOT).as_posix(),'parent_sha256':digest(P),'refs':refs,'frames':frames,'animations':animations,'runtime_verified':False,'scope':'현재 호버10참조의 층/공유 읽기조사. 출력이미지는 검토용이며 새 그림/실기 완료가 아니다.'});print(json.dumps({'groups':len({q['offset']for q in frames}),'layers':{q['ref']:{k:v['opaque']for k,v in q['layers'].items()}for q in frames},'animations':[q['id']for q in animations]}))
if __name__=='__main__':main()
