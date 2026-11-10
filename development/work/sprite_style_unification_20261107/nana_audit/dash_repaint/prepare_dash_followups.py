"""대시 후속 원화와 낮은 대시 발목 국소 교정용 입력 추출."""
from pathlib import Path
import sys,json
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N),str(N/'native_restore')]
from preview_restore import Archive,sha,need
from prepare_air_inputs import page
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());need(sha(a.data)==p['parent_arc_sha256'],'Parent')
    page(a,[(f'POSE {n}',n,0)for n in(69,75,77,81)],D/'basic_second4.png')
    page(a,[(f'POSE {n}',n,0)for n in(83,94)],D/'basic_last2.png')
    a.composite(71)[0].crop((128,144,192,192)).resize((1024,768),Image.Resampling.NEAREST).save(D/'dash71_original_pose.png')
if __name__=='__main__':main()
