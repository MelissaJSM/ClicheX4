"""새 원화의 관절/구두 접점만 고정하는 후보. 게임/원본 파일 쓰기 없음."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.spatial import Delaunay
from scipy.ndimage import map_coordinates
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,need,write,helper,digest
from register_page import register
from review_all_bodies import source as body_source

# Source/target coordinates are on the registered world grid, never arbitrary
# image row ratios. Each small shoe and its ankle travel together.
POINTS={
33:[((2,19),(0,19)),((5,21),(5,21)),((-1,8),(-1,8)),((3,10),(3,10))],
35:[((2,10),(-1,10)),((11,20),(9,20)),((-3,3),(-3,3)),((5,10),(4,10))],
37:[((4,12),(2,12)),((10.5,16),(6.5,16)),((-4,7),(-2,7)),((6,11),(4,11))],
39:[((13.5,14),(8.5,14)),((-2,2),(-2,2)),((7,8),(4,8))],
41:[((7.5,17),(6.5,17)),((2,8),(1,8)),((-3,2),(-3,2)),((4,10),(4,10))],
43:[((15,14),(11.5,14)),((-3,3),(-3,3)),((8,9),(6,9))],
45:[((4,12),(4,12)),((6,12),(6,12)),((4,16),(4,16)),((6,16),(6,16)),
    ((7,12),(9,12)),((10,12),(12,12)),((7,17),(9,17)),((10,17),(12,17)),((-2,6),(-2,6))],
47:[((3.5,18),(3.5,18)),((10.5,14),(9.5,17)),((-2,7),(-2,7)),((5,9),(5,9))],
49:[((-4,21),(-4.5,21)),((10,21),(9.5,21)),((-3,11),(-3,11)),((5,13),(5,13))],
51:[((-5,20),(-7,20)),((13,20),(10,20)),((-5,12),(-5,12)),((4,13),(4,13)),((2,12),(2,12))],
53:[((-4.5,21),(-6.5,21)),((10.5,21),(7.5,21)),((-3,10),(-3,10)),((4,13),(3,13))],
}
def folder(n):return 'fourth51_knee_registered_v1'if n==51 else'fourth_joint_registered_v1'if n in(37,47)else'fourth_a_registered_v1'if n<41 else'fourth_b_registered_v1'if n<49 else'fourth_c_registered_v1'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='fourth_contacts_probe_v1');ap.add_argument('--refs',nargs='*',type=int);args=ap.parse_args();refs=args.refs or list(POINTS)
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/args.out;need(not out.exists(),'Fresh output');out.mkdir()
    pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],float);rows=[];reports=[]
    for n in refs:
        fdir=D/folder(n);doc=json.loads((fdir/'registration.json').read_text('utf8'));r=next(r for r in doc['frames']if r['ref']==n);need(digest(ROOT/r['source'])==r['source_sha256'],'Art source');crop=Image.open(fdir/f'source_{n:03}.png').convert('RGBA');old=np.array(Image.open(fdir/f'fourth_{n:03}.png'));base=np.array(Image.open(body_source(n)/f'base_{n:03}.png'));ex,ey=r['eye'];start=ey+15
        fixed=[(-40,-40),(40,-40),(-40,40),(40,40),(-20,start),(0,start),(20,start),(35,start),(-25,25),(30,25)]
        pairs=[(q,q)for q in fixed]+POINTS[n];src=np.array([s for s,t in pairs],float);dst=np.array([t for s,t in pairs],float);need(len(np.unique(src,axis=0))==len(src),'Distinct anchors')
        tri=Delaunay(src);scale=8;size=80;yy,xx=np.indices((size*scale,size*scale),dtype=float);coords=np.stack((xx/scale-40+.5/scale,yy/scale-40+.5/scale),-1);uv=np.full_like(coords,np.nan);ratios=[]
        for ids in tri.simplices:
            s0,s1,s2=src[ids];d0,d1,d2=dst[ids];sa=np.linalg.det(np.stack((s1-s0,s2-s0)));da=np.linalg.det(np.stack((d1-d0,d2-d0)));need(sa*da>0,f'Flipped triangle {n}/{ids.tolist()}');ratios.append(float(da/sa))
            w=(coords-d0)@np.linalg.inv(np.stack((d1-d0,d2-d0),1)).T;inside=(w[:,:,0]>=-1e-9)&(w[:,:,1]>=-1e-9)&(w.sum(2)<=1+1e-9);mapped=s0+w[:,:,0,None]*(s1-s0)+w[:,:,1,None]*(s2-s0);uv[inside]=mapped[inside]
        ox,oy=r['native_position'];sx=(uv[:,:,0]-ox)*crop.width/r['native_width']-.5;sy=np.where(uv[:,:,1]<ey+1,(uv[:,:,1]-oy)*r['split']/r['height_above'],r['split']+(uv[:,:,1]-ey-1)*(crop.height-r['split'])/r['height_below'])-.5
        rgba=np.array(crop,float);alpha=rgba[:,:,3]/255;aa=map_coordinates(alpha,[sy,sx],order=1,mode='constant',cval=0);sample=np.zeros((size*scale,size*scale,4),np.uint8)
        for ci in range(3):sample[:,:,ci]=np.rint(map_coordinates(rgba[:,:,ci]*alpha,[sy,sx],order=1,mode='constant',cval=0)/np.maximum(aa,.00001)).clip(0,255).astype(np.uint8)
        sample[:,:,3]=np.rint(aa*255).astype(np.uint8);Image.fromarray(sample).save(out/f'fourth_{n:03}_source_rgba8.png');native=register(Image.fromarray(sample),(size,size),pal,'area_vote');target=old.copy();sampled=np.zeros_like(old);sampled[120:200,120:200]=native
        Y,X=np.indices(old.shape);region=(Y>=160+start)&(X<180);target[region]=sampled[region]
        # All upper/new accepted cloth is unchanged. Only source-based local
        # joint registration below the explicit seam is proposed here.
        need(np.array_equal(target[~region],old[~region]),'Protected upper/veil');Image.fromarray(target).save(out/f'fourth_{n:03}.png');a.rgba(target,16).save(out/f'fourth_{n:03}_rgba.png')
        rows.append((f'contacts {n}',[('새 기본',a.rgba(base)),('포스 원화 등록',a.rgba(old,16)),('관절/구두 접점 후보',a.rgba(target,16))]));reports.append({'ref':n,'source_art_sha256':r['source_sha256'],'source_indexed_sha256':sha(old.tobytes()),'output_indexed_sha256':sha(target.tobytes()),'source_points':src.tolist(),'target_points':dst.tolist(),'mesh_ratio':[min(ratios),max(ratios)],'upper_region_exact':True,'source_rgba_resampling':True,'flat_fills':0,'native_packed':False})
    for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',7)
    write(out/'registration.json',{'frames':reports,'scope':'새 원화의 국소 관절/발 정합 검토본. 부분파츠 패킹 전이며 미술 통과 여부는 별도 판정.','native_packed':False,'runtime_verified':False});print(json.dumps({'refs':refs,'out':str(out)}))
if __name__=='__main__':main()
