"""피격의 겹친 다리에서 같은 원화 행의 소량 폭 정합만 시험한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
def spans(mask):
    xx=np.flatnonzero(mask)
    return []if not len(xx)else np.split(xx,np.flatnonzero(np.diff(xx)>1)+1)
def main():
    a=Archive((N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC').read_bytes())
    out=D/'common_legs_probe_v1';out.mkdir(exist_ok=False);records=[];views=[]
    for n,start,xmax,foot in((106,10,2,20),(110,7,1,17),(233,5,5,12),(234,5,2,15)):
        src=D/('first_registered_v1'if n<200 else'extra_registered_v1')
        b=np.array(Image.open(src/f'base_{n:03}_registered_indices.png'));f=np.array(Image.open(src/f'fourth_{n:03}_registered_indices.png'))
        nb,nf=b.copy(),f.copy();region=(Y>=start)&(X<=xmax);links=[];rejected=[]
        for y in range(start+160,190):
            bs,fs=spans((b[y]>0)&region[y]),spans((f[y]>0)&region[y])
            if not bs:continue
            if len(bs)!=len(fs):
                rejected.append({'y':y-160,'reason':'다리 분지 수 불일치','base':[list(map(int,s-160))for s in bs],'fourth':[list(map(int,s-160))for s in fs]});continue
            for sb,sf in zip(bs,fs):
                if np.array_equal(sb,sf):continue
                if abs(float(sb.mean()-sf.mean()))>1.5 or min(len(sb),len(sf))/max(len(sb),len(sf))<.5:
                    rejected.append({'y':y-160,'reason':'이동1.5px/폭비0.5 한도','base':list(map(int,sb-160)),'fourth':list(map(int,sf-160))});continue
                # 맨다리의 실제 외곽을 우선하되 구두 구역은 새기본 부츠의 끝/폭을 보존한다.
                dst=sb if y>=160+foot else sf
                for form,old,new,s in(('base',b,nb,sb),('fourth',f,nf,sf)):
                    if np.array_equal(s,dst):continue
                    samples=s[np.rint(np.linspace(0,len(s)-1,len(dst))).astype(int)]
                    new[y,s]=0;new[y,dst]=old[y,samples]
                    for xx,sx in zip(dst,samples):
                        links.append({'form':form,'world':[int(xx-160),y-160],'source_world':[int(sx-160),y-160],'index':int(old[y,sx])})
        need(np.array_equal(nb[~region],b[~region])and np.array_equal(nf[~region],f[~region]),'상체 변경')
        full=np.where(nf,nf,nb).astype(np.uint8)
        for form,z in(('base',nb),('fourth',nf)):
            Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png')
        a.rgba(full,16).save(out/f'full_{n:03}_rgba.png')
        records.append({'ref':n,'base_source_sha256':sha(b.tobytes()),'fourth_source_sha256':sha(f.tobytes()),
                        'base_sha256':sha(nb.tobytes()),'fourth_sha256':sha(nf.tobytes()),'source_links':links,
                        'rejected_rows':rejected,'remaining_exposed_base_lower':int(((nb>0)&(nf==0)&region).sum()),
                        'components':{'base':int(label(nb>0,np.ones((3,3)))[1]),'fourth':int(label(nf>0,np.ones((3,3)))[1])}})
        views.append((f'{n} common leg test',[('new base source',a.rgba(b)),('base local registration',a.rgba(nb)),('new Fourth source',a.rgba(f,16)),('actual full',a.rgba(full,16))]))
    for k in range(0,4,2):helper.grid(views[k:k+2],out/f'comparison_{k//2+1}.png',6)
    write(out/'manifest.json',{'frames':records,'method':'다리마다 같은 원화 행·동일 분지의 표본만 재등록. 상체/머리 불변. 몸체 일괄채움·색재생성·전신 축척 없음. 거부된 행은 공개하고 원안 보존.',
                             'status':'미술 검토 전 국소 공통외곽 시험안, 부분파츠·효과 미포함','native_packed':False,'runtime_verified':False})
    print(json.dumps({q['ref']:{'remaining':q['remaining_exposed_base_lower'],'rejected':q['rejected_rows'],'components':q['components']}for q in records}))
if __name__=='__main__':main()
