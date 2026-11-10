"""다음 Ultimate 서서사격/특수 잔여를 부모 자원에서 읽기만 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
REFS=(85,86,88,89,90,91,95,96,97,98,99)
def shift(z,dx,dy=0):
 out=np.zeros_like(z);y,x=np.nonzero(z);need(np.all((x+dx>=0)&(x+dx<384)&(y+dy>=0)&(y+dy<384)),'이동경계');out[y+dy,x+dx]=z[y,x];return out
def main():
 parent=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC';a=Archive(parent.read_bytes());out=N/'ultimate_special_review01';out.mkdir(exist_ok=False);rows=[];meta=[]
 for n in REFS:
  rows.append((str(n),[('before idle',a.composite(0,15)[0]),('before current',a.composite(n,15)[0]),('after idle',a.composite(0)[0]),('after current',a.composite(n)[0])]))
  meta.append({'ref':n,'stream_offset':a.banks[0]['frames'][n]['offset'],'tile_count':a.banks[0]['frames'][n]['tile_count'],'layers':{str(pb):{'opaque':int((a.layer(n,pb)[0]>0).sum()),'sha256':sha(a.layer(n,pb)[0].tobytes())}for pb in(0,5,6,7,8)}})
 for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',6)
 pairs=[]
 for sn,tn,dx in((85,86,0),(89,88,0),(90,91,0),(95,96,1),(98,99,1)):
  pairs.append({'source':sn,'target':tn,'dx':dx,'layers':{str(pb):{'changed_cells':int((shift(a.layer(sn,pb)[0],dx)!=a.layer(tn,pb)[0]).sum()),'changed_alpha_cells':int(((shift(a.layer(sn,pb)[0],dx)>0)!=(a.layer(tn,pb)[0]>0)).sum())}for pb in(0,5,6,7,8)}})
 write(out/'report.json',{'source':parent.relative_to(ROOT).as_posix(),'source_sha256':digest(parent),'refs':list(REFS),'frames':meta,'relation_probes':pairs,'scope':'다음미술잔여의 읽기 비교. 위평행이동은검사한가설이며changed_cells0인층만exact로취급. 원화생성/수정/패킹/정책결정/실기없음. 판이만들어진것과직접열람은별도.','game_files_written':False});print(json.dumps({'sheets':4,'pairs':pairs}))
if __name__=='__main__':main()
