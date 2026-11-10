"""다음 Ultimate 사다리의 현행표시와 수용 기본형 포즈를 읽기만 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
from src.psx_player import composition_frame

def main():
 out=D/'initial_review_v1';out.mkdir(exist_ok=False);p=N/'ultimate_victory_repaint/packed_victory_candidate_v1/PL02_U.ARC';bp=N.parent/'root_nana_ladder/packed_ladder07/PL00_U.ARC';a=Archive(p.read_bytes());b=Archive(bp.read_bytes());need(digest(bp)=='509cc9785cb5eb3dca9f7a8a3fd1d3ea334887a98d3834b9f327266b3c6bbdce','기본동결');rows=[];refs=[143,144,146,149,151,153,154,183,150,155];records=[]
 for n in refs:
  rows.append((f'ladder {n}',[('new base pose',b.composite(n)[0]),('current jacket',a.composite(n,15)[0]),('current after',a.composite(n)[0]),('accepted ultimate idle',a.composite(0,15)[0])]))
  f=a.banks[0]['frames'][n];records.append({'ref':n,'stream':f['offset'],'tile_count':f['tile_count'],'raw_owners':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],'parts':{str(pb):composition_frame(a.c,pb,n)['parts']for pb in(0,5,6,7,8)}})
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',5)
 write(out/'report.json',{'current_ultimate_arc':p.relative_to(ROOT).as_posix(),'current_ultimate_arc_sha256':digest(p),'new_base_arc':bp.relative_to(ROOT).as_posix(),'new_base_arc_sha256':digest(bp),'unique_body_pose_refs':[143,144,146,149,151,153,154,183],'firing_refs':[150,155],'mirrored_refs_to_verify':[145,147,148,152],'frames':records,'scope':'다음제작 우선순위용 읽기비교. 기본형과Ultimate를 동일몸으로 자동복사하지 않음.현재신규원화/패킹/실기없음.','native_packed':False,'runtime_verified':False})
 print(out)
if __name__=='__main__':main()
