"""Register explicit C04 corrections without silently weakening other-frame guards."""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.overhaul_sprites_audit import D,entry,write,sha,rgba,board
from scripts.overhaul_sprites_costume import full
from scripts.extract_zero import save_image
from scripts.prepare_rin_run import quantize
from scipy.ndimage import label,binary_dilation
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_sprite_batch import canvas_from_parts

def shift(image,dx=0,dy=0):
    out=np.zeros_like(image);h,w=image.shape
    out[max(0,dy):min(h,h+dy),max(0,dx):min(w,w+dx)]=image[max(0,-dy):min(h,h-dy),max(0,-dx):min(w,w-dx)]
    return out

def part_layer(arc,n,indices):
    g,c=entry(arc,2),entry(arc,3);f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    cp=composition_frame(c,0,n);parts=[p for p in cp['parts']if p['index']in indices]
    small=canvas_from_parts(raw,f['tile_count'],{'parts':parts});out=np.zeros((384,384),np.uint8);out[80:240,80:240]=small;return out

def complete_effects(project):
    nana=project=='ver_rin_nana';folder=D/('nana_preultimate'if nana else'shibuki_preultimate');arc=(D/project/'baseline/PL02_U.ARC').read_bytes();pal=struct.unpack_from('<64H',entry(arc,9));out=folder/'state_overrides';out.mkdir(exist_ok=True)
    meta=json.loads((out/'state.json').read_text('utf8'))if(out/'state.json').exists()else{'base_frames':[],'post_frames':[],'shared_frames':[]}
    def get(n):return np.array(Image.open(folder/f'normalized/{n:03}.png'))
    base={};post={};shared=set();registration=[];colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:16]],np.int32)
    source=Image.open(folder/'arrival_generated.png').convert('RGBA')
    for i,n in enumerate([133,135,136,137]):
        crop=source.crop((i%2*source.width//2,i//2*source.height//2,(i%2+1)*source.width//2,(i//2+1)*source.height//2));a=np.array(crop);labs,_=label(a[:,:,3]>=224,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;mask=labs==sizes.argmax();a[~mask,3]=0;sy,sx=np.nonzero(mask);crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));a=np.array(crop).astype(np.int32);yy,xx=np.indices(a.shape[:2]);r,g,b=a[:,:,:3].transpose(2,0,1)
        eye=(g>r+8)&(g>b+8)if nana else(r>b+50)&(g>b+25)&(r>g)&(b<140)
        eye&=(a[:,:,3]>=224)&(yy<crop.height*.65)&(xx<crop.width*.6);ey,ex=np.nonzero(eye)
        if not len(ex):raise ValueError(f'Generated eye missing {n}')
        tx=-4 if nana else -5;ty=({133:-2,135:-13,136:-12,137:-15}if nana else{133:1,135:-8,136:-9,137:-8})[n];sole=22
        choices=[]
        for h in range(28,65):
            scale=h/crop.height;cy=round((float(np.median(ey))+.5)*scale-.5);choices.append((abs(h-1-cy-(sole-ty)),abs(h-(51 if nana else 47)),h,cy))
        _,_,h,cy=min(choices);scale=h/crop.height;v=quantize(crop,colors,scale);vx=round((float(np.median(ex))+.5)*scale-.5);vh,vw=v.shape;dx=160+tx-vx;dy=160+ty-cy;target=np.zeros((384,384),np.uint8);target[dy:dy+vh,dx:dx+vw]=v
        # Deterministic source registration keeps original eye and sole anchors.
        by,bx=np.nonzero(target);target=shift(target,0,182-int(by.max()));ey_world=ty+182-int(by.max())
        if n in(136,137):
            cp=composition_frame(entry(arc,3),0,n);indices=[p['index']for p in cp['parts']if p['tile']==7];fx=part_layer(arc,n,indices);target[fx>0]=fx[fx>0]
        base[n]=target;shared.add(n);registration.append({'frame':n,'eye_world':[tx,ey_world],'sole_world':22,'generated_height':h,'uniform_scale':scale})
    fx=full(arc,129)[0];base[134]=np.where(base[133],base[133],fx).astype(np.uint8);shared.add(134)
    fx=part_layer(arc,131,range(16));body=part_layer(arc,131,range(16,24));vals,cnt=np.unique(body[body>0],return_counts=True);light=int(vals[cnt.argmax()]);base[131]=np.where(base[133]>0,light,fx).astype(np.uint8);shared.add(131)
    base[132]=full(arc,132)[0].copy()
    cp=composition_frame(entry(arc,3),0,140);fx=part_layer(arc,140,[p['index']for p in cp['parts']if p['tile']==8]);old=full(arc,140)[0];vals,cnt=np.unique(old[(old>0)&(fx==0)],return_counts=True);light=int(vals[cnt.argmax()]);base[140]=np.where(get(0)>0,light,fx).astype(np.uint8);shared.add(140)
    # Reuse the completed return body under the already-approved aura geometry.
    b,a,o=full(arc,157);body=shift(get(156),dy=-1);mask=body>0;halo=binary_dilation(mask,np.ones((3,3)),iterations=2);inner=binary_dilation(mask,np.ones((3,3)));v=np.where(inner,7,np.where(halo,13,0)).astype(np.uint8)if nana else np.where(inner,9,np.where(halo,14,0)).astype(np.uint8);v[mask]=body[mask];v[o==0]=b[o==0];base[157]=v
    fx=full(arc,159)[0]
    for armor in(False,True):
        body=shift(full(arc,156)[1]if armor else get(156),dy=-10)
        if nana:
            energy_map=np.array([0,5,6,7,8,5,6,7,8,9,8,9,13,13,9,9],np.uint8);body=energy_map[body%16]
        v=np.where(body,body,fx).astype(np.uint8)
        if armor:post[158]=v
        else:base[158]=v
    base[158][post[158]==0]=0
    # Shared hurt flashes follow each state's body; original external rays stay.
    for armor in(False,True):
        normal=full(arc,106)[1]if armor else get(106);launch=full(arc,110)[1]if armor else get(110)
        native109=full(arc,109)[0];vals,cnt=np.unique(native109[native109>0],return_counts=True);order=np.argsort(-cnt);inside=int(vals[order[0]]);border=int(vals[order[1]])if len(vals)>1 else inside
        mask=normal>0;v=np.where(binary_dilation(mask),border,0).astype(np.uint8);v[mask]=inside
        (post if armor else base)[109]=v
        old=full(arc,110)[0]>0;new=launch>0
        for n in(112,113,114):
            native=full(arc,n)[0]%16;v=native.copy();v[binary_dilation(old,iterations=2)]=0
            if n==114:v[np.isin(v,[3,5])]=0
            if n==112:v[binary_dilation(new)]=6;v[new]=14
            elif n==113:v[binary_dilation(new)]=1
            else:
                v[binary_dilation(new)]=1;v[new]=3;v[np.isin(launch%16,[1,2,4,8,15])&new]=5;v[np.isin(launch%16,[6,9])&new]=1
            v=np.where(v,v+32,0).astype(np.uint8);(post if armor else base)[n]=v
        # Flat departure silhouettes use the same accepted body proportions.
        for n in(208,209):
            native=full(arc,n)[0];vals,cnt=np.unique(native[native>0],return_counts=True);color=int(vals[cnt.argmax()]);shape=full(arc,0)[1]if armor else get(0);(post if armor else base)[n]=np.where(shape>0,color,0).astype(np.uint8)
        native=full(arc,210)[0];sy,sx=np.nonzero(native);vals,cnt=np.unique(native[native>0],return_counts=True);color=int(vals[cnt.argmax()]);shape=full(arc,0)[1]if armor else get(0);y,x=np.nonzero(shape);w=int(sx.max()-sx.min()+1);h=int(y.max()-y.min()+1)
        small=np.array(Image.fromarray((shape[y.min():y.max()+1,x.min():x.max()+1]>0).astype(np.uint8)).resize((w,h),Image.Resampling.NEAREST));v=np.zeros_like(shape);left=int(sx.min());top=int(sy.max())+1-h;v[top:top+h,left:left+w]=np.where(small,color,0);(post if armor else base)[210]=v
    for n in post:
        # Opaque effect layers draw over the base. Preserve its external pixels
        # only where the approved armor layer also covers them.
        base[n][post[n]==0]=0
    # Armor body layers use their fixed armor CLUT; the electric flash uses
    # CLUT2. It therefore stays a shared effect layer, not a new armor layer.
    for n in(112,113,114):
        base[n]=post.pop(n);shared.add(n)
    if not nana:
        for n in(148,149,150):
            candidate=get(n);head=part_layer(arc,n,range(3));missing=(head>0)&(candidate==0);b,a,o=full(arc,n)
            if np.any(missing&(o==0)):raise ValueError('Ladder head fill outside armor')
            candidate[missing]=head[missing]
            if not np.array_equal(np.where(o,o,candidate),a):raise ValueError('Ladder acquired altered')
            base[n]=candidate
    for n,v in base.items():save_image(v.tobytes(),(384,384),pal,out/f'base_{n:03}.png')
    for n,v in post.items():save_image(v.tobytes(),(384,384),pal,out/f'post_{n:03}.png')
    meta.update(baseline_sha256=sha(arc),base_frames=sorted(set(meta['base_frames'])|set(base)),post_frames=sorted((set(meta['post_frames'])|set(post))-{112,113,114}),shared_frames=sorted(set(meta['shared_frames'])|shared),arrival_registration=registration,arrival_source_sha256=sha((folder/'arrival_generated.png').read_bytes()))
    write(out/'state.json',meta);board([(str(n)+' PRE',rgba(v,pal))for n,v in sorted(base.items())],out/'remaining_pre_review.png',cols=6);board([(str(n)+' POST',rgba(v,pal))for n,v in sorted(post.items())],out/'remaining_post_review.png',cols=4)
    print(json.dumps({'project':project,'base':meta['base_frames'],'post':meta['post_frames'],'shared':meta['shared_frames']}))

def shibuki():
    project='ver_buki_riko';folder=D/'shibuki_preultimate';arc=(D/project/'baseline/PL02_U.ARC').read_bytes()
    pal=struct.unpack_from('<64H',entry(arc,9));out=folder/'state_overrides';out.mkdir(exist_ok=True)
    previous=json.loads((out/'state.json').read_text('utf8'))if(out/'state.json').exists()else{'base_frames':[],'post_frames':[],'shared_frames':[]}
    native=np.array(Image.open(folder/'normalized/000.png'));yy,xx=np.indices(native.shape)
    colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal],np.int32)
    mapping=np.argmin(((colors[16:32,None]-colors[None,1:16])**2).sum(axis=2),axis=1)+1;mapping[0]=0
    items=[]
    for n in(1,2):
        post=np.array(Image.open(ROOT/f'work/overhaul_20261105/ui/c04_shibuki_ultimate/frame{n}_indexed.png'))
        base=native.copy()if n==1 else np.array(Image.open(folder/'normalized/002.png'))
        if n==2:
            head=(yy<156)&(xx>=145)&(xx<=177);base[head]=mapping[post[head]]
        base[post==0]=0
        save_image(base.tobytes(),(384,384),pal,out/f'base_{n:03}.png');save_image(post.tobytes(),(384,384),pal[16:32],out/f'post_{n:03}.png')
        items.extend([(f'{n} PRE',rgba(base,pal)),(f'{n} POST',rgba(post,pal[16:32]))])
    previous.update(baseline_sha256=sha(arc),base_frames=sorted(set(previous['base_frames'])|{1,2}),post_frames=sorted(set(previous['post_frames'])|{1,2}),source='UI C04 candidate.json; pre outfit clips to corrected post alpha, eyes/feet preserved')
    write(out/'state.json',previous);board(items,out/'c04_pre_post_review.png',cols=4)
    print(json.dumps(previous))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--effects',choices=['ver_rin_nana','ver_buki_riko']);args=p.parse_args()
    complete_effects(args.effects)if args.effects else shibuki()
