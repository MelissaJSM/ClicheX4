"""기존 귀환156..160의 상세 보존 여부를 새 승리 옆에서 별도 검토한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def main():
 out=D/'return_review_v1';out.mkdir(exist_ok=False);p=D/'packed_victory_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());parent=Archive((N/'ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC').read_bytes());rows=[];checks=[]
 for mask in(15,0):
  rows.append((f'return mask{mask}',[('idle',a.composite(0,mask)[0]),('new victory207',a.composite(207,mask)[0]),('current return156',a.composite(156,mask)[0]),('current return157',a.composite(157,mask)[0])]))
  for n in range(156,161):
   im=a.composite(n,mask)[0];need(im.tobytes()==parent.composite(n,mask)[0].tobytes(),'귀환 보존');checks.append({'ref':n,'mask':mask,'rgba_sha256':sha(im.tobytes()),'unchanged':True})
 helper.grid(rows,out/'comparison.png',7)
 hp=ROOT/'work/ver_rin_nana/nana_ultimate_armor/ceremony_v1/generated_first.png';im=Image.open(hp);im.crop((512,0,1024,512)).save(out/'historical156.png')
 write(out/'report.json',{'candidate_arc_sha256':digest(p),'unchanged_return_displays':checks,'historical156':{'path':hp.relative_to(ROOT).as_posix(),'sha256':digest(hp),'crop':[512,0,1024,512]},'scope':'156..160을 새 원화로 집계하지 않고 기존 상세/권총 의미를 비교하는 정적 읽기판. 게임실기는 별도.','art_decision_pending':True,'runtime_verified':False})
if __name__=='__main__':main()
