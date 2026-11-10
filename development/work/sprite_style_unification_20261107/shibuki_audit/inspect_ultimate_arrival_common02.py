"""135 보류와138/139 반려를 제외한 세 자세의 공통부 조사판. 픽셀 편집 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from inspect_ultimate_hurt_common import grid

def main():
    d=H/'ultimate_arrival_common_inspection02';need(not d.exists(),'Fresh inspection');d.mkdir();rows=[]
    for n,folder in((133,'ultimate_arrival_native01'),(136,'ultimate_arrival_separate_native01'),(137,'ultimate_arrival_native02')):
        s=H/folder;images=[Image.open(s/f'{f}_{n:03}.png').convert('RGBA')for f in('before','after')];grid(images,d/f'{n:03}_grid.png',[f'{n} new jacket',f'{n} new swimsuit'])
        b=np.array(Image.open(s/f'before_{n:03}_indices.png'));a=np.array(Image.open(s/f'after_{n:03}_indices.png'));m=(a>0)&(b==0)
        rows.append({'ref':n,'source_folder':folder,'source_files':{f:sha((s/f'{f}_{n:03}_indices.png').read_bytes())for f in('before','after')},'after_alpha_outside_before':[[int(x)-160,int(y)-160,int(a[y,x])]for y,x in zip(*np.nonzero(m))],'total_outside':int(m.sum())})
    write(d/'report.json',{'rows':rows,'excluded_unaccepted_refs':[135,138,139],'purpose':'확정 반려/보류 자세를 전체 수용판에 섞지 않고 다른 새 세 자세의 공통부만 조사.','art_changed':False,'arc_changed':False});print(json.dumps([{'ref':r['ref'],'outside':r['total_outside']}for r in rows]))
if __name__=='__main__':main()
