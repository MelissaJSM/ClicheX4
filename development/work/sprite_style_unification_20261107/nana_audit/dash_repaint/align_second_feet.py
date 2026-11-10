"""각 새 부츠의 축척과 방향을 유지하며 원 동작의 발끝으로 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.spatial import Delaunay
from scipy.ndimage import map_coordinates,label
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register
# Rectangle corners share one translation, so the complete boot is never
# stretched or rotated. Only the adjacent calf from the same source is fitted.
CONFIG={69:(13,[(-2,17,4,23,4,0)]),
        75:(16,[(-3,20,1,23,5,0),(1,18,4,22,4,0)]),
        77:(12,[(5,18,10,23,-1,-1),(10,16,15,20,-1,3)]),
        81:(6,[(-2,16,5,23,4,-1),(26,18,32,23,-5,0)]),
        83:(8,[(-11,17,-5,23,3,-1),(11,17,16,23,-4,0)])}
def locate(n):
    if n==75:
        p=json.loads((D/'basic_second_refined_v3/registration.json').read_text('utf8'))['frames'][1]
        return p['edited_registration'],D/'basic_second_refined_v3/source_075.png',D/'basic_second_refined_v3/base_075.png',p['edited_source_art_sha256']
    folder='basic_last_registered_v2'if n==83 else'basic_second_registered_v1';d=json.loads((D/folder/'registration.json').read_text('utf8'));r=next(r for r in d['frames']if r['ref']==n)
    return r,D/folder/f'source_{n:03}.png',D/('basic_second_refined_v3'if n in(69,77,81)else folder)/f'base_{n:03}.png',r.get('source_art_sha256',d.get('source_art_sha256'))
def transform(crop,r,old,start,modules,pal,n,partial=False):
    fixed=[(-40,-40),(40,-40),(-40,40),(40,40),(-40,start),(-20,start),(0,start),(20,start),(40,start),(-40,28),(40,28)];pairs=[(q,q)for q in fixed]
    for x0,y0,x1,y1,dx,dy in modules:
        pairs.extend([((x,y),(x+dx,y+dy))for x,y in((x0,y0),(x1,y0),(x0,y1),(x1,y1))])
    src=np.array([s for s,t in pairs],float);dst=np.array([t for s,t in pairs],float);need(len(np.unique(src,axis=0))==len(src),'Distinct anchors');tri=Delaunay(src);yy,xx=np.indices((640,640),dtype=float);coords=np.stack((xx/8-40+.0625,yy/8-40+.0625),-1);uv=np.full_like(coords,np.nan);ratios=[]
    for ids in tri.simplices:
        s0,s1,s2=src[ids];d0,d1,d2=dst[ids];sa=np.linalg.det(np.stack((s1-s0,s2-s0)));da=np.linalg.det(np.stack((d1-d0,d2-d0)));need(sa*da>0,f'Flipped triangle {n} {src[ids].tolist()}');ratios.append(float(da/sa));w=(coords-d0)@np.linalg.inv(np.stack((d1-d0,d2-d0),1)).T;inside=(w[:,:,0]>=-1e-9)&(w[:,:,1]>=-1e-9)&(w.sum(2)<=1+1e-9);mapped=s0+w[:,:,0,None]*(s1-s0)+w[:,:,1,None]*(s2-s0);uv[inside]=mapped[inside]
    ox,oy=r['native_position'];ex,ey=r['target_eye'];sx=(uv[:,:,0]-ox)*crop.width/r['native_width']-.5;sy=np.where(uv[:,:,1]<ey+1,(uv[:,:,1]-oy)*r['split']/r['height_above'],r['split']+(uv[:,:,1]-ey-1)*(crop.height-r['split'])/r['height_below'])-.5;rgba=np.array(crop,float);alpha=rgba[:,:,3]/255;aa=map_coordinates(alpha,[sy,sx],order=1,mode='constant',cval=0);sample=np.zeros((640,640,4),np.uint8)
    for ci in range(3):sample[:,:,ci]=np.rint(map_coordinates(rgba[:,:,ci]*alpha,[sy,sx],order=1,mode='constant',cval=0)/np.maximum(aa,.00001)).clip(0,255).astype(np.uint8)
    sample[:,:,3]=np.rint(aa*255).astype(np.uint8);native=register(Image.fromarray(sample),(80,80),pal,'area_vote');full=np.zeros_like(old);full[120:200,120:200]=native;new=old.copy();Y,X=np.indices(old.shape);mask=Y>=160+start;new[mask]=full[mask]
    need(np.array_equal(new[~mask],old[~mask]),'Upper exact')
    if not partial:
        need(np.nonzero(new)[0].max()==np.nonzero(old)[0].max(),'Original floor');need(label(new>0,np.ones((3,3)))[1]==1,'Connected alpha')
    return new,sample,{'source_points':src.tolist(),'target_points':dst.tolist(),'mesh_area_ratio':[min(ratios),max(ratios)]}
def separated77(crop,r,old,start,modules,pal):
    # Distances partition only the already authored lower legs. No pixel colour
    # is invented and neither foot borrows texture from the other leg.
    yy,xx=np.indices((crop.height,crop.width),dtype=float);xy=np.stack((xx,yy),-1)
    paths=[[(137,341),(166,383),(185,422),(196,460)],[(165,340),(198,375),(225,400),(238,424)]]
    distances=[]
    for path in paths:
        ds=[]
        for aa,bb in zip(path[:-1],path[1:]):
            aa=np.array(aa,float);bb=np.array(bb,float);v=bb-aa;t=((xy-aa)*v).sum(2)/(v*v).sum();p=aa+t.clip(0,1)[:,:,None]*v;ds.append(((xy-p)**2).sum(2))
        distances.append(np.minimum.reduce(ds))
    owner=np.argmin(distances,axis=0);results=[];samples=[];metas=[]
    for i,module in enumerate(modules):
        rgba=np.asarray(crop).copy();rgba[owner!=i,3]=0
        new,sample,meta=transform(Image.fromarray(rgba),r,old,start,[module],pal,77,True);results.append(new);samples.append(sample);metas.append(meta)
    Y,X=np.indices(old.shape);mask=Y>=160+start;out=old.copy();out[mask]=0
    # The stocking/back leg is below the exposed/front knee leg.
    for i in(1,0):sel=mask&(results[i]>0);out[sel]=results[i][sel]
    need(np.array_equal(out[~mask],old[~mask]),'77 upper exact');need(label(out>0,np.ones((3,3)))[1]==1,'77 connected');need(np.nonzero(out)[0].max()==182,'77 floor')
    combined=np.asarray(crop).copy();combined[owner==0,:3]//=2
    return out,combined,{'separate_authored_leg_paths':paths,'separate_meshes':metas,'lower_overlap_pixels':int(np.count_nonzero(mask&(results[0]>0)&(results[1]>0)))}
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'));arc=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(arc.data)==plan['parent_arc_sha256'],'Parent');pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[:16]],float);out=D/'basic_second_contacts_v4';need(not out.exists(),'Fresh output');out.mkdir();rows=[];proof=[]
    for n,(start,modules)in CONFIG.items():
        r,src,oldpath,artsha=locate(n);crop=Image.open(src).convert('RGBA');old=np.array(Image.open(oldpath));new,sample,meta=separated77(crop,r,old,start,modules,pal)if n==77 else transform(crop,r,old,start,modules,pal,n)
        Image.fromarray(new).save(out/f'base_{n:03}.png');arc.rgba(new).save(out/f'base_{n:03}_rgba.png');Image.fromarray(sample).save(out/f'source_rgba8_{n:03}.png');meta.update(ref=n,source_art_sha256=artsha,source_rgba_sha256=digest(src),old_sha256=sha(old.tobytes()),after_sha256=sha(new.tobytes()),native_upper_y_lt_exact=start,rigid_boot_modules=modules,floor_y=int(np.nonzero(new)[0].max()-160),floor_x=(np.flatnonzero(new[np.nonzero(new)[0].max()])-160).tolist(),old_game_pixels_used=0,flat_fills=0);proof.append(meta)
        rows.append((f'dash{n}',[('원래',arc.composite(n)[0]),('새 원화 첫 등록',arc.rgba(old)),('각 부츠 접점 정합',arc.rgba(new)),('대기',arc.composite(0)[0])]))
    for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',8)
    write(out/'registration.json',{'source_arc_sha256':sha(arc.data),'frames':proof,'native_packed':False,'runtime_verified':False});print(json.dumps({'out':str(out),'refs':list(CONFIG)}))
if __name__=='__main__':main()
