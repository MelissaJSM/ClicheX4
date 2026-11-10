"""수용 보행 하체를 유지하는 대안을 비교만 한다. 실제 자원 미수정."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive,sha,write,helper
from PIL import Image
import numpy as np
D=Path(__file__).parent
def main():
    out=D/'accepted_lower_alternative';out.mkdir(exist_ok=True);a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'));yy=np.indices((384,384))[0]-160
    report=[]
    for page in range(4):
        rows=[]
        for n in range(1+page*8,9+page*8,2):
            p=next(q for q in plan['frames']if q['ref']==n);ex,ey=p['eye_world_original_registration'];cut=ey+18;lower=yy>=cut
            old=a.layer(n)[0];oldfull=old.copy()
            for pb in(8,5,7,6):v=a.layer(n,pb)[0];oldfull=np.where(v,v,oldfull)
            new=np.array(Image.open(D/'cycle_registered_v1'/f'run_{n:03}.png'));f=np.array(Image.open(D/'fourth_registered_v1'/f'run_{n:03}.png'))
            base=new.copy();base[lower]=old[lower]
            full=np.where(f,f,base);full[lower]=oldfull[lower]
            Image.fromarray(base).save(out/f'run_{n:03}.png');Image.fromarray(full).save(out/f'fourth_{n:03}.png')
            rows.append((f'ref {n}',[('현재 수용 기본/포스',a.composite(n)[0]),('새 기본+수용 하체',a.rgba(base)),('새 포스+수용 하체',a.rgba(full,16))]))
            report.append({'ref':n,'preserved_lower_from_world_y':cut,'basic_lower_exact':True,'fourth_lower_exact':True,'base_sha256':sha(base.tobytes()),'fourth_sha256':sha(full.tobytes())})
        helper.grid(rows,out/f'comparison_{page+1}.png',6)
    write(out/'report.json',{'ready_to_apply':False,'scope':'사용자 수용 보행 하체 보존 대안 비교. 새 기본/포스 원화의 상체는 그대로. 원화 명암 복원은 별도 단계.','frames':report})
if __name__=='__main__':main()
