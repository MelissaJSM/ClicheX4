"""고정등록 두 의상의 하체 분지 차이를 읽고 미정합 원인을 공개한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
def spans(z):
    x=np.flatnonzero(z)
    return []if not len(x)else np.split(x,np.flatnonzero(np.diff(x)>1)+1)
def main():
    out=D/'geometry_probe_v1';out.mkdir(exist_ok=False)
    a=Archive((N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC').read_bytes())
    rec=[];views=[]
    for n,lo in((106,6),(110,4),(233,3),(234,3)):
        src=D/('first_registered_v1'if n<200 else'extra_registered_v1')
        b=np.array(Image.open(src/f'base_{n:03}_registered_indices.png'))
        f=np.array(Image.open(src/f'fourth_{n:03}_registered_indices.png'))
        full=np.where(f,f,b).astype(np.uint8);lower=np.indices(b.shape)[0]>=lo+160
        rr=[]
        for y in range(160+lo,190):
            if not np.any((b[y]>0)&(f[y]==0)):continue
            rr.append({'y':y-160,'base':[[int(x[0])-160,int(x[-1])-159]for x in spans(b[y]>0)],
                       'fourth':[[int(x[0])-160,int(x[-1])-159]for x in spans(f[y]>0)],
                       'base_exposed_x':[int(x)-160 for x in np.flatnonzero((b[y]>0)&(f[y]==0))]})
        rec.append({'ref':n,'lower_from_y':lo,'lower_exposed_base_pixels':int(((b>0)&(f==0)&lower).sum()),'rows':rr})
        views.append((f'{n} diagnostic',[('new base',a.rgba(b)),('new Fourth source',a.rgba(f,16)),('unregistered actual overlay',a.rgba(full,16))]))
    helper.grid(views[:2],out/'comparison_1.png',7);helper.grid(views[2:],out/'comparison_2.png',7)
    write(out/'report.json',{'scope':'진단 합성. 드러난 기본 부츠/소매를 해결하기 전이며 최종안이 아님.','frames':rec,'native_packed':False})
    print(json.dumps(rec))
if __name__=='__main__':main()
