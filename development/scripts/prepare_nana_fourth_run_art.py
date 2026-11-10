"""생성 포스 의상을 수용한 나나 이동16쌍에 정규화·등록한다. 게임 파일 미수정."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import label,binary_dilation
from PIL import Image,ImageDraw,ImageFont
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.prepare_nana_pilot import normalize
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import composition_frame

PARENT=ROOT/'out/ver_rin_nana/nana_fourth_idle_20261030T063824458758Z'
PARENT_SHA='3d71c9ae921df7b9496e185894def835b2abf564ebc0a779a489d708a92cdaca'
ART=ROOT/'work/ver_rin_nana/nana_fourth_armor/run_v1'
LAYERS={'head':5,'body':6,'arm':7,'leg':8}


def intervals(row):
    xs=np.flatnonzero(row)
    return [] if not len(xs) else [(int(v.min()),int(v.max())) for v in np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)]


def prepare(out,profile='run'):
    require(profile in ('run','air','wall','dash'),'Unsupported motion profile')
    parent,parent_sha,art=PARENT,PARENT_SHA,ART
    source_sha='38ad93dda064cca77943190d59821634c3f444bc77833fd023e3de3e03861310'
    cols,rows,frames=4,4,list(range(1,33))
    if profile=='air':
        from scripts.prepare_nana_fourth_air_reference import PARENT as ap,PARENT_SHA as ah,FRAMES as af
        parent,parent_sha,art,rows,frames=ap,ah,ROOT/'work/ver_rin_nana/nana_fourth_armor/air_v1',3,af
        source_sha='17b11d88dcfa3c00ea65a1a160e1ec1176e101827bc9464c5b786928b2b5f185'
    if profile=='wall':
        from scripts.prepare_nana_fourth_wall_reference import PARENT as wp,PARENT_SHA as wh,FRAMES as wf
        parent,parent_sha,art,cols,rows,frames=wp,wh,ROOT/'work/ver_rin_nana/nana_fourth_armor/wall_v1',3,2,wf
        source_sha='2b2e8f9f5aedfb002bc7db6566a1b705f7d204a08b30181c92f7498c618639dd'
    if profile=='dash':
        from scripts.prepare_nana_fourth_dash_reference import PARENT as dp,PARENT_SHA as dh,FRAMES as df
        parent,parent_sha,art,cols,rows,frames=dp,dh,ROOT/'work/ver_rin_nana/nana_fourth_armor/dash_v1',4,2,df
        source_sha='c434ab720523d134995effe59564898dee645d0fae99e87cdf6a369f7974396b'
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh armor work path required')
    require(digest(parent/'rin_nana.bin')==parent_sha,'Parent changed')
    require(digest(art/'generated.png')==source_sha,'Movement source changed')
    arc=(parent/'modified.arc').read_bytes();c=entry(arc,3);words=struct.unpack_from('<16H',entry(arc,9),32)
    rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    source=Image.open(art/'generated.png').convert('RGBA');plan=json.loads((art/'plan.json').read_text('utf8'));order=plan['frame_order']
    alpha_min,alpha_max=source.getchannel('A').getextrema()
    require(alpha_min==0 and alpha_max>=250,'Transparent source with opaque foreground required');out.mkdir(parents=True)
    yy,xx=np.indices((160,160));pictures={};records=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
    board=Image.new('RGB',(cols*256,(rows+1)*282),'#242934');draw=ImageDraw.Draw(board)
    for i,n in enumerate(order):
        base=render(arc,n)[1];shot=render(arc,n+1)[1]
        ey,ex=np.nonzero((base==14)&(yy<(100 if profile=='dash' else 80)));require(len(ex)>0,'Native eye missing');eye_x=int(round(float(np.median(ex))));eye_y=int(round(float(np.median(ey))))
        by,bx=np.nonzero(base);top,bottom=int(by.min()),int(by.max());hip=eye_y+17
        if profile=='dash':hip=eye_y+({69:14,71:8,75:8}.get(n,17))
        cell=source.crop((i%cols*source.width//cols,i//cols*source.height//rows,(i%cols+1)*source.width//cols,(i//cols+1)*source.height//rows))
        a=np.array(cell);labels,count=label(a[:,:,3]>=128);sizes=np.bincount(labels.flat);sizes[0]=0;main=int(sizes.argmax());keep=labels==main
        sy,sx=np.nonzero(keep);box=(int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1));a[~keep,3]=0;crop=Image.fromarray(a).crop(box)
        v=normalize(crop,bottom-top+1,rgb)
        vy,vx=np.nonzero((v==14)&(np.indices(v.shape)[0]<v.shape[0]//2))
        if not len(vx):
            colors=np.array(crop).astype(np.int32);r,g,b=colors[:,:,:3].transpose(2,0,1)
            green=(g>r+10)&(g>b+10)&(g>60)&(colors[:,:,3]>=128);green[crop.height//2:]=False
            cy,cx=np.nonzero(green);require(len(cx)>0,f'Generated eye missing {n}')
            vx=cx*v.shape[1]/crop.width;vy=cy*v.shape[0]/crop.height
        dx=eye_x-int(round(float(np.median(vx))));dy=eye_y-int(round(float(np.median(vy))))
        require(min(dx,dy)>=0 and dx+v.shape[1]<=160 and dy+v.shape[0]<=160,'Canvas overflow')
        target=np.zeros_like(base);target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        face=((yy>=eye_y-3)&(yy<eye_y+6)&(xx>=eye_x-2)&(xx<eye_x+7))|((yy<eye_y+6)&(xx<eye_x-1))
        target[face]=base[face]
        if profile in ('air','wall','dash'):
            # Tiny cream pixels on dark headwear were explicitly rejected.
            hat_specks=np.isin(target,(10,11,12,13,15))&(yy>=eye_y-12)&(yy<eye_y-3)&(xx>=eye_x+5)&(xx<eye_x+14)
            target[hat_specks]=2
        contact_box=None
        if profile=='wall':
            palm=np.isin(base,(11,12,13))&(xx>eye_x+8)&(yy<eye_y+4)
            components,count=label(palm,np.ones((3,3)));require(count>0,'Native wall palm missing')
            rightmost=max(range(1,count+1),key=lambda k:int(np.nonzero(components==k)[1].max()))
            py,px=np.nonzero(components==rightmost)
            contact_box=[int(px.min())-1,int(py.min())-1,int(px.max())+2,int(py.max())+2]
            x,y,x2,y2=contact_box;target[y:y2,x:x2]=base[y:y2,x:x2]
        # Keep a narrow pink braid in front of the short dark veil, matching
        # the accepted armor instead of leaving the base outfit's loose hair.
        for y in range(eye_y-2,hip+1):
            hair=np.flatnonzero(np.isin(target[y],(7,8,9))&(np.arange(160)>=eye_x+8))
            if len(hair)>3:
                for x in hair[:-2]:target[y,x]={7:2,8:3,9:4}[int(target[y,x])]
        # Native stride silhouette is authoritative. One clean contour and skin
        # interior replace stockings; toe accents come from native shoe marks.
        foot_seeds=np.isin(target,(5,6))&(yy>=hip+5)
        foot=binary_dilation(foot_seeds,iterations=2)&(base>0)
        if profile in ('air','wall','dash'):
            calves,count=label((base>0)&(yy>=hip+4))
            foot=np.zeros_like(base,dtype=bool)
            for component in range(1,count+1):
                cy,cx=np.nonzero(calves==component)
                if len(cx)>=3:
                    foot|=(calves==component)&(yy>=int(cy.max())-2)
        lower_y,lower_x=np.nonzero((base>0)&(yy>=hip+4))
        # The trailing toe can lie outside the generated crop after native
        # stride registration. Keep its last three columns in the shoe color.
        foot|=(base>0)&(yy>=hip+4)&(xx>=int(lower_x.max())-2)
        for y in range(hip+4,bottom+1):
            target[y]=0
            for left,right in intervals(base[y]>0):
                target[y,left:right+1]=1
                if right-left>=2:
                    target[y,left+1:right]=12
                    if right-left>=4:target[y,right-1]=11
                    for x in range(left+1,right):
                        if foot[y,x]:target[y,x]=5
                elif right>left:target[y,left]=5 if foot[y,left] or foot[y,right] else 12
        # Keep the foot contact row and recolor only its opaque interior.
        target[bottom]=np.where(base[bottom]>0,1,0)
        if profile in ('wall','dash'):
            # Registration can shift the generated shoe below the native toe.
            # Keep wall contact height exact, including the transparent rows.
            target[bottom+1:]=0
        sy,sx=np.nonzero(target);missing=np.argwhere((base>0)&(target==0));distances=[]
        for y,x in missing:
            dist=(sy-y)**2+(sx-x)**2;k=int(dist.argmin());require(dist[k]<=25,f'Pose {n} exceeds local registration at {x},{y}')
            target[y,x]=target[sy[k],sx[k]];distances.append(int(dist[k]))
        target[face]=base[face]
        if profile in ('wall','dash'):
            # Alpha registration can leave a detached generated edge texel.
            # Remove only tiny islands that do not contain any native pixel.
            islands,count=label(target>0,np.ones((3,3)))
            for component in range(1,count+1):
                mask=islands==component
                if np.count_nonzero(mask)<=2 and not np.any(base[mask]):target[mask]=0
        diff=base!=shot;gy,gx=np.nonzero(diff);require(len(gx)>0,'Shot pair has no gun change')
        gun=(xx>=gx.min())&(xx<=gx.max())&(yy>=gy.min())&(yy<=gy.max())
        shot_target=target.copy();shot_target[gun]=shot[gun];shot_target[face]=shot[face]
        # The base shooting arm leaves a transparent notch below the cheek.
        # Its former hair/torso overlap does not join the new dress shoulder.
        # Bridge only transparent shoulder pixels; hand, gun and opaque face
        # pixels retain their native coordinates and values.
        shoulder_pixels=[]
        for y in range(eye_y+2,eye_y+9):
            left=np.flatnonzero(shot_target[y,eye_x-10:eye_x-2])+eye_x-10
            right=np.flatnonzero(shot_target[y,eye_x:eye_x+6])+eye_x
            if not len(left) or not len(right):continue
            start,end=int(left.max()+1),int(right.min())
            if end-start>7:continue
            for x in range(start,end):
                if shot_target[y,x]==0:
                    shot_target[y,x]=1 if y==eye_y+2 else 2
                    shoulder_pixels.append([x,y])
        pistol=(xx>=gx.min())&(xx<eye_x-8)&(yy>=gy.min())&(yy<=gy.max())
        # Any base pixels added by shooting outside the rectangular source
        # region would indicate a mismatched pair rather than a costume patch.
        require(not np.any((shot>0)&(shot_target==0)),'Shooting base escapes target')
        wall_pistol=None
        if profile in ('wall','dash'):
            from scripts.prepare_nana_fourth_wall_gun import refit
            minimum_shift=1 if profile=='dash' else 3
            shot_target,wall_pistol=refit(shot_target,eye_x,rgb,minimum_shift)
            shot,_=refit(shot,eye_x,rgb,minimum_shift)
            save_image(shot.tobytes(),(160,160),words,out/f'base_{n+1:03}.png')
        hat_pixels=(target>0)&(xx>=eye_x-1)&(xx<eye_x+9)
        hat_top=int(np.nonzero(hat_pixels if profile!='run' else target)[0].min())
        rear_split={13:12,27:17,31:12,59:17,67:0,69:-6,77:-6,79:0}.get(n,4)
        sleeve_split={13:4,15:3,27:4,29:3,47:4,51:4,59:8,65:2,67:2,69:2,77:2,79:2}.get(n,-2)
        layer_masks={5:(yy>=hat_top)&(yy<hat_top+16)&(xx>=eye_x-1)&(xx<eye_x+15),
                     8:(yy>=hip)|((xx>=eye_x+14)&(yy>=eye_y+rear_split)),
                     7:(xx<eye_x+sleeve_split)&(yy>=eye_y-2)&(yy<hip)}
        # In one-slot arm poses retain the rear sleeve in the torso layer.
        if profile!='wall' and min(len(composition_frame(c,7,f)['parts']) for f in (n,n+1))>=2:
            layer_masks[7]|=(xx>=eye_x+11)&(yy>=eye_y+10)&(yy<hip)
        if profile=='air' and n in (39,41):
            layer_masks[7]|=(xx>=eye_x+9)&(yy<eye_y+5)
            if n==41:layer_masks[7]&=(xx>=eye_x-2)
        if profile=='wall':
            layer_masks[7]|=(xx>=eye_x+9)&(yy<eye_y+(2 if n==65 else 5))
        for f,b,t in ((n,base,target),(n+1,shot,shot_target)):
            layers={k:np.zeros_like(b) for k in LAYERS.values()};remaining=np.where(t!=b,t,0).astype(np.uint8)
            for k in (5,8,7):layers[k][layer_masks[k]]=remaining[layer_masks[k]];remaining[layer_masks[k]]=0
            layers[6]=remaining
            if f==n+1:
                # This joint belongs to the sleeve, not the hat/torso; keep
                # it in the same original arm part as the shooting upper arm.
                for x,y in shoulder_pixels:
                    for k in layers:layers[k][y,x]=shot_target[y,x] if k==7 else 0
            merged=b.copy()
            for k in (8,5,7,6):merged=np.where(layers[k],layers[k],merged)
            require(np.array_equal(merged,t),'Layer split mismatch')
            for name,k in LAYERS.items():save_image(layers[k].tobytes(),(160,160),words,out/f'{name}_{f:03}.png')
            pictures[f]=save_image(t.tobytes(),(160,160),words,out/f'full_{f:03}.png').convert('RGBA')
        if profile not in ('wall','dash'):require(np.array_equal(shot_target[pistol],shot[pistol]),'Pistol changed')
        tile=pictures[n].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);board.paste(tile,(i%cols*256,i//cols*282+24),tile);draw.text((i%cols*256+4,i//cols*282+3),f'{profile} {n:03} / 사격 {n+1:03}',font=font,fill='white')
        records.append({'frame':n,'shot':n+1,'source_cell':i,'crop':box,'size':list(v.shape[::-1]),'placement':[dx,dy],'eye':[eye_x,eye_y],'hip':hip,'wall_pistol_adjustment':wall_pistol,
            'boundary_pixels':len(missing),'max_boundary_distance_squared':max(distances,default=0),'gun_box':[int(gx.min()),int(gy.min()),int(gx.max()+1),int(gy.max()+1)],'pistol_box':[int(gx.min()),int(gy.min()),eye_x-8,int(gy.max()+1)],'shoulder_bridge_pixels':shoulder_pixels,'native_lower_silhouette_preserved_from_y':hip+4,'pistol_pixels_preserved':True,'rear_layer_split':rear_split,'sleeve_layer_split':sleeve_split,'wall_contact_box':contact_box})
        if wall_pistol:records[-1]['pistol_pixels_preserved']=False
    if profile=='dash':
        for f,original in ((73,71),(74,72)):
            base=render(arc,f)[1]
            if f==74:
                from src.psx_sprite_batch import canvas_from_parts
                _,_,descriptor,raw=render(arc,f)
                ordinary=composition_frame(c,0,72);comp=composition_frame(c,0,74)
                tiles={p['tile'] for p in ordinary['parts']}
                effects={**comp,'parts':[p for p in comp['parts'] if p['tile'] not in tiles]}
                effect=canvas_from_parts(raw,descriptor['tile_count'],effects)
                base=np.where(effect,effect,np.array(Image.open(out/'base_072.png')))
                save_image(base.tobytes(),(160,160),words,out/f'base_{f:03}.png')
            merged=base.copy()
            for k in (8,5,7,6):
                name=next(name for name,v in LAYERS.items() if v==k)
                layer=np.array(Image.open(out/f'{name}_{original:03}.png'))
                save_image(layer.tobytes(),(160,160),words,out/f'{name}_{f:03}.png')
                merged=np.where(layer,layer,merged)
            pictures[f]=save_image(merged.tobytes(),(160,160),words,out/f'full_{f:03}.png').convert('RGBA')
    for i,n in enumerate((0,85)):
        im=render(arc,n,True)[0].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);board.paste(im,(i*256,rows*282+24),im);draw.text((i*256+4,rows*282+3),f'수용 기준 {n:03}',font=font,fill='white')
    board.save(out/'family_4x.png');images=[]
    steps=plan['native_run_animation']['steps'] if profile=='run' else [{'frame':n,'duration_ticks':6} for n in order]
    for step in steps:
        im=pictures[step['frame']].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);bg=Image.new('RGB',im.size,'#242934');bg.paste(im,(0,0),im);images.append(bg)
    images[0].save(out/(profile+'_preview.gif'),save_all=True,append_images=images[1:],duration=[round(s['duration_ticks']*1000/60) for s in steps],loop=0,disposal=2)
    write(out/'layers.json',{'task':'fourth_armor_nana','parent':parent.relative_to(ROOT).as_posix(),'parent_sha256':parent_sha,'frames':frames,'canvas_size':[160,160],'origin':[80,80],'palette_words':list(words),'source':(art/'generated.png').relative_to(ROOT).as_posix(),'source_sha256':digest(art/'generated.png'),'registration':records,'runtime_verified':False,'preview_timing':'native run' if profile=='run' else 'contact-sheet slideshow; not gameplay timing'})
    print(json.dumps({'output':out.relative_to(ROOT).as_posix(),'frames':len(frames),'native_pistol_pairs':len(order)}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--profile',choices=('run','air','wall','dash'),default='run');a=p.parse_args();prepare(a.output,a.profile)
