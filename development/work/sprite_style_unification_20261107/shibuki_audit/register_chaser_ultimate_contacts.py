"""Ultimate 첫체이서의 강체 원점/발 모듈과 금색안경 표본을 등록."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from inspect_chaser_sources import shifted

def main():
    s=H/'chaser_ultimate_native01';d=H/'chaser_ultimate_contacts01';need(not d.exists(),'새 정합 출력');a=Archive((H/'prepared_standing_fire_ultimate01/PL02_U.ARC').read_bytes());d.mkdir();rows=[];yy,xx=np.indices((384,384))
    for form,mask,pal in(('before',15,16),('after',0,0)):
        pics=[]
        for n in(162,166):
            source=np.array(Image.open(s/f'{form}_{n:03}_indices.png'));z=source.copy();sample=np.array(Image.open(s/f'{form}_{n:03}_sample_rgba.png'));gold=[]
            # 얼굴보다 높은 안경 ROI의 실제 금색 원화 표본만 기존 금색7로 등록.
            eye_cut=150 if n==162 else 154
            for y,x in np.argwhere((source>0)&(yy<eye_cut)&(yy>130)&(xx>=148)&(xx<=164)):
                r,g,b,alpha=map(int,sample[y-112,x-112])
                if g>=140 and r-g>=10 and g-b>=25 and z[y,x]!=7:
                    gold.append({'xy':[int(x-160),int(y-160)],'source_RGBA':[r,g,b,alpha],'nearest_index':int(z[y,x]),'semantic_index':7});z[y,x]=7
            if n==166:
                z=shifted(z,-1);move={'whole_sprite_translation':[0,-1],'reason':'고정셀에서 눈·귀/발이 함께1px낮음. 전신강체평행이동이며 스케일/관절변형없음.'}
            else:
                module=(yy>=170)&(xx>=163)&(xx<=171)&(z>0);part=np.where(module,z,0);q=z.copy();q[module]=0;shift=shifted(part,1);need(not np.any((shift>0)&(q>0)),'발모듈 겹침');q[shift>0]=shift[shift>0];need(np.count_nonzero(q)==np.count_nonzero(z),'발도트 소실');z=q;move={'foot_module_translation':[0,1],'source_region_world':[3,10,11,18],'source_pixels':int(module.sum()),'reason':'162 발끝만1px높아 새하퇴/샌들 모듈을1px 아래 등록. 옛다리 덮기·행늘림없음.'}
            labs,count=label(z>0,np.ones((3,3)));need(count==1,'새 연결 분리');im=a.rgba(z,pal);need(metrics(im)['bbox'][3]==17,'원발높이 불일치')
            Image.fromarray(z).save(d/f'{form}_{n:03}_indices.png');im.save(d/f'{form}_{n:03}.png');pics.extend([(f'{n} 고정셀 첫등록',a.rgba(source,pal)),(f'{n} 접점정합',im)])
            rows.append({'form':form,'ref':n,'movement':move,'gold_source_samples':gold,'original_metrics':metrics(a.composite(n,mask)[0]),'source_metrics':metrics(a.rgba(source,pal)),'registered_metrics':metrics(im),'components':[int((labs>0).sum())],'indices_sha256':sha(z.tobytes()),'outside_gold_and_movement_unchanged':True})
        page(pics,a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    write(d/'report.json',{'parent_sha256':sha(a.data),'source_report':{'path':(s/'report.json').relative_to(ROOT).as_posix(),'sha256':sha((s/'report.json').read_bytes())},'rows':rows,'body_scale_changed':False,'old_coarse_art_copied':False,'arc_written':False,'runtime_verified':False,'limits':['양폼 공통머리/사지·부분층은 후속이다.','피부손의 실제 차량손잡이 접촉과 원발판 실기는 별도다.']});print(json.dumps(rows))
if __name__=='__main__':main()
