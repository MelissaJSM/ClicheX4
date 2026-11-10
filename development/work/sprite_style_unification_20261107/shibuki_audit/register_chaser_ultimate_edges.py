"""170 새 샌들 모듈1px 강체정합과 공동 외곽1표본을 별도 후보에 기록."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
from inspect_chaser_sources import shifted
def main():
    s=H/'chaser_ultimate_common01';d=H/'chaser_ultimate_common02';need(not d.exists(),'새 정합후보');d.mkdir();a=Archive((H/'prepared_standing_fire_ultimate01/PL02_U.ARC').read_bytes());yy,xx=np.indices((384,384));rows=[]
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words],np.int32);back=np.r_[0,1+((rgb[1:16,None]-rgb[None,17:32])**2).sum(2).argmin(1)].astype('uint8')
    for n in(162,166,170,174):
        before=np.array(Image.open(s/f'before_{n:03}_indices.png'));after=np.array(Image.open(s/f'after_{n:03}_indices.png'));changes=[]
        if n==170:
            need(after[176,171]==15 and before[176,171]==0,'外곽 표본 기대');before[176,171]=back[15];changes.append({'type':'new_after_outline_donor','xy':[11,16],'source_palette':0,'source_index':15,'before_index':int(back[15]),'reason':'새후폼 옷단 외곽1셀이 재킷 바깥으로남아 동일새외곽을 재킷에도 등록. 옛몸사용/선임의추가없음.'})
            for form,z in(('before',before),('after',after)):
                mask=(yy>=176)&(xx>=162)&(xx<=170)&(z>0);part=np.where(mask,z,0);z[mask]=0;moving=shifted(part,-1);overlap=(moving>0)&(z>0)
                changes.append({'type':'new_ankle_sandal_module','form':form,'source_region_world':[2,16,10,22],'translation':[0,-1],'source_pixels':int(mask.sum()),'overlap_occluded_pixels':int(overlap.sum()),'overlap_rows':[[int(x)-160,int(y)-160,int(z[y,x]),int(moving[y,x])]for y,x in zip(*np.nonzero(overlap))],'reason':'무릎/머리 고정, 새발목·샌들 전체를1px위로 강체등록해 원발바닥21에정합. 겹침은 관절접속 의미영역으로별도기록, 압축용도트삭제아님.'})
                z[moving>0]=moving[moving>0]
        over=np.where(same_rgba(a,before,after),0,before).astype('uint8');layers={0:after,5:over,**{b:np.zeros_like(after)for b in(6,7,8)}};need(not np.any((after>0)&(before==0)),'후폼 바깥 누출');need(compose(a,layers,15).tobytes()==a.rgba(before,16).tobytes(),'재킷source exact')
        for form,z,mask,pal in [('before',before,15,16),('after',after,0,0)]:
            need(label(z>0,np.ones((3,3)))[1]==1,'관절분리');Image.fromarray(z).save(d/f'{form}_{n:03}_indices.png');compose(a,layers,mask).save(d/f'{form}_{n:03}.png')
            if n==170:need(metrics(a.rgba(z,pal))['bbox'][3]==21,'원발바닥21')
        for b,z in layers.items():Image.fromarray(z).save(d/f'{n:03}_bank{b}_indices.png')
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        rows.append({'ref':n,'registrations':changes,'full_before_exact':True,'outside_before':0,'metrics':{form:metrics(a.rgba(z,pal))for form,z,pal in [('before',before,16),('after',after,0)]}})
    for form,mask in [('before',15),('after',0)]:
        for i,refs in enumerate(((162,166),(170,174))):
            pics=[]
            for n in refs:pics.extend([(f'{n} common draft',Image.open(s/f'{form}_{n:03}.png')),(f'{n} registered',Image.open(d/f'{form}_{n:03}.png'))])
            page(pics,a.composite(0,mask)[0],d/f'{form}_comparison_{i:02}.png',cols=2,scale=5)
    write(d/'report.json',{'source_report_sha256':sha((s/'report.json').read_bytes()),'parent_sha256':sha(a.data),'rows':rows,'common_masks_source':s.relative_to(ROOT).as_posix(),'body_scaled':False,'old_art_copied':False,'arc_written':False,'runtime_vehicle_contacts_verified':False});print(json.dumps(rows))
if __name__=='__main__':main()
