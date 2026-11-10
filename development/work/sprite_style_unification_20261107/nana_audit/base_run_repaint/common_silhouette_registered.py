"""시험: 같은 행/다리의 새 기본 원화 외곽을 공동 알파에 재등록한다."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive,sha,write,helper,need
from PIL import Image
import numpy as np
D=Path(__file__).parent
def spans(row):
    points=np.flatnonzero(row)
    return np.split(points,np.flatnonzero(np.diff(points)>1)+1) if len(points) else []
def main():
    out=D/'common_silhouette_registered_v2';out.mkdir(exist_ok=True)
    a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'));reports=[]
    for page in range(4):
        rows=[]
        for n in range(1+page*8,9+page*8,2):
            p=next(q for q in plan['frames']if q['ref']==n);ex,ey=p['eye_world_original_registration'];b=np.array(Image.open(D/'cycle_registered_v1'/f'run_{n:03}.png'));f=np.array(Image.open(D/'fourth_contacts_v1'/f'run_{n:03}.png'));target=b.copy();links=[];removed=[]
            for y in range(160+ey+17,384):
                for segment in spans(b[y]>0):
                    dest=segment[f[y,segment]>0]
                    target[y,segment]=0
                    if not len(dest):
                        removed.append([int(y),int(segment[0]),int(segment[-1])]);continue
                    samples=np.rint((dest-dest[0])*(len(segment)-1)/max(1,dest[-1]-dest[0])).astype(int)
                    target[y,dest]=b[y,segment[samples]]
                    links.extend([[int(x),int(y),int(sx),int(y),int(b[y,sx])]for x,sx in zip(dest,segment[samples])])
            full=np.where(f,f,target)
            Image.fromarray(target).save(out/f'run_{n:03}.png');Image.fromarray(full).save(out/f'fourth_{n:03}.png')
            rows.append((f'ref {n}',[('새 기본 원화',a.rgba(b)),('공동 외곽 재등록',a.rgba(target)),('포스 원화 자연스러운 발',a.rgba(full,16))]))
            floor=int(np.nonzero(b)[0].max());reports.append({'ref':n,'source_links':links,'removed_entire_spans':removed,'source_sha':sha(b.tobytes()),'target_sha':sha(target.tobytes()),'floor':floor-160,'floor_x_before':(np.flatnonzero(b[floor]>0)-160).tolist(),'floor_x_after':(np.flatnonzero(target[floor]>0)-160).tolist()})
        helper.grid(rows,out/f'comparison_{page+1}.png',6)
    write(out/'report.json',{'ready_to_apply':False,'scope':'기본·포스 공동 외곽 시험. 같은 y의 같은 원화 다리 span만 대응, 다른 재질 채움 없음. 실기 없음.','frames':reports})
if __name__=='__main__':main()
