"""새 벽 기본/포스와 새 사격팔을 실제 부분 파츠 후보로 조립한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper
from prepare_fourth_guides import source
def spans(row):
    xs=np.flatnonzero(row);return np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)if len(xs)else[]
def main():
    a=Archive((D.parent/'base_run_repaint/packed_joint_v2/PL00_U.ARC').read_bytes());plan=json.loads((D/'inputs.json').read_text('utf8'));out=D/'joint_layers_probe_v4';out.mkdir(exist_ok=True);Y,X=np.indices((384,384));xx=X-160;yy=Y-160;reports=[];rows=[]
    for n in range(55,67,2):
        p=next(q for q in plan['frames']if q['ref']==n);ex,ey=map(int,p['eye_world']);b=np.array(Image.open(source(n)));f=np.array(Image.open(D/'fourth_contacts_v1'/f'fourth_{n:03}.png'));base=b.copy();links=[];removed=[];footlinks=[]
        if n==57:
            # The new basic front boot has a valid low toe at world y=10.
            # Preserve that authored silhouette instead of intersecting away
            # its final two pixels to match the smaller Fourth low shoe.
            original=f.copy();foot_region=(xx<-5)&(yy>=5)&(yy<=10);f[foot_region]=0
            for y in range(5,11):
                sy=round(5+(y-5)*4/5);dest=np.flatnonzero((b[160+y]>0)&(np.arange(384)<155));src=np.flatnonzero((original[160+sy]>0)&(np.arange(384)<155))
                need(len(src)>0 and len(dest)>0,'57 authored front foot row')
                samples=np.rint(np.linspace(0,len(src)-1,len(dest))).astype(int);f[160+y,dest]=original[160+sy,src[samples]]
                footlinks.extend([[int(x-160),y,int(sx-160),sy,int(original[160+sy,sx])]for x,sx in zip(dest,src[samples])])
        for y in range(160+ey+17,384):
            for segment in spans(b[y]>0):
                dest=segment[f[y,segment]>0];base[y,segment]=0
                if not len(dest):removed.append([int(y-160),int(segment[0]-160),int(segment[-1]-160)]);continue
                samples=np.rint((dest-dest[0])*(len(segment)-1)/max(1,dest[-1]-dest[0])).astype(int);base[y,dest]=b[y,segment[samples]]
                links.extend([[int(x-160),int(y-160),int(sx-160),int(b[y,sx])]for x,sx in zip(dest,segment[samples])])
        if n==57:base[(xx<-5)&(yy>=5)&(yy<=10)]=b[(xx<-5)&(yy>=5)&(yy<=10)]
        lower_change=base!=b;need(not np.any(lower_change&(yy<ey+17)),'Common lower changed upper')
        display={}
        for ref in(n,n+1):
            body=base.copy();costume=f.copy()
            if ref%2==0:
                originalshot=np.array(Image.open(D/'shot_reach_review_v4'/f'merged_probe_{ref:03}.png'));body=originalshot.copy();body[lower_change]=base[lower_change]
                arm=np.array(Image.open(D/'shot_reach_review_v4'/f'translated_arm_{ref:03}.png'))
                remove=(xx<=ex+1)&(yy>=np.where(xx<ex-3,ey+1,ey+4))&(yy<ey+15);head_guard=(yy<=ey+4)&(xx>=ex-2);remove&=~head_guard;costume[remove]=0;costume[arm>0]=arm[arm>0]
                need(np.array_equal(body[yy<ey+17],originalshot[yy<ey+17]),'Shooting upper changed')
            full=np.where(costume,costume,body).astype(np.uint8)
            # Head module follows crown/face. Large trailing veil remains legs,
            # matching the user's accepted four-part assignment.
            head=(yy<ey+4)&((xx>=ex-3)|(yy<ey))
            palmseed=np.isin(full,[10,11,12,13])&(xx>8)&(yy<ey+3)
            py,px=np.nonzero(palmseed);need(len(px)>0,'Raised palm ownership')
            palm=np.array([float(np.median(px)-160),float(np.median(py)-160)]);shoulder=np.array([ex+7,ey+5],float);v=palm-shoulder
            t=np.clip(((xx-shoulder[0])*v[0]+(yy-shoulder[1])*v[1])/float(v@v),0,1)
            distance=(xx-shoulder[0]-t*v[0])**2+(yy-shoulder[1]-t*v[1])**2
            raised_arm=(distance<=10)&(xx>ex+4)
            leg=(yy>=ey+17)|((xx>=ex+14)&(yy>=ey+4))
            front=(xx<ex+3)&(yy>=ey)&(yy<ey+17)&~head
            owner=np.full((384,384),6,np.uint8);owner[leg]=8;owner[head]=5;owner[front|raised_arm]=7
            pc=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full]
            diff=((full!=body)|((costume>0)&pc))&(full>0);layers={pb:np.where(diff&(owner==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}
            merged=body.copy()
            for pb in(8,5,7,6):merged=np.where(layers[pb],layers[pb],merged)
            need(np.array_equal(merged,full),'Joint composition')
            for pb,ar in{0:body,**layers}.items():Image.fromarray(ar).save(out/f'layer{pb}_{ref:03}.png')
            Image.fromarray(full).save(out/f'full_{ref:03}.png');Image.fromarray(owner).save(out/f'owner_{ref:03}.png')
            rgba=a.rgba(body);rgba.alpha_composite(a.rgba(costume,16));display[ref]=[a.rgba(body),rgba]
            reports.append({'ref':ref,'base_sha256':sha(body.tobytes()),'full_sha256':sha(full.tobytes()),'layers':{str(pb):sha(v.tobytes())for pb,v in layers.items()},'changed_by_owner':{str(pb):int(np.count_nonzero(v))for pb,v in layers.items()},'common_lower_links':links if ref==n else None,'removed_lower_spans':removed if ref==n else None,'front_57_foot_source_links':footlinks if ref==n else None,'muzzle_protected':ref%2==0})
        rows.append((f'wall {n}/{n+1}',[('대기 기본',a.composite(0)[0]),('새 기본',display[n][0]),('새 기본 사격',display[n+1][0]),('대기 포스',a.composite(0,15)[0]),('새 포스',display[n][1]),('새 포스 사격',display[n+1][1])]))
    for i in range(0,6,3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',5)
    write(out/'manifest.json',{'ready_to_apply':False,'source_arc_sha256':sha(a.data),'frames':reports,'scope':'공동 하체 외곽 및 새 사격팔 합성의 미술 검토 후보. 파츠 패킹/실기 전.','runtime_verified':False});print(json.dumps({'out':str(out),'frames':len(reports)}))
if __name__=='__main__':main()
