"""새 대시 원화의 부츠를 강체로 이동하고 바로 위 정강이 접점만 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.spatial import Delaunay
from scipy.ndimage import map_coordinates,label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register
# Each ankle/boot bounding rectangle translates as one rigid module. The narrow
# transition above it uses source RGBA, not generated gradients or old pixels.
CONFIG={67:(14,[(-6,18,3,23,2),(16,18,23,23,-4)]),79:(10,[(10,18,18,23,-3)]),93:(10,[(7,14,12,18,-3)])}
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(a.data)==plan['parent_arc_sha256'],'Parent');doc=json.loads((D/'basic_registered_v1/registration.json').read_text('utf8'));out=D/'basic_contacts_v2';need(not out.exists(),'Fresh output');out.mkdir();pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],float);rows=[];proof=[]
    for n,(start,modules)in CONFIG.items():
        r=next(r for r in doc['frames']if r['ref']==n);crop=Image.open(D/f'basic_registered_v1/source_{n:03}.png').convert('RGBA');old=np.array(Image.open(D/f'basic_registered_v1/base_{n:03}.png'));ex,ey=r['target_eye'];fixed=[(-40,-40),(40,-40),(-40,40),(40,40),(-30,start),(-10,start),(0,start),(10,start),(30,start),(-30,26),(30,26)];pairs=[(q,q)for q in fixed]
        for x0,y0,x1,y1,dx in modules:
            pairs.extend([((x,y),(x+dx,y))for x,y in((x0,y0),(x1,y0),(x0,y1),(x1,y1))])
        src=np.array([s for s,t in pairs],float);dst=np.array([t for s,t in pairs],float);need(len(np.unique(src,axis=0))==len(src),'Distinct anchors');tri=Delaunay(src);yy,xx=np.indices((640,640),dtype=float);coords=np.stack((xx/8-40+.0625,yy/8-40+.0625),-1);uv=np.full_like(coords,np.nan);ratios=[]
        for ids in tri.simplices:
            s0,s1,s2=src[ids];d0,d1,d2=dst[ids];sa=np.linalg.det(np.stack((s1-s0,s2-s0)));da=np.linalg.det(np.stack((d1-d0,d2-d0)));need(sa*da>0,f'Flipped triangle {n}');ratios.append(float(da/sa));w=(coords-d0)@np.linalg.inv(np.stack((d1-d0,d2-d0),1)).T;inside=(w[:,:,0]>=-1e-9)&(w[:,:,1]>=-1e-9)&(w.sum(2)<=1+1e-9);mapped=s0+w[:,:,0,None]*(s1-s0)+w[:,:,1,None]*(s2-s0);uv[inside]=mapped[inside]
        ox,oy=r['native_position'];sx=(uv[:,:,0]-ox)*crop.width/r['native_width']-.5;sy=np.where(uv[:,:,1]<ey+1,(uv[:,:,1]-oy)*r['split']/r['height_above'],r['split']+(uv[:,:,1]-ey-1)*(crop.height-r['split'])/r['height_below'])-.5;rgba=np.array(crop,float);alpha=rgba[:,:,3]/255;aa=map_coordinates(alpha,[sy,sx],order=1,mode='constant',cval=0);sample=np.zeros((640,640,4),np.uint8)
        for ci in range(3):sample[:,:,ci]=np.rint(map_coordinates(rgba[:,:,ci]*alpha,[sy,sx],order=1,mode='constant',cval=0)/np.maximum(aa,.00001)).clip(0,255).astype(np.uint8)
        sample[:,:,3]=np.rint(aa*255).astype(np.uint8);native=register(Image.fromarray(sample),(80,80),pal,'area_vote');new=old.copy();full=np.zeros_like(old);full[120:200,120:200]=native;Y,X=np.indices(old.shape);mask=Y>=160+start;new[mask]=full[mask];need(np.array_equal(new[~mask],old[~mask]),'Upper exact');need(np.nonzero(new)[0].max()==np.nonzero(old)[0].max(),'Floor preserved');Image.fromarray(new).save(out/f'base_{n:03}.png');a.rgba(new).save(out/f'base_{n:03}_rgba.png');Image.fromarray(sample).save(out/f'source_rgba8_{n:03}.png');rows.append((f'dash{n}',[('원래',a.composite(n)[0]),('첫 새 원화',a.rgba(old)),('부츠/발목 접점 정합',a.rgba(new)),('대기',a.composite(0)[0])]))
        proof.append({'ref':n,'old_sha256':sha(old.tobytes()),'after_sha256':sha(new.tobytes()),'source_art_sha256':doc['source_art_sha256'],'native_upper_y_lt_exact':start,'rigid_boot_modules':[list(m)for m in modules],'source_points':src.tolist(),'target_points':dst.tolist(),'mesh_area_ratio':[min(ratios),max(ratios)],'floor_y':int(np.nonzero(new)[0].max()-160),'floor_x':(np.flatnonzero(new[np.nonzero(new)[0].max()])-160).tolist(),'components_8':int(label(new>0,np.ones((3,3)))[1]),'old_game_pixels_used':0,'flat_fills':0})
    new=np.array(Image.open(D/'dash71_boots_registered_v1/base_071.png'));Image.fromarray(new).save(out/'base_071.png');a.rgba(new).save(out/'base_071_rgba.png');helper.grid(rows,out/'comparison.png',8);write(out/'registration.json',{'source_arc_sha256':sha(a.data),'frames':proof,'separate_71_source':'dash71_boots_registered_v1','scope':'국소 원화 등록 미술 후보. 패킹·게임 실행 전.','native_packed':False,'runtime_verified':False});print(json.dumps(proof))
if __name__=='__main__':main()
