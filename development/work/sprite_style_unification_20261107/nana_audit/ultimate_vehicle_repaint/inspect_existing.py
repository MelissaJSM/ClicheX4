"""얼티밋 탑승13의 실제5층 공유·평행이동과 고유4자세를 읽기 조사한다."""
from pathlib import Path
import sys,json
import numpy as np
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,helper,need
from src.psx_player import composition_frame,bank_offsets
from scripts.prepare_shibuki_ultimate_production import records
P=N/'ultimate_recoil_repaint/packed_recoil_candidate_v1/PL02_U.ARC'
KEYS=(162,166,170,174);PBS=(0,5,6,7,8)
def main():
 need(digest(P)=='ce61617f541fd59a5a3ab0b26bba6ce88cc7740bf5f9d4719c9acb129783c8d0','동결부모');a=Archive(P.read_bytes());out=D/'existing_v1';out.mkdir(exist_ok=False);refs=list(range(162,175));frames=[]
 for n in refs:
  group=162 if n<166 else 166 if n<170 else 170 if n<174 else 174;layers={};f=a.banks[0]['frames'][n]
  for pb in PBS:
   z=a.layer(n,pb)[0];source=a.layer(group,pb)[0];translation=[]
   for dy in range(-4,5):
    for dx in range(-2,3):
     if np.array_equal(z,np.roll(np.roll(source,dy,0),dx,1)):translation.append([dx,dy])
   rr=records(a.c,pb,n);owners=[i for i in range(composition_frame(a.c,pb,0)['bank_frame_count'])if records(a.c,pb,i)==rr];layers[str(pb)]={'sha256':sha(z.tobytes()),'opaque':int((z>0).sum()),'translations_from_group':translation,'identical_record_refs':owners}
  frames.append({'ref':n,'source_key':group,'offset':f['offset'],'tile_count':f['tile_count'],'raw_owners':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],'layers':layers,'rgba_hashes':{str(mask):sha(a.composite(n,mask)[0].tobytes())for mask in(0,15)}})
 for n in KEYS:
  helper.grid([(f'ride{n}',[('before idle',a.composite(0,15)[0]),('before old',a.composite(n,15)[0]),('after idle',a.composite(0)[0]),('after old',a.composite(n)[0])])],out/f'comparison_{n}.png',6)
 write(out/'report.json',{'parent_arc':P.relative_to(ROOT).as_posix(),'parent_sha256':digest(P),'refs':refs,'source_keys':list(KEYS),'frames':frames,'runtime_verified':False,'scope':'얼티밋 탑승 실제5층·공유의 읽기조사. 새그림/패킹/실기완료 아님. 기본형과의 동작별명 관계를 자동 가정하지 않는다.'});print(json.dumps({'report':str(out/'report.json'),'groups':len({q['offset']for q in frames}),'layer0_translations':{q['ref']:q['layers']['0']['translations_from_group']for q in frames}}))
if __name__=='__main__':main()
