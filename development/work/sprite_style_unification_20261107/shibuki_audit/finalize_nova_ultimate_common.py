"""후폼의 새 머리/팔 경계 한 셀을 동색 공통 외곽으로 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
def main():
    d=H/'nova_ultimate_common02';need(not d.exists(),'새 출력');d.mkdir();a=Archive((H/'prepared_chaser_ultimate01/PL02_U.ARC').read_bytes());rows=[];pics={'before':[],'after':[]}
    for n in (213,215):
        s=H/'nova_ultimate_common01';before=np.array(Image.open(s/f'before_{n:03}_indices.png'));after=np.array(Image.open(s/f'after_{n:03}_indices.png'));points=[]
        if n==215:
            x,y=8,6;i=int(after[160+y,160+x]);need(i==8 and before[160+y,160+x]==0,'예상 새 외곽');matches=[j for j in range(1,16)if a.words[16+j]==a.words[i]];need(matches,'공통 동색 필요');j=matches[0];before[160+y,160+x]=j;points.append({'xy':[x,y],'source':'nova_ultimate_common01/after_215_indices.png','source_index':i,'before_index':j,'RGB_exact':True,'meaning':'새 후폼 팔 뒤 머리/그늘 외곽 1셀을 같은 색으로 재킷폼에도 보존'})
        over=np.where(same_rgba(a,before,after),0,before).astype('uint8');layers={0:after,5:over,**{b:np.zeros_like(after)for b in(6,7,8)}}
        need(not((after>0)&(before==0)).any(),'후폼 외곽 누출');need(compose(a,layers,15).tobytes()==a.rgba(before,16).tobytes(),'전폼 exact')
        for b,z in layers.items():Image.fromarray(z).save(d/f'{n:03}_bank{b}_indices.png')
        for form,z,m,pal in [('before',before,15,16),('after',after,0,0)]:
            Image.fromarray(z).save(d/f'{form}_{n:03}_indices.png');im=compose(a,layers,m);im.save(d/f'{form}_{n:03}.png');pics[form].extend([(f'{n} 기존',a.composite(n,m)[0]),(f'{n} 새 준비',im)])
        cc=[int(label(np.array(compose(a,layers,m))[:,:,3]>0,np.ones((3,3)))[1])for m in range(16)];need(cc==[1]*16,'부분 관절 연결');page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        rows.append({'ref':n,'outline_registrations':points,'partial_component_counts':cc,'before_exact':True,'after_exact':True,'layers':{str(b):sha(z.tobytes())for b,z in layers.items()},'metrics':{form:metrics(compose(a,layers,m))for form,m in [('before',15),('after',0)]}})
    for form,m in [('before',15),('after',0)]:page(pics[form],a.composite(0,m)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    write(d/'report.json',{'parent_sha256':sha(a.data),'source_common_sha256':sha((H/'nova_ultimate_common01/report.json').read_bytes()),'rows':rows,'arc_written':False,'policy':'새 원화만 사용. 종아리 국소/공통 머리·사지 후 마지막 같은 색 외곽1셀을 보존. 원작 몸체 축소·옛머리 복사 없음.'});print(json.dumps(rows))
if __name__=='__main__':main()
