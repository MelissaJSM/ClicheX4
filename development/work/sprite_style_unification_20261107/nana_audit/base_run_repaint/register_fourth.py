"""새 포스 원화의 원점 등록과 기본층 겹침을 먼저 계측한다. 최종 패치 아님."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from register_cycle import PAGES,body_register
from register_page import crop_cell
from preview_restore import Archive,sha,digest,write,need,helper
from PIL import Image
from scipy.ndimage import distance_transform_edt
import numpy as np
D=Path(__file__).parent
def main():
    out=D/'fourth_registered_v1';out.mkdir(exist_ok=True)
    a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'))
    palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32)
    reports=[];rows=[]
    for page,(_,refs) in enumerate(PAGES,1):
        path=D/f'fourth_page{page}_v1/generated.png';im=Image.open(path).convert('RGBA')
        for cell,n in enumerate(refs):
            p=next(q for q in plan['frames']if q['ref']==n);crop,box=crop_cell(im,cell)
            full,r=body_register(crop,p,palette);base=np.array(Image.open(D/'cycle_registered_v1'/f'run_{n:03}.png'))
            miss=(base>0)&(full==0);dist=distance_transform_edt(full==0)
            mixed=np.where(full,full,base)
            Image.fromarray(full).save(out/f'run_{n:03}.png')
            a.rgba(full,16).save(out/f'run_{n:03}_rgba.png')
            Image.fromarray(miss.astype(np.uint8)).save(out/f'missing_{n:03}.png')
            rows.append((f'ref {n}',[('포스 대기',a.composite(0,15)[0]),('새 기본',a.rgba(base)),('새 포스 원화 등록',a.rgba(full,16)),('기본 잔여 포함',a.rgba(mixed,16))]))
            reports.append({'ref':n,'source':str(path.relative_to(ROOT)),'source_sha256':digest(path),'crop':box,**r,'missing_base_pixels':int(miss.sum()),'missing_distance_max':float(dist[miss].max(initial=0)),'target_sha256':sha(full.tobytes())})
        helper.grid(rows[-4:],out/f'comparison_{page}.png',5)
    write(out/'registration.json',{'passed_registration':True,'ready_to_pack':False,'frames':reports,'method':'원화 전체 고정CLUT area vote 및 눈/발 정합. 기본 밖 결손은 아직 메우지 않음.','source_arc_sha256':sha(a.data),'runtime_verified':False})
    print(json.dumps([{'ref':r['ref'],'missing':r['missing_base_pixels'],'distance':r['missing_distance_max']} for r in reports]))
if __name__=='__main__':main()
