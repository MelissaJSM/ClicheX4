"""새 포스 자연스러운 발을 기준으로 기본 공통 실루엣을 제한한 비교."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive,sha,write,helper
from PIL import Image
import numpy as np
D=Path(__file__).parent
def main():
    out=D/'common_silhouette_probe';out.mkdir(exist_ok=True);a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'));yy=np.indices((384,384))[0]-160;reports=[]
    for page in range(4):
        rows=[]
        for n in range(1+page*8,9+page*8,2):
            p=next(q for q in plan['frames']if q['ref']==n);ex,ey=p['eye_world_original_registration'];b=np.array(Image.open(D/'cycle_registered_v1'/f'run_{n:03}.png'));f=np.array(Image.open(D/'fourth_body_scale'/f'run_{n:03}.png'));cut=(yy>=ey+17)&(f==0);base=b.copy();base[cut]=0;full=np.where(f,f,base)
            Image.fromarray(base).save(out/f'run_{n:03}.png');Image.fromarray(full).save(out/f'fourth_{n:03}.png');rows.append((f'ref {n}',[('새 기본',a.rgba(b)),('공통 경계 기본',a.rgba(base)),('원화 발 유지 포스',a.rgba(full,16))]));reports.append({'ref':n,'removed':int(np.count_nonzero((b>0)&cut)),'foot_max_y_before':int(np.nonzero(b)[0].max()-160),'foot_max_y_after':int(np.nonzero(base)[0].max()-160)})
        helper.grid(rows,out/f'comparison_{page+1}.png',6)
    write(out/'report.json',{'ready_to_apply':False,'method':'검토만: 새 기본의 하체가 새 포스 바깥으로 나간 알파를 제거. 양쪽 원화 색변경/채움 없음. 끝점과 외곽 읽힘을 검수해야 함.','frames':reports})
if __name__=='__main__':main()
