"""같은 포즈의 피부/신발만 원화 행 내부에서 기본 다리 폭으로 정합한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper
from prepare_fourth_guides import source
from prepare_wall_joint_layers import spans
def main():
    a=Archive((D.parent/'base_run_repaint/packed_joint_v2/PL00_U.ARC').read_bytes());plan=json.loads((D/'inputs.json').read_text('utf8'));out=D/'fourth_leg_width_probe_v2';out.mkdir(exist_ok=True);rows=[];reports=[];Y,X=np.indices((384,384));yy=Y-160;xx=X-160
    for n in range(55,67,2):
        p=next(q for q in plan['frames']if q['ref']==n);ex,ey=map(int,p['eye_world']);b=np.array(Image.open(source(n)));f=np.array(Image.open(D/'fourth_contacts_v1'/f'fourth_{n:03}.png'));t=f.copy();start=max(10,ey+17)
        skin=np.isin(f,[10,11,12,13])&(yy>=start);shoes=np.isin(f,[5,6])&(yy>=12);seed=skin|shoes
        mask=binary_dilation(seed,structure=np.ones((3,3)),iterations=1)&np.isin(f,[1,2,5,6,10,11,12,13])&(yy>=start)
        t[mask]=0;links=[];rejected=[]
        for y in range(160+start,384):
            source_spans=spans(mask[y]);destination=spans(b[y]>0)
            for dst in destination:
                if not source_spans:rejected.append([y-160,int(dst[0]-160),int(dst[-1]-160)]);continue
                src=min(source_spans,key=lambda s:abs(float(s.mean()-dst.mean())))
                if abs(float(src.mean()-dst.mean()))>5:rejected.append([y-160,int(dst[0]-160),int(dst[-1]-160)]);continue
                samples=np.rint(np.linspace(0,len(src)-1,len(dst))).astype(int);t[y,dst]=f[y,src[samples]];links.extend([[int(x-160),y-160,int(sx-160),int(f[y,sx])]for x,sx in zip(dst,src[samples])])
        # Pixels rejected from the leg-material mapping remain authored cloth,
        # not invented skin. This is a review probe, not a publishable target.
        t[mask&(t==0)&(f>0)&(b>0)]=f[mask&(t==0)&(f>0)&(b>0)]
        Image.fromarray(t).save(out/f'fourth_{n:03}.png');full=np.where(t,t,b).astype(np.uint8)
        rows.append((f'wall {n}',[('새 기본 원화',a.rgba(b)),('포스 자연 원화',a.rgba(f,16)),('피부/신발 동일 행 정합',a.rgba(full,16))]));reports.append({'ref':n,'source_links':links,'rejected_rows':rejected,'changed_pixels':int(np.count_nonzero(t!=f))})
    for i in range(0,6,3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',7)
    write(out/'report.json',{'ready_to_apply':False,'scope':'하체 폭 시험. 10행 아래 분리된 종아리/신발만. 같은 원화/높이/다리 안에서만 샘플. 옛 그림·단색 채움 없음.','frames':reports});print(json.dumps({'out':str(out),'changes':{r['ref']:r['changed_pixels']for r in reports},'rejected':{r['ref']:r['rejected_rows']for r in reports}}))
if __name__=='__main__':main()
