"""Source-derived air bodies/arms and partial-costume registration review."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(D.parent/'native_restore'),str(D)]
from preview_restore import Archive,sha,need,write,helper,digest
from review_all_bodies import source as body_source

def shot_source(n):
    return D/('firing_a_joint_probe_v1'if n<=40 else'firing_b_joint_probe_v2'if n<=48 else'landing_reach_joint_v1'if n<=52 else'landing54_probe_v2')
def fourth_source(n):return D/('fourth45_contacts_probe_v5'if n==45 else'fourth_contacts_probe_v3')
def spans(row):
    xs=np.flatnonzero(row);return np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)if len(xs)else[]
def load(p):return np.array(Image.open(p))
def quantize_rgba_row(crop,width,palette):
    z=np.array(crop);alpha=z[:,:,3].astype(np.float32)/255;rgb=z[:,:,:3].astype(np.float32);ids=1+((rgb[:,:,None,:]-palette[None,None,1:,:])**2).sum(3).argmin(2)
    votes=np.stack([np.array(Image.fromarray(np.where(ids==i,alpha,0).astype(np.float32),'F').resize((width,1),Image.Resampling.BOX))for i in range(1,16)])
    coverage=np.array(Image.fromarray(alpha,'F').resize((width,1),Image.Resampling.BOX));need(np.all(coverage>.02),'No authored RGBA coverage');return (1+votes.argmax(0).astype(np.uint8))[0],coverage[0].tolist()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='joint_layers_probe_v1');ap.add_argument('--lower-mode',choices=['intersection','preserve_base','semantic_legs','semantic_rgba'],default='intersection');args=ap.parse_args();out=D/args.out;need(not out.exists(),'Fresh candidate');out.mkdir()
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(a.data)==plan['parent_arc_sha256'],'Parent');Y,X=np.indices((384,384));x=X-160;y=Y-160;reports=[];rows=[]
    # Explicit leg region excludes the trailing hair and veil. This is only
    # a registration proposal; no source span may be silently discarded.
    xmax={33:11,35:13,37:11,39:12,41:11,43:16,45:14,47:14,49:13,51:14,53:12}
    for n in range(33,54,2):
        b=load(body_source(n)/f'base_{n:03}.png');f=load(fourth_source(n)/f'fourth_{n:03}.png');base=b.copy();q=next(q for q in plan['frames']if q['ref']==n);ex,ey=map(lambda v:int(np.floor(v)),q['eye']);links=[];unmatched=[]
        region=(y>=ey+17)&(x<=xmax[n])
        source_fourth=f.copy()
        if args.lower_mode=='preserve_base':f[region]=0
        leg_source=source_fourth.copy();garment=None
        rgba_field=Image.open(D/'fourth_contacts_rgba_v6'/f'fourth_{n:03}_source_rgba8.png').convert('RGBA')if args.lower_mode=='semantic_rgba'else None
        rgba_links=[];palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32)
        if args.lower_mode in('semantic_legs','semantic_rgba'):
            seed=np.isin(f,[10,11,12])&(y>=ey+13)&(x<=xmax[n])
            feet={33:[(0,19),(5,21)],35:[(-1,10),(9,20)],37:[(2,12),(6,16)],39:[(9,14)],41:[(2,8),(6,17)],43:[(11,14)],45:[(5,14),(10,15)],47:[(3,18),(9,17)],49:[(-5,21),(10,21)],51:[(-7,20),(10,20)],53:[(-7,21),(8,21)]}[n]
            nearfeet=np.zeros_like(seed)
            for fx,fy in feet:nearfeet|=(x-fx)**2+(y-fy)**2<=16
            seed|=np.isin(f,[5,6])&nearfeet
            legmask=binary_dilation(seed,np.ones((3,3)))&(f>0)&(y>=ey+13)&(x<=xmax[n])
            leg_source=np.where(legmask,f,0);garment=np.where(legmask,0,f);f=garment.copy()
        for py in range(160+ey+17,384):
            for segment in spans((b[py]>0)&region[py]):
                if garment is not None and np.all(garment[py,segment]>0):continue
                if args.lower_mode in('preserve_base','semantic_legs','semantic_rgba'):
                    options=[]
                    for sy0 in range(max(0,py-2),min(384,py+3)):
                        for src in spans((leg_source[sy0]>0)&(x[sy0]<=xmax[n])):
                            gap=max(int(segment[0]-src[-1]),int(src[0]-segment[-1]),0)
                            if gap>3:continue
                            options.append((gap*10+abs(float(np.mean(segment)-np.mean(src)))+abs(py-sy0)*1.5,sy0,src))
                    need(options,f'No same-leg Fourth source {n}/{py-160}/{segment.tolist()}');_,sy0,src=min(options,key=lambda z:z[0]);samples=np.rint(np.linspace(0,len(src)-1,len(segment))).astype(int);f[py,segment]=leg_source[sy0,src[samples]]
                    if rgba_field is not None:
                        box=((int(src[0])-120)*8,(sy0-120)*8,(int(src[-1])+1-120)*8,(sy0+1-120)*8);values,coverage=quantize_rgba_row(rgba_field.crop(box),len(segment),palette);f[py,segment]=values;rgba_links.append({'target':[int(segment[0])-160,py-160,int(segment[-1])+1-160],'source_rgba8_box':box,'coverage':coverage})
                    links.extend([[int(px-160),py-160,int(sx-160),sy0-160,int(leg_source[sy0,sx])]for px,sx in zip(segment,src[samples])]);continue
                dest=segment[f[py,segment]>0]
                if not len(dest):unmatched.append([py-160,int(segment[0]-160),int(segment[-1]-160)]);continue
                base[py,segment]=0;samples=np.rint((dest-dest[0])*(len(segment)-1)/max(1,dest[-1]-dest[0])).astype(int);base[py,dest]=b[py,segment[samples]]
                links.extend([[int(px-160),py-160,int(sx-160),int(b[py,sx])]for px,sx in zip(dest,segment[samples])])
        if garment is not None:
            f=np.where(garment,garment,f);f[(y<ey+17)&(source_fourth>0)]=source_fourth[(y<ey+17)&(source_fourth>0)]
        palm_window=None
        if n==37:palm_window=(x>=7)&(x<=13)&(y<=-12)
        if n==39:palm_window=(x>=2)&(x<=9)&(y<=-24)
        if n==41:palm_window=(x>=0)&(x<=9)&(y<=-25)
        if palm_window is not None:
            # Shared new-art palm, not old-game hand; do not draw two displaced
            # hands when the same limb is visible through a transparent overlay.
            f[palm_window]=b[palm_window]
        changed=base!=b;need(not np.any(changed&~region),'Base upper/hair exact');display={}
        for ref in(n,n+1):
            body=base.copy();costume=f.copy();front_arm=None
            if ref%2==0:
                sd=shot_source(ref);body=load(sd/f'merged_{ref:03}.png');body[changed]=base[changed];front_arm=load(sd/f'new_sleeve_{ref:03}.png');qr=next(q for q in plan['frames']if q['ref']==ref);sx,sy=map(lambda v:int(np.floor(v)),qr['eye']);head=(x>=sx-2)&(y<=sy+5);end=16 if 42<=ref<=48 else 14
                remove=(x<=sx+1)&(y>=sy+4)&(y<sy+end)&~head
                if ref==54:remove=(x<=-4)&(y>=-6)&(y<=3)
                costume[remove]=0;costume[front_arm>0]=front_arm[front_arm>0]
                gun=load(D/'fire_constraints'/f'barrel_{ref:03}.png');gy,gx=np.nonzero(gun);win=(X>=gx.min())&(X<=gx.min()+7)&(Y>=gy.min())&(Y<=gy.max());costume[win]=gun[win];body[win]=gun[win]
                need(np.array_equal(body[win],gun[win])and np.array_equal(costume[win],gun[win]),'Full gun window')
            full=np.where(costume,costume,body).astype(np.uint8)
            head=(y<ey+4)&((x>=ex-3)|(y<ey))
            leg=(y>=ey+17)|((x>=ex+14)&(y>=ey+4))
            front=(x<ex+3)&(y>=ey)&(y<ey+17)&~head
            owner=np.full((384,384),6,np.uint8);owner[leg]=8;owner[head]=5;owner[front]=7
            # Rear raised arms in 37/39/41 are independently owned by arms.
            if n in(37,39,41):
                palm={37:(11,-13),39:(6,-24),41:(6,-22)}[n];shoulder=np.array([ex+6,ey+6],float);v=np.array(palm)-shoulder;t=np.clip(((x-shoulder[0])*v[0]+(y-shoulder[1])*v[1])/float(v@v),0,1);dist=(x-shoulder[0]-t*v[0])**2+(y-shoulder[1]-t*v[1])**2;owner[(dist<10)&(x>ex+4)]=7
            if front_arm is not None:owner[front_arm>0]=7
            pc=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full];diff=((full!=body)|((costume>0)&pc))&(full>0);layers={pb:np.where(diff&(owner==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}
            merged=body.copy()
            for pb in(8,5,7,6):merged=np.where(layers[pb],layers[pb],merged)
            need(np.array_equal(merged,full),'Layer reconstruction')
            for pb,idx in{0:body,**layers}.items():Image.fromarray(idx).save(out/f'layer{pb}_{ref:03}.png')
            Image.fromarray(full).save(out/f'full_{ref:03}.png');Image.fromarray(owner).save(out/f'owner_{ref:03}.png');rgba=a.rgba(body);rgba.alpha_composite(a.rgba(costume,16));display[ref]=[a.rgba(body),rgba]
            reports.append({'ref':ref,'lower_mode':args.lower_mode,'new_body_source':(body_source(n)/f'base_{n:03}.png').relative_to(ROOT).as_posix(),'fourth_source':(fourth_source(n)/f'fourth_{n:03}.png').relative_to(ROOT).as_posix(),'base_sha256':sha(body.tobytes()),'full_sha256':sha(full.tobytes()),'common_lower_source_links':links if ref==n else None,'rgba_source_links':rgba_links if ref==n else None,'unmatched_spans_preserved_for_review':unmatched if ref==n else None,'base_alpha_components_8':label(body>0,np.ones((3,3)))[1],'full_alpha_components_8':label(full>0,np.ones((3,3)))[1],'layers':{str(pb):sha(v.tobytes())for pb,v in layers.items()},'native_packed':False})
        rows.append((f'air {n}/{n+1}',[('새 기본 원안',a.rgba(b)),('기본 공통 접점',display[n][0]),('새 기본 사격',display[n+1][0]),('새 포스',display[n][1]),('새 포스 사격',display[n+1][1])]))
    for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',6)
    write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':reports,'scope':'공통 하체 외곽 및 새 사격팔의 부분파츠 분류 검토본. 미해결 행을 삭제하지 않고 명시. 네이티브 패킹/실기 전.','ready_to_apply':False,'runtime_verified':False});print(json.dumps({'out':str(out),'frames':len(reports),'unmatched_spans':sum(len(r['unmatched_spans_preserved_for_review']or[])for r in reports)}))
if __name__=='__main__':main()
