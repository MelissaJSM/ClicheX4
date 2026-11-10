"""등장 전후 공통관절 후보를 정하는 원점 격자. 원화·ARC 수정 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from inspect_ultimate_hurt_common import grid

def main():
    d=H/'ultimate_arrival_common_inspection01';need(not d.exists(),'Fresh inspection');d.mkdir();s=H/'ultimate_arrival_native01';rows=[]
    for n in(133,135):
        images=[Image.open(s/f'{f}_{n:03}.png').convert('RGBA')for f in('before','after')];grid(images,d/f'{n:03}_grid.png',[f'{n} new jacket',f'{n} new swimsuit'])
        before=np.array(Image.open(s/f'before_{n:03}_indices.png'));after=np.array(Image.open(s/f'after_{n:03}_indices.png'));outside=(after>0)&(before==0)
        rows.append({'ref':n,'source_files':{f:sha((s/f'{f}_{n:03}_indices.png').read_bytes())for f in('before','after')},'after_alpha_outside_before':[[int(x)-160,int(y)-160,int(after[y,x])]for y,x in zip(*np.nonzero(outside))],'total_outside':int(outside.sum())})
    write(d/'report.json',{'rows':rows,'purpose':'공통머리/사지/관절 의미영역을 실제좌표로 검토.수치차이만으로미술결함확정하지않음.','art_or_arc_changed':False});print(json.dumps([{k:r[k]for k in('ref','total_outside')}for r in rows]))
if __name__=='__main__':main()
