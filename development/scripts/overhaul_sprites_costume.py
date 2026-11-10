"""C03: prepare one-character costume edit batches from actual BIN frames."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import D,entry,render,rgba,write,sha,BASES
from scripts.prepare_rin_run import quantize
from scripts.extract_zero import save_image

GROUPS={
 'run_shot':list(range(2,33,2)),
 'air':list(range(33,55))+[93,94],
 'wall_dash':list(range(55,85)),
 'special':[87,88,89,90,91,95,96,97,98,99,100,101,102,103,104,231,232],
 'reaction':[106,107,108,109,110,111,112,113,114,120,121,122,123,124,125,233,234,235,236],
 'ladder':list(range(143,156))+[183],
 'stage_vehicle':[135,136,137,138,139,141,142,156,162,166,170,174,204,205,206,207,213,214,215,216]
}

def full(arc,n):
    base,_=render(arc,0,0,n);out=base.copy();over=np.zeros_like(base)
    for b in(8,5,7,6):
        a,_=render(arc,0,b,n);over[a>0]=a[a>0];out[a>0]=a[a>0]
    return base,out,over

def base_palette_colors(project,n,palette):
    # The acquired form uses multiple CLUT rows; the pre-state uses row0.
    # Register retained head/leg RGB through that palette rather than copying
    # a different row's numeric index (which could turn a navy outline red).
    image=np.array(Image.open(D/f'{project}/x_ultimate/{n:03}.png').convert('RGBA'));out=np.zeros(image.shape[:2],np.uint8)
    colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in palette[1:16]],np.int32)
    opaque=image[:,:,3]>0
    values,inverse=np.unique(image[:,:,:3][opaque],axis=0,return_inverse=True);ids=np.argmin(((values.astype(np.int32)[:,None]-colors[None])**2).sum(axis=2),axis=1)+1
    out[opaque]=ids[inverse];return out

def plan(project):
    folder=D/('nana_preultimate'if project=='ver_rin_nana'else'shibuki_preultimate');folder.mkdir(exist_ok=True)
    arc=(D/project/'baseline/PL02_U.ARC').read_bytes();pal=struct.unpack_from('<64H',entry(arc,9))
    all_frames={};aliases={};pages=[]
    for group,ids in GROUPS.items():
        unique=[];seen={}
        for n in ids:
            b,a,o=full(arc,n);key=sha(a.tobytes())
            if key in seen:aliases[n]=seen[key];continue
            seen[key]=n;unique.append(n)
            y,x=np.nonzero(a);box=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
            eyes=np.argwhere((a==14)&(np.indices(a.shape)[0]<180))
            all_frames[n]={'bbox':box,'full_sha256':key,'eye_candidates':(eyes[:,::-1]-160).tolist()}
        for j in range(0,len(unique),16):
            order=unique[j:j+16];rows=(len(order)+3)//4;sheet=Image.new('RGBA',(1024,rows*256))
            for i,n in enumerate(order):
                image=Image.open(D/f'{project}/x_ultimate/{n:03}.png').convert('RGBA')
                box=all_frames[n]['bbox'];w,h=box[2]-box[0],box[3]-box[1]
                # Fixed 3x native scale, enough room for both ordinary poses and local effects.
                cell=image.crop((int((box[0]+box[2])/2)-42,int((box[1]+box[3])/2)-42,int((box[0]+box[2])/2)+43,int((box[1]+box[3])/2)+43)).resize((255,255),Image.Resampling.NEAREST)
                sheet.alpha_composite(cell,(i%4*256,i//4*256))
            name=f'{group}_{j//16:02}';path=folder/f'{name}_target.png';sheet.save(path);pages.append({'name':name,'frames':order,'columns':4,'rows':rows,'target':path.relative_to(ROOT).as_posix(),'generated':(folder/f'{name}_generated.png').relative_to(ROOT).as_posix()})
    report={'project':project,'baseline':BASES[project][0],'source_arc_sha256':sha(arc),'frames':all_frames,'aliases':aliases,'pages':pages,'special_derived':'Idle breathing/blink; teleport light; heads; full armor-only moves handled separately.'}
    write(folder/'production_plan.json',report);print(json.dumps({'pages':[(p['name'],p['frames'])for p in pages],'aliases':aliases}))

def normalize(project):
    folder=D/('nana_preultimate'if project=='ver_rin_nana'else'shibuki_preultimate');info=json.loads((folder/'production_plan.json').read_text('utf8'))
    arc=(D/project/'baseline/PL02_U.ARC').read_bytes()
    if sha(arc)!=info['source_arc_sha256']:raise ValueError('Source changed')
    pal=struct.unpack_from('<64H',entry(arc,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:16]],np.int32)
    pages=[{'name':'pilot','frames':[0,85,1,33],'columns':2,'rows':2,'generated':str((folder/'generated.png').relative_to(ROOT))},{'name':'run','frames':list(range(1,33,2)),'columns':4,'rows':4,'generated':str((folder/'generated_run.png').relative_to(ROOT))},*info['pages']]
    out=folder/'normalized';out.mkdir(exist_ok=True);reports=[];failures=[];targets={};yy,xx=np.indices((384,384))
    for page in pages:
        path=ROOT/page['generated']
        if not path.exists():continue
        image=Image.open(path).convert('RGBA');items=[]
        for i,n in enumerate(page['frames']):
            base,current,over=full(arc,n);retained=base_palette_colors(project,n,pal)
            if not np.any(over):
                failures.append({'frame':n,'reason':'No acquired overlay: separate shared-state design needed'});continue
            crop=image.crop((i%page['columns']*image.width//page['columns'],i//page['columns']*image.height//page['rows'],(i%page['columns']+1)*image.width//page['columns'],(i//page['columns']+1)*image.height//page['rows']))
            data=np.array(crop);lab,count=label(data[:,:,3]>=224,np.ones((3,3)));sizes=np.bincount(lab.flat);sizes[0]=0
            if not sizes.max():raise ValueError('Missing generated pose')
            mask=lab==int(sizes.argmax());gy,gx=np.nonzero(mask);data[~mask,3]=0;data[mask,3]=255;crop=Image.fromarray(data).crop((gx.min(),gy.min(),gx.max()+1,gy.max()+1))
            cy,cx=np.nonzero(current);top,bottom=int(cy.min()),int(cy.max());left,right=int(cx.min()),int(cx.max())
            a=quantize(crop,colors,(bottom-top+1)/crop.height);ah,aw=a.shape;dx=left+round((right-left+1-aw)/2);dy=bottom+1-ah
            target=np.zeros_like(current);target[dy:dy+ah,dx:dx+aw]=a
            eye_index=14 if project=='ver_rin_nana'else 7
            eye_region=(current==eye_index)&(yy<top+(bottom-top+1)*.65)
            if project=='ver_buki_riko':eye_region&=yy>=top+10
            ey,ex=np.nonzero(eye_region)
            if len(ex):
                eye_x=int(round(float(np.median(ex))));eye_y=int(round(float(np.median(ey))))
                head=(xx>=eye_x-7)&(xx<=eye_x+18)&(yy<eye_y+6)
                hip=eye_y+17
                if 67<=n<=84:hip=eye_y+({69:14,70:14,71:8,72:8,75:8,76:8}.get(n,17))
                lower=yy>=hip+3
                gun=(current>0)&(xx<eye_x-9)&(yy>=eye_y)&(yy<=eye_y+11)
                if np.any(gun):
                    gun_x=int(np.nonzero(gun)[1].min());gun=(xx>=gun_x)&(xx<gun_x+8)&(yy>=eye_y-1)&(yy<=eye_y+11)
                else:gun=np.zeros_like(current,bool)
                keep=head|lower|gun;target[keep]=retained[keep]
            else:
                eye_x=eye_y=None;keep=(yy<=top+15)|(yy>=bottom-3);target[keep]=retained[keep]
            target[over==0]=base[over==0]
            if not np.array_equal(np.where(over,over,target),current):raise ValueError('Acquired display differs')
            targets[n]=target;save_image(target.tobytes(),(384,384),pal,out/f'{n:03}.png')
            items.append((str(n),rgba(target,pal)))
            reports.append({'frame':n,'page':page['name'],'generated_sha256':sha(path.read_bytes()),'eye_world':None if eye_x is None else[eye_x-160,eye_y-160],'uniform_scale':(bottom-top+1)/crop.height,'acquired_exact':True,'kept_pixels':int(keep.sum()),'bbox_before':[left,top,right+1,bottom+1]})
        from scripts.overhaul_sprites_audit import board
        board(items,out/(page['name']+'_review.png'),cols=4)
    for key,value in info['aliases'].items():
        n=int(key);master=int(value)
        if master not in targets:continue
        b,a,o=full(arc,n);t=targets[master].copy();t[o==0]=b[o==0]
        if not np.array_equal(np.where(o,o,t),a):raise ValueError('Alias acquired display differs')
        targets[n]=t;save_image(t.tobytes(),(384,384),pal,out/f'{n:03}.png')
    for n in(0,85):
        pilot=folder/f'pilot_{n:03}.png'
        if pilot.exists():targets[n]=np.array(Image.open(pilot))
    # Native breathing deformation, with fixed sole rows, follows the accepted
    # existing idle recipe rather than separately generated near-duplicates.
    if 0 in targets:
        for n in(92,115,116,117,118,119):
            dy=1 if 115<=n<=118 else -1 if n==119 else 0;master=targets[0];t=np.zeros_like(master)
            for y in range(384):
                shift=dy if y<170 else round(dy*max(0,178-y)/8);source=y-shift
                if 0<=source<384:t[y]=master[source]
            b,a,o=full(arc,n);t[o==0]=b[o==0];targets[n]=t
    if 85 in targets:
        b,a,o=full(arc,86);_,reference,_=full(arc,85);t=targets[85].copy();t[a!=reference]=a[a!=reference];t[o==0]=b[o==0];targets[86]=t
    # Riding heads have no jacket. Reuse the accepted Ultimate head exactly.
    for n in range(184,204):
        b,a,o=full(arc,n);t=base_palette_colors(project,n,pal);t[o==0]=b[o==0];targets[n]=t
    # Paired firing poses share the exact same torso/legs in the source. Preserve
    # that relation rather than keeping independently generated shading jitter.
    from src.psx_player import graphics_bank
    groups={};coherence=[]
    for f in graphics_bank(entry(arc,2),0,allow_bank_aliases=True)['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
    aliases_added=[]
    for refs in groups.values():
        selected=[n for n in refs if n in targets]
        if not selected:continue
        master=selected[0];_,original,_=full(arc,master)
        for n in set(refs)-set(selected):
            b,a,o=full(arc,n)
            if not np.any(o):continue
            t=targets[master].copy();t[a!=original]=a[a!=original];t[o==0]=b[o==0];targets[n]=t;aliases_added.append({'frame':n,'master':master})
    for refs in groups.values():
        if len(refs)<2 or set(refs)-set(targets):continue
        original=[full(arc,n)for n in refs];common=np.all(np.stack([q[1]for q in original])==original[0][1],axis=0);covered=np.all(np.stack([q[2]>0 for q in original]),axis=0)
        shared=targets[refs[0]].copy();shared[common&~covered]=original[0][1][common&~covered]
        for n,(b,a,o)in zip(refs,original):
            targets[n][common]=shared[common];targets[n][o==0]=b[o==0]
            if not np.array_equal(np.where(o,o,targets[n]),a):raise ValueError('Coherence adjustment changed acquired frame')
            save_image(targets[n].tobytes(),(384,384),pal,out/f'{n:03}.png')
        coherence.append({'frames':refs,'shared_source_pixels':int(common.sum())})
    for n,t in targets.items():
        b,a,o=full(arc,n)
        if not np.array_equal(np.where(o,o,t),a):raise ValueError('Derived acquired display differs')
        save_image(t.tobytes(),(384,384),pal,out/f'{n:03}.png')
    write(out/'normalization.json',{'source_sha256':sha(arc),'frames':sorted(targets),'reports':reports,'failures':failures,'shared_pose_coherence':coherence,'aliases_derived':aliases_added,'production_complete':False})
    print(json.dumps({'normalized':len(targets),'failures':failures}))
    return targets

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',choices=list(BASES));p.add_argument('--normalize',action='store_true');a=p.parse_args();normalize(a.project)if a.normalize else plan(a.project)
