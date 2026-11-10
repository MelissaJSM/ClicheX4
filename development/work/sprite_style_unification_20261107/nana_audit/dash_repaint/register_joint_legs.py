"""같은 자세의 각 다리에서 허벅지/종아리/구두의 순서를 보존해 정합."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,binary_erosion
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper,digest
from prepare_next_guides import body_path
# Four anchors are authored thigh, knee, ankle and toe. Each target/source pair
# refers to the SAME limb. No cross-leg or cross-material nearest fallback.
PATHS={
67:([[[0,9],[-4,12],[1,19],[0,22]],[[7,10],[10,14],[15,20],[16,22]]],[[[-5,9],[-6,12],[1,19],[0,22]],[[7,11],[11,15],[16,20],[16,22]]],9),
69:([[[-7,12],[-10,14],[5,19],[7,22]]],[[[-6,12],[-9,15],[5,19],[6,22]]],11),
71:([[[-5,17],[-8,19],[1,20],[3,22]],[[-1,17],[3,18],[5,19],[7,21]]],[[[-8,17],[-10,20],[2,20],[4,22]],[[0,17],[3,18],[4,19],[5,21]]],16),
75:([[[-5,17],[-4,19],[3,20],[4,22]],[[-1,16],[1,17],[6,18],[7,20]]],[[[-4,17],[-4,19],[5,20],[6,22]],[[1,16],[3,17],[5,19],[6,20]]],16),
77:([[[-3,8],[-5,10],[5,18],[6,21]],[[0,9],[6,13],[12,19],[13,22]]],[[[-4,9],[-4,12],[5,19],[5,22]],[[1,10],[6,14],[12,20],[12,22]]],8),
79:([[[0,7],[-1,9],[4,14],[4,16]],[[5,9],[8,14],[11,20],[11,22]]],[[[-1,8],[-2,10],[6,16],[6,17]],[[4,10],[8,14],[11,20],[11,22]]],6),
81:([[[9,7],[7,11],[7,18],[4,20]],[[19,8],[21,13],[24,20],[24,22]]],[[[8,7],[7,11],[5,18],[3,20]],[[20,9],[24,13],[27,20],[27,22]]],6),
83:([[[-5,8],[-5,12],[-6,18],[-6,21]],[[6,9],[8,13],[10,20],[10,22]]],[[[-4,8],[-5,12],[-6,18],[-6,21]],[[5,10],[8,13],[11,20],[11,22]]],7),
93:([[[-1,5],[-2,9],[6,14],[6,17]],[[3,6],[5,10],[8,11],[9,12]]],[[[-2,5],[-2,9],[6,14],[6,17]],[[2,6],[3,9],[3,10],[4,11]]],4),
94:([[[10,1],[18,4],[26,8],[27,11]],[[7,1],[6,3],[13,4],[16,4]]],[[[10,1],[18,4],[26,8],[27,11]],[[7,1],[6,3],[11,3],[14,4]]],0)}
def project(points,path):
    candidates=[]
    for seg,(aa,bb)in enumerate(zip(path[:-1],path[1:])):
        aa=np.array(aa,float);bb=np.array(bb,float);v=bb-aa;length=np.linalg.norm(v);t=np.clip(((points-aa)*v).sum(-1)/(length*length),0,1);center=aa+t[...,None]*v;normal=np.array([-v[1],v[0]])/length;perp=((points-center)*normal).sum(-1);dist=((points-center)**2).sum(-1);candidates.append((dist,t+seg,perp))
    best=np.argmin(np.stack([z[0]for z in candidates]),axis=0)
    return tuple(np.choose(best,np.stack([z[i]for z in candidates]))for i in range(3))
def fields(mask,paths):
    yy,xx=np.nonzero(mask);pts=np.stack((xx-160,yy-160),1).astype(float);allp=[project(pts,p)for p in paths];owner=np.argmin(np.stack([q[0]for q in allp]),axis=0)
    return pts,owner,allp
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='joint_leg_material_v1');ap.add_argument('--skip',default='71,75');ap.add_argument('--material',action='store_true');args=ap.parse_args();skip={int(v)for v in args.skip.split(',')if v}
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],float);out=D/args.out;need(not out.exists(),'Fresh output');out.mkdir();Y,X=np.indices((384,384));reports=[];rows=[]
    for n,(bp,fp,start)in PATHS.items():
        if n in skip:continue
        b=np.array(Image.open(body_path(n)));f=np.array(Image.open(D/'fourth_contacts_probe_v2'/f'fourth_{n:03}.png'));src=f.copy();rgba=np.array(Image.open(D/'fourth_contacts_probe_v2'/f'source_rgba8_{n:03}.png').convert('RGBA'));bm=(b>0)&(Y>=160+start);fm=(f>0)&(Y>=160+start)
        bpts,bown,bproj=fields(bm,bp);fpts,fown,fproj=fields(fm,fp);need(len(bpts)>0 and len(fpts)>0,'Leg data');mapped=[];fallback=[]
        # Restrict these masks to the explicit articulated legs. Distant hair
        # and hem points stay in their original authored locations.
        bkeep=np.min(np.stack([q[0]for q in bproj]),axis=0)<=36;fkeep=np.min(np.stack([q[0]for q in fproj]),axis=0)<=36
        chosen=fkeep.copy()
        if args.material:chosen&=np.choose(fown,np.stack([z[1]for z in fproj]))>=1
        clear=fpts[chosen].astype(int)+160;f[clear[:,1],clear[:,0]]=0
        boundary=bm&~binary_erosion(bm,np.ones((3,3)));fcolors=src[(fpts[:,1]+160).astype(int),(fpts[:,0]+160).astype(int)]
        for k,pt in enumerate(bpts):
            if not bkeep[k]:continue
            own=int(bown[k]);_,t,pdist=(v[k]for v in bproj[own]);sameb=(bown==own)&bkeep;near=sameb&(np.abs(bproj[own][1]-t)<.28)
            if args.material and t<1:continue
            if np.count_nonzero(near)<2:near=sameb&(np.abs(bproj[own][1]-t)<.6)
            lo=float(np.min(bproj[own][2][near]))-.5;hi=float(np.max(bproj[own][2][near]))+.5;u=np.clip((pdist-lo)/max(1,hi-lo),.02,.98)
            samef=(fown==own)&fkeep;distance=np.abs(fproj[own][1]-t);eligible=samef&(distance<.3)
            if not eligible.any():
                tt=float(distance[samef].min());need(tt<.85,f'Same segment missing {n}/{own}/{t}');eligible=samef&(distance<=tt+.12);fallback.append([int(pt[0]),int(pt[1]),own,float(t),tt])
            slo=float(np.min(fproj[own][2][eligible]))-.45;shi=float(np.max(fproj[own][2][eligible]))+.45;seg=min(2,int(t));tt=min(1.,t-seg);aa=np.array(fp[own][seg],float);bb=np.array(fp[own][seg+1],float);v=bb-aa;normal=np.array([-v[1],v[0]])/np.linalg.norm(v);sp=aa+tt*v+normal*(slo+u*(shi-slo))
            # Sample the authored high-resolution field, keeping premultiplied
            # alpha and checking coverage. If an edge is nearly transparent,
            # retreat along the SAME cross-section, not toward another limb.
            got=None
            for shrink in(1.,.8,.6,.4,.2,0.):
                point=aa+tt*v+normal*(slo+u*(shi-slo))*shrink;xy=(point+40)*8+4;sy,sx=xy[1],xy[0];alpha=float(map_coordinates(rgba[:,:,3].astype(float),[[sy],[sx]],order=1,mode='constant',cval=0)[0])/255
                if alpha>.35:
                    color=np.array([float(map_coordinates(rgba[:,:,c].astype(float)*rgba[:,:,3]/255,[[sy],[sx]],order=1,mode='constant',cval=0)[0])/alpha for c in range(3)]);idx=1+int(((pal[1:]-color)**2).sum(1).argmin());got=(idx,point,alpha,shrink);break
            if got is None:
                # An exact same-limb, same segment native source cell can be
                # chosen when the curved source crosses a linear guide. Its
                # authored RGBA is sampled; colour is never fabricated.
                cand=np.flatnonzero(eligible)
                score=np.linalg.norm(fpts[cand]-sp,axis=1)+distance[cand]*4
                for ci in cand[np.argsort(score)]:
                    point=fpts[ci];xy=(point+40)*8+4;sy,sx=xy[1],xy[0];alpha=float(map_coordinates(rgba[:,:,3].astype(float),[[sy],[sx]],order=1,mode='constant',cval=0)[0])/255
                    if alpha<=.35:continue
                    color=np.array([float(map_coordinates(rgba[:,:,c].astype(float)*rgba[:,:,3]/255,[[sy],[sx]],order=1,mode='constant',cval=0)[0])/alpha for c in range(3)]);idx=1+int(((pal[1:]-color)**2).sum(1).argmin());got=(idx,point,alpha,-1.);break
            if got is None:raise ValueError(f'No authored same-leg coverage {n} at {pt.tolist()} t={t} source={sp.tolist()}')
            idx,point,alpha,shrink=got;xx,yy=(pt+160).astype(int);f[yy,xx]=idx;mapped.append({'target':pt.astype(int).tolist(),'leg':own,'segment_t':float(t),'source_rgba8':((point+40)*8+4).tolist(),'alpha':alpha,'normal_retreat':shrink,'index':idx})
            if args.material and 1<=t<2:
                if boundary[yy,xx] and b[yy,xx]==1:
                    f[yy,xx]=1;mapped[-1].update(index=1,source_base_outline=True);continue
                candidates=np.flatnonzero(samef&np.isin(fcolors,[10,11,12]))
                need(len(candidates)>0,f'Authored skin segment {n}/{own}')
                score=np.abs(fproj[own][1][candidates]-t)*5+np.linalg.norm(fpts[candidates]-sp,axis=1)
                found=None
                for ci in candidates[np.argsort(score)]:
                    ss=fpts[ci].astype(int);box=((ss[0]+40)*8,(ss[1]+40)*8,(ss[0]+41)*8,(ss[1]+41)*8);tile=rgba[box[1]:box[3],box[0]:box[2]];aa=tile[:,:,3].astype(float)/255;rgb=tile[:,:,:3].astype(float);ids=1+((rgb[:,:,None,:]-pal[None,None,1:,:])**2).sum(3).argmin(2);votes=np.array([aa[ids==v].sum()for v in(10,11,12)])
                    if votes.sum()<8:continue
                    idx=(10,11,12)[int(votes.argmax())];found=(idx,box,votes.tolist(),float(fproj[own][1][ci]));break
                need(found is not None,f'RGBA skin coverage {n}/{own}')
                idx,box,votes,tt=found;f[yy,xx]=idx;mapped[-1].update(index=idx,authored_skin_rgba_box=box,skin_votes=votes,source_segment_t=tt)
        Image.fromarray(f).save(out/f'fourth_{n:03}.png');a.rgba(f,16).save(out/f'fourth_{n:03}_rgba.png');reports.append({'ref':n,'base_paths':bp,'fourth_paths':fp,'leg_start':start,'source_rgba_sha256':digest(D/'fourth_contacts_probe_v2'/f'source_rgba8_{n:03}.png'),'mapped':mapped,'same_leg_t_fallback':fallback,'before':sha(src.tobytes()),'after':sha(f.tobytes())});rows.append((f'{n} 같은 다리 구간 정합',[('기본',a.rgba(b)),('포스 원화등록',a.rgba(src,16)),('구간 후보',a.rgba(f,16))]))
    for k in range(0,len(rows),3):helper.grid(rows[k:k+3],out/f'comparison_{k//3+1}.png',7)
    write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':reports,'native_packed':False,'runtime_verified':False});print(str(out))
if __name__=='__main__':main()
