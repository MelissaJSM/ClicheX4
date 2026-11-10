"""새 비사격 공중11몸체의 연결 순서/출처/접지를 검토용으로 수집한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,need,write,helper
def source(n):
    folder='basic_registered_v2'if n in(33,39,47,51)else('basic_landing_registered_v5'if n in(45,49,53)else'basic_middle_registered_v2')
    return D/folder
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/'basic_sequence_review_v1';out.mkdir(exist_ok=True);manifest=[];Y,X=np.indices((384,384))
    for i,refs in enumerate((list(range(33,41,2)),list(range(41,49,2)),[49,51,53])):
        rows=[]
        for n in refs:
            idx=np.array(Image.open(source(n)/f'base_{n:03}.png'));reg=json.loads((source(n)/'registration.json').read_text('utf8'));q=next(r for r in reg['frames']if r['ref']==n);ex,ey=q['target_eye'];need(idx[160+ey,160+ex]==14,'Eye moved');need(label(idx>0,np.ones((3,3)))[1]==1,'Detached alpha')
            feet=[]
            for side in(X<160,X>=160):
                y,x=np.nonzero((idx>0)&side);fy=int(y.max());feet.append({'y':fy-160,'x':(x[y==fy]-160).tolist()})
            if n in(49,51,53):need(all(f['y']==22 for f in feet),'Landing contact')
            manifest.append({'ref':n,'indexed_path':(source(n)/f'base_{n:03}.png').relative_to(ROOT).as_posix(),'indexed_sha256':sha(idx.tobytes()),'source_art_sha256':reg['source_art_sha256'],
                             'eye':[ex,ey],'feet':feet,'alpha_components_8':1,'old_art_pixels_used':0})
            rows.append((f'air {n}',[('대기 기준',a.composite(0)[0]),('현재',a.composite(n)[0]),('새 전신',a.rgba(idx))]))
        helper.grid(rows,out/f'sequence_{i+1}.png',6)
    write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':manifest,'native_tables':p['animations_from_hash_bound_prior_exe'],
       'scope':'11개 비사격 새 몸체의 정적 연결 순서.3착지 모두 양발y22, 눈 원점 보존. 사격/포스/패킹은 별도 미완료.','native_packed':False,'runtime_verified':False})
    print(json.dumps({'refs':[q['ref']for q in manifest],'landing':{q['ref']:q['feet']for q in manifest if q['ref']in(49,51,53)}}))
if __name__=='__main__':main()
