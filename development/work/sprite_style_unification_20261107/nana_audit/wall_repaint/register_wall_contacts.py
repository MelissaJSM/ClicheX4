"""Whole-source registration with rigid head/hand anchors and lower-body tilt."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import crop_cell,register
from PIL import Image
import numpy as np
from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator
from scipy.ndimage import map_coordinates

KEYS=[55,57,61,65]
CONTROL={
55:{'head':[-10,-22,3,-11],'hand':[12,-10],'hand_delta':[2,-2],'foot_delta':6,'body_delta':2},
57:{'head':[-9,-23,6,-12],'hand':[15,-11],'hand_delta':[3,-2],'foot_delta':4,'body_delta':3},
61:{'head':[-8,-23,5,-12],'hand':[13,-18],'hand_delta':[4,0],'foot_delta':5,'body_delta':3},
65:{'head':[-7,-22,7,-12],'hand':[14,-21],'hand_delta':[2,-1],'foot_delta':4,'body_delta':2},
}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',type=int,choices=[1,2],default=1);ap.add_argument('--page',choices=['keys','remaining'],default='keys');args=ap.parse_args()
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['source_arc']).read_bytes());need(sha(a.data)==plan['source_sha256'],'Parent')
    source_dir=D/f'basic_{args.page}_v{args.version}';native_dir=D/(f'basic_registered_probe_v{args.version}'if args.page=='keys'else f'basic_remaining_registered_v{args.version}')
    reg=json.loads((native_dir/'registration.json').read_text('utf8'));im=Image.open(source_dir/'generated.png').convert('RGBA');need(digest(source_dir/'generated.png')==reg['source_art_sha256'],'Source provenance');palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
    out=D/(f'basic_contacts_probe_v{args.version+1}'if args.page=='keys'else f'basic_remaining_contacts_v{args.version}');out.mkdir(exist_ok=True);rows=[];records=[]
    refs=KEYS if args.page=='keys'else[59,63]
    for k,n in enumerate(refs):
        r=next(q for q in reg['frames']if q['ref']==n);p=next(q for q in plan['frames']if q['ref']==n);c=CONTROL[n].copy()if n in CONTROL else{};crop,box=crop_cell(im,k);arr=np.array(crop).astype(float)
        if args.page=='keys'and args.version==2:
            h,delta,foot={55:([12,-10],[2,-1],6),57:([14,-11],[4,-2],4),61:([14,-18],[3,0],4),65:([15,-20],[1,-2],3)}[n]
            c.update(hand=h,hand_delta=delta,foot_delta=foot)
        old=np.array(Image.open(native_dir/f'base_{n:03}.png'));ys,xs=np.nonzero(old);left,top,right,bottom=int(xs.min()-160),int(ys.min()-160),int(xs.max()-159),int(ys.max()-159)
        if args.page=='remaining':
            Y,X=np.indices(old.shape);original=a.layer(n)[0]
            def palm(m):
                y,x=np.nonzero(np.isin(m,[10,11,12,13])&(X>168)&(Y<155));need(len(x)>0,'Palm not found');return np.array([np.median(x)-160,np.median(y)-160])
            def foot(m):
                y=np.where(m>0)[0].max();return float(np.median(np.where(m[y]>0)[0])-160)
            delta=np.rint(palm(original)-palm(old)).astype(int);ex,ey=map(int,p['eye_world']);c={'head':[ex-6,top-1,ex+8,ey+1],'hand':np.rint(palm(old)).astype(int).tolist(),'hand_delta':delta.tolist(),'foot_delta':round(foot(original)-foot(old)),'body_delta':round(delta[0]*.75)}
        l,t,rr,b=c['head'];hx,hy=c['hand'];dx,dy=c['hand_delta'];f=c['foot_delta'];bd=c['body_delta']
        # All four palm-neighborhood points receive the same translation.
        # This changes placement rather than elongating the drawn forearm.
        source=[[-40,-40],[40,-40],[-40,40],[40,40],[l,t],[rr,t],[l,b],[rr,b],p['eye_world'],[hx-2,hy-3],[hx+2,hy-3],[hx-2,hy+3],[hx+2,hy+3],[-6,0],[5,0],[-8,10],[8,10],[-10,bottom],[15,bottom]]
        delta=[[0,0],[0,0],[f,0],[f,0],[0,0],[0,0],[0,0],[0,0],[0,0]]+[[dx,dy]]*4+[[bd,0]]*2+[[round((bd+f)/2),0]]*2+[[f,0]]*2
        src=np.array(source,float);dst=src+np.array(delta,float);tri=Delaunay(src if args.page=='remaining'else dst)
        ratios=[]
        for ids in tri.simplices:
            area_src=np.linalg.det(np.stack([src[ids[1]]-src[ids[0]],src[ids[2]]-src[ids[0]]]))
            area_dst=np.linalg.det(np.stack([dst[ids[1]]-dst[ids[0]],dst[ids[2]]-dst[ids[0]]]))
            need(area_src*area_dst>0,f'Source/target mesh flips or collapses {n}: {ids.tolist()} {area_src}/{area_dst}; {c}')
            ratios.append(float(area_dst/area_src))
        scale=8;x0,y0=-40,-40;size=80;yy,xx=np.indices((size*scale,size*scale),dtype=float);coords=np.stack((xx/scale+x0+(0.5/scale),yy/scale+y0+(0.5/scale)),axis=-1)
        if args.page=='remaining':
            # Preserve source triangulation when collinear source anchors bend.
            # Re-triangulating only destination points can create a collapsed
            # source triangle and is correctly rejected above.
            uv=np.full(coords.shape,np.nan)
            for ids in tri.simplices:
                p0,p1,p2=dst[ids];basis=np.stack((p1-p0,p2-p0),axis=1);weights=(coords-p0)@np.linalg.inv(basis).T
                inside=(weights[:,:,0]>=-1e-9)&(weights[:,:,1]>=-1e-9)&(weights.sum(2)<=1+1e-9)
                mapped=src[ids[0]]+weights[:,:,0,None]*(src[ids[1]]-src[ids[0]])+weights[:,:,1,None]*(src[ids[2]]-src[ids[0]])
                uv[inside]=mapped[inside]
        else:uv=LinearNDInterpolator(tri,src,fill_value=np.nan)(coords)
        ox,oy=r['native_position'];ey=p['eye_world'][1];split=round(r['source_eye'][1]+1);nativew=round(crop.width*r['source_scale_x']);hu=ey-oy+1;hl=bottom-ey-1
        sx=(uv[:,:,0]-ox)*crop.width/nativew-.5
        sy=np.where(uv[:,:,1]<ey+1,(uv[:,:,1]-oy)*split/hu,split+(uv[:,:,1]-(ey+1))*(crop.height-split)/hl)-.5
        alpha=arr[:,:,3]/255;channels=[]
        for ci in range(3):channels.append(map_coordinates(arr[:,:,ci]*alpha,[sy,sx],order=1,mode='constant',cval=0))
        aa=map_coordinates(alpha,[sy,sx],order=1,mode='constant',cval=0);rgba=np.zeros((size*scale,size*scale,4),np.uint8)
        for ci in range(3):rgba[:,:,ci]=np.round(np.array(channels[ci])/np.maximum(aa,.00001)).clip(0,255).astype(np.uint8)
        rgba[:,:,3]=np.round(aa*255).astype(np.uint8)
        native=register(Image.fromarray(rgba),(size,size),palette,'area_vote');target=np.zeros((384,384),np.uint8);target[120:200,120:200]=native
        # Source iris is explicitly tied to the established eye pixel.
        ex,ey=map(int,p['eye_world']);target[ey+160,ex+160]=14
        Image.fromarray(target).save(out/f'base_{n:03}.png');a.rgba(target).save(out/f'base_{n:03}_rgba.png')
        rows.append((f'wall {n}',[('idle',a.composite(0)[0]),('current',a.composite(n)[0]),('new source v1',a.rgba(old)),('contact alignment',a.rgba(target))]))
        Y,X=np.indices(target.shape);mask=np.isin(target,[10,11,12,13])&(X>168)&(Y<155);py,px=np.nonzero(mask)
        ty,tx=np.nonzero(target);records.append({'ref':n,'source_points':source,'target_points':dst.tolist(),'mesh_area_ratio_bounds':[min(ratios),max(ratios)],'eye':[ex,ey],'native_foot_max_y':int(ty.max()-160),'right_hand_skin_bbox':[int(px.min()-160),int(py.min()-160),int(px.max()-160),int(py.max()-160)]if len(px)else None,'native_bbox':[int(tx.min()-160),int(ty.min()-160),int(tx.max()+1-160),int(ty.max()+1-160)],'source_sha256':digest(source_dir/'generated.png'),'old_art_pixels_used':0,'indexed_sha256':sha(target.tobytes())})
    helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'source_arc_sha256':sha(a.data),'frames':records,'scope':'New art only; source coordinate registration, no old lower-body/head overlay','native_packed':False,'runtime_verified':False})
    print(json.dumps({'out':str(out)}))

if __name__=='__main__':main()
