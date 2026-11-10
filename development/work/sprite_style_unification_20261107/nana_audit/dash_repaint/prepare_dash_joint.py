"""새 원화만 사용한 대시 기본/포스 파츠 합성 후보. 미일치 행은 거부한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore'),str(D.parent/'air_repaint')]
from preview_restore import Archive,sha,need,write,helper,digest
from prepare_air_joint_layers import spans,quantize_rgba_row
sys.path.insert(0,str(D))
from prepare_next_guides import body_path
from register_arm_reach_joint import OLD_HAND_BOXES
REFS=(67,69,71,75,77,79,81,83,93,94)
def load(p):return np.array(Image.open(p))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='joint_layers_probe_v1');args=ap.parse_args();out=D/args.out;need(not out.exists(),'Fresh candidate');out.mkdir()
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(a.data)==plan['parent_arc_sha256'],'Parent');Y,X=np.indices((384,384));x=X-160;y=Y-160;reports=[];rows=[];palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32)
    for n in REFS:
        b=load(body_path(n));f=load(D/'fourth_contacts_probe_v2'/f'fourth_{n:03}.png');src=f.copy();rgba=Image.open(D/'fourth_contacts_probe_v2'/f'source_rgba8_{n:03}.png').convert('RGBA');q=next(q for q in plan['frames']if q['ref']==n);ex,ey=[int(np.floor(v))for v in q['eye']];start=ey+17
        # Below the skirt this range is legs only, excluding the trailing veil.
        # Any newly covered base-boot pixel is sampled from this pose's authored
        # bare leg/shoe, never a constant skin fill or a different pose.
        xmax={67:22,69:12,71:14,75:13,77:18,79:21,81:33,83:20,93:14,94:33}[n]
        links=[];missing=[]
        for py in range(160+start,200):
            for dest in spans((b[py]>0)&(x[py]<=xmax)):
                if np.all(f[py,dest]>0):continue
                options=[]
                for sy in range(max(160+start,py-2),min(200,py+3)):
                    for sg in spans((src[sy]>0)&(x[sy]<=xmax)):
                        gap=max(int(dest[0]-sg[-1]),int(sg[0]-dest[-1]),0)
                        if gap>4:continue
                        options.append((gap*10+abs(float(dest.mean()-sg.mean()))+abs(py-sy)*2,sy,sg))
                if not options:missing.append([py-160,int(dest[0]-160),int(dest[-1]-160)]);continue
                _,sy,sg=min(options,key=lambda z:z[0]);box=((int(sg[0])-120)*8,(sy-120)*8,(int(sg[-1])+1-120)*8,(sy+1-120)*8)
                values,coverage=quantize_rgba_row(rgba.crop(box),len(dest),palette)
                f[py,dest]=values;links.append({'target':[int(dest[0]-160),py-160,int(dest[-1]+1-160)],'source_rgba8_box':box,'coverage':coverage})
        display={};refs=(n,n+1)if n<93 else(n,)
        for ref in refs:
            body=b.copy();costume=f.copy();arm=None
            if ref%2==0 and ref<93:
                sd=D/'firing_reach_joint_v3';body=load(sd/f'merged_{ref:03}.png');arm=load(sd/f'new_sleeve_{ref:03}.png');head=(x>=ex-2)&(y<=ey+5)
                remove=(((x<=ex+2)&(y>=ey+8)&(y<ey+15))|((x<=ex-2)&(y>=ey+3)&(y<ey+8)))&~head
                if ref in OLD_HAND_BOXES:
                    xx0,yy0,xx1,yy1=OLD_HAND_BOXES[ref];remove|=(x>=xx0)&(x<xx1)&(y>=yy0)&(y<yy1)&~head
                costume[remove]=0;costume[arm>0]=arm[arm>0]
                gun=load(D/'fire_constraints'/f'barrel_{ref:03}.png');gy,gx=np.nonzero(gun);win=(X>=gx.min())&(X<=gx.min()+7)&(Y>=gy.min())&(Y<=gy.max());costume[win]=gun[win];body[win]=gun[win]
            full=np.where(costume,costume,body).astype(np.uint8)
            head=(y<ey+4)&((x>=ex-3)|(y<ey));leg=(y>=ey+17)|((x>=ex+14)&(y>=ey+4));front=(x<ex+3)&(y>=ey)&(y<ey+17)&~head
            owner=np.full((384,384),6,np.uint8);owner[leg]=8;owner[head]=5;owner[front]=7
            if arm is not None:owner[arm>0]=7
            if n in(93,94):
                shoulder=np.array([ex+7,ey+5]);palm=np.array([5,-19]if n==93 else[13,-12]);v=palm-shoulder;t=np.clip(((x-shoulder[0])*v[0]+(y-shoulder[1])*v[1])/float(v@v),0,1);dist=(x-shoulder[0]-t*v[0])**2+(y-shoulder[1]-t*v[1])**2;owner[(dist<8)&(x>ex+5)]=7
            pc=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full];diff=((full!=body)|((costume>0)&pc))&(full>0);layers={pb:np.where(diff&(owner==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}
            merged=body.copy()
            for pb in(8,5,7,6):merged=np.where(layers[pb],layers[pb],merged)
            need(np.array_equal(merged,full),'Layer reconstruction')
            for pb,ar in{0:body,**layers}.items():Image.fromarray(ar).save(out/f'layer{pb}_{ref:03}.png')
            Image.fromarray(full).save(out/f'full_{ref:03}.png');Image.fromarray(owner).save(out/f'owner_{ref:03}.png');real=a.rgba(body);real.alpha_composite(a.rgba(costume,16));display[ref]=[a.rgba(body),real]
            reports.append({'ref':ref,'base_source':str(body_path(n).relative_to(ROOT)),'source_rgba_links':links if ref==n else None,'unresolved_rows':missing,'body_sha256':sha(body.tobytes()),'full_sha256':sha(full.tobytes()),'alpha_components_8':int(label(full>0,np.ones((3,3)))[1]),'layers':{str(pb):sha(ar.tobytes())for pb,ar in layers.items()}})
        cols=[('새 기본',a.rgba(b)),('포스 직접등록',a.rgba(src,16)),('공통 포스',display[n][1])]
        if n<93:cols.extend([('기본 사격',display[n+1][0]),('포스 사격',display[n+1][1])])
        else:cols.extend([('기본 대기',a.composite(0)[0]),('포스 대기',a.composite(0,15)[0])])
        rows.append((f'dash {n}',cols))
    for k in range(0,len(rows),3):helper.grid(rows[k:k+3],out/f'comparison_{k//3+1}.png',6)
    write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':reports,'runtime_verified':False,'native_packed':False,'scope':'새 원화 공통 합성 검토용. 미일치 행이 있으면 패킹 불가.'});print(json.dumps({'unresolved':{r['ref']:r['unresolved_rows']for r in reports if r['unresolved_rows']},'out':str(out)}))
if __name__=='__main__':main()
