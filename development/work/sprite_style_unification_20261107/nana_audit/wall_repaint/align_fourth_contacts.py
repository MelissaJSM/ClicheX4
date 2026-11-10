"""포스 새 원화의 손/발 국소 정합. 팔 길이 늘림이나 옛 그림 덮기 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.spatial import Delaunay
from scipy.ndimage import map_coordinates
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register
from prepare_fourth_guides import source
def main():
    a=Archive((D.parent/'base_run_repaint/packed_joint_v2/PL00_U.ARC').read_bytes());reg=json.loads((D/'fourth_registered_v1/registration.json').read_text('utf8'));out=D/'fourth_contacts_v1';out.mkdir(exist_ok=True)
    palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);Y,X=np.indices((384,384));rows=[];reports=[]
    for r in reg['frames']:
        n=r['ref'];base=np.array(Image.open(source(n)));old=np.array(Image.open(D/'fourth_registered_v1'/f'fourth_{n:03}.png'));crop=Image.open(D/'fourth_registered_v1'/f'source_{n:03}.png').convert('RGBA');need(digest(ROOT/r['source'])==r['source_sha256'],'Art hash')
        ex,ey=r['eye'];ox,oy=r['native_position'];bottom=r['foot_y']+1
        def palm(m):
            y,x=np.nonzero(np.isin(m,[10,11,12,13])&(X>168)&(Y<155));need(len(x)>0,'Palm');return np.array([np.median(x)-160,np.median(y)-160])
        def foot(m):
            y=np.where(m>0)[0].max();return float(np.median(np.where(m[y]>0)[0])-160)
        hx,hy=palm(old);hd=np.rint(palm(base)-palm(old));fd=round(foot(base)-foot(old));bd=round(fd*.4)
        src=np.array([[-40,-40],[40,-40],[-40,40],[40,40],[ex-7,oy-1],[ex+8,oy-1],[ex-7,ey+1],[ex+8,ey+1],[ex,ey],[hx-2,hy-3],[hx+2,hy-3],[hx-2,hy+3],[hx+2,hy+3],[-6,0],[5,0],[-8,10],[8,10],[-10,bottom],[20,bottom]],float)
        changes=np.array([[0,0],[0,0],[fd,0],[fd,0]]+[[0,0]]*5+[hd.tolist()]*4+[[bd,0]]*2+[[round((bd+fd)/2),0]]*2+[[fd,0]]*2,float);dst=src+changes;tri=Delaunay(src)
        scale=8;size=80;yy,xx=np.indices((size*scale,size*scale),dtype=float);coords=np.stack((xx/scale-40+.5/scale,yy/scale-40+.5/scale),-1);uv=np.full_like(coords,np.nan);ratios=[]
        for ids in tri.simplices:
            sa=np.linalg.det(np.stack([src[ids[1]]-src[ids[0]],src[ids[2]]-src[ids[0]]]))
            da=np.linalg.det(np.stack([dst[ids[1]]-dst[ids[0]],dst[ids[2]]-dst[ids[0]]]))
            need(sa*da>0,f'Flipped triangle {n}/{ids.tolist()}');ratios.append(float(da/sa))
            p0,p1,p2=dst[ids];basis=np.stack((p1-p0,p2-p0),1);w=(coords-p0)@np.linalg.inv(basis).T;inside=(w[:,:,0]>=-1e-9)&(w[:,:,1]>=-1e-9)&(w.sum(2)<=1+1e-9);mapped=src[ids[0]]+w[:,:,0,None]*(src[ids[1]]-src[ids[0]])+w[:,:,1,None]*(src[ids[2]]-src[ids[0]]);uv[inside]=mapped[inside]
        sx=(uv[:,:,0]-ox)*crop.width/r['native_width']-.5;sy=np.where(uv[:,:,1]<ey+1,(uv[:,:,1]-oy)*r['split']/r['height_above'],r['split']+(uv[:,:,1]-ey-1)*(crop.height-r['split'])/r['height_below'])-.5
        arr=np.array(crop).astype(float);alpha=arr[:,:,3]/255;aa=map_coordinates(alpha,[sy,sx],order=1,mode='constant',cval=0);rgba=np.zeros((size*scale,size*scale,4),np.uint8)
        for ci in range(3):rgba[:,:,ci]=np.rint(map_coordinates(arr[:,:,ci]*alpha,[sy,sx],order=1,mode='constant',cval=0)/np.maximum(aa,.00001)).clip(0,255).astype(np.uint8)
        rgba[:,:,3]=np.rint(aa*255).astype(np.uint8);native=register(Image.fromarray(rgba),(size,size),palette,'area_vote');target=np.zeros((384,384),np.uint8);target[120:200,120:200]=native
        # The single green iris is fixed to the base eye, distinct from brooch.
        eyemask=(Y<160+ey+2)&(X<160+ex+7)&(X>=160+ex-7)&(target==14);target[eyemask]=12;target[ey+160,ex+160]=14
        Image.fromarray(target).save(out/f'fourth_{n:03}.png');a.rgba(target,16).save(out/f'fourth_{n:03}_rgba.png')
        ys,xs=np.nonzero(target);fy=int(ys.max());reports.append({'ref':n,'source_sha256':r['source_sha256'],'source_points':src.tolist(),'target_points':dst.tolist(),'palm_delta':hd.tolist(),'foot_x_delta':fd,'mesh_ratio':[min(ratios),max(ratios)],'eye':[ex,ey],'foot_y':fy-160,'foot_x':(np.flatnonzero(target[fy])-160).tolist(),'base_foot_x':(np.flatnonzero(base[fy])-160).tolist(),'indexed_sha256':sha(target.tobytes()),'old_art_pixels_used':0})
        rows.append((f'wall {n}',[('새 기본',a.rgba(base)),('포스 직접등록',a.rgba(old,16)),('접점 정합',a.rgba(target,16))]))
    for i in range(0,6,3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',8)
    write(out/'registration.json',{'frames':reports,'native_packed':False,'runtime_verified':False,'method':'원화 RGBA에서 직접 영역투표. 고정 머리/눈·강체 손 이동·하체 미세 기울기; 옛 그림 없음.'});print(json.dumps(reports))
if __name__=='__main__':main()
