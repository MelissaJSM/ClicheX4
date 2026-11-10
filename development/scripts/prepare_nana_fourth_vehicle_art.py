"""수용 접점과 머리를 사용하여 체이서·라이드 아머 의상을 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import label,distance_transform_edt
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_vehicle_reference import PARENT,PARENT_SHA,FRAMES,ORDER,EDITED_FRAMES
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.prepare_nana_fourth_run_art import intervals,LAYERS
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.extract_zero import save_image
from src.psx_player import composition_frame
from src.psx_sprite_batch import canvas_from_parts
SOURCE=ROOT/'work/ver_rin_nana/nana_fourth_armor/vehicle_v1/generated.png'
SOURCE_SHA='57c655e653283f5ec5a069828517fe9ca3f6a523f636f5fe42fee38e59ca424d'
HIPS={162:82,166:82,170:79,174:77}
CONTACTS={162:[(59,78,66,83)],166:[(59,80,66,85)],170:[(62,73,68,79)],174:[(64,70,70,76)]}
HEADS={184:0,193:37,195:94,196:0,199:0}

def translate(v,dx,dy):
    a=np.zeros_like(v);x=max(0,dx);y=max(0,dy);x2=min(160,160+dx);y2=min(160,160+dy)
    a[y:y2,x:x2]=v[y-dy:y2-dy,x-dx:x2-dx];return a

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh vehicle art path required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(SOURCE)==SOURCE_SHA,'Source changed')
    arc=(PARENT/'modified.arc').read_bytes();c=entry(arc,3);words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    src=Image.open(SOURCE).convert('RGBA');require(src.getchannel('A').getextrema()==(0,255),'Transparent source required');out.mkdir(parents=True)
    yy,xx=np.indices((160,160));layers={};records=[]
    for i,n in enumerate(ORDER):
        base=render(arc,n)[1];by,bx=np.nonzero(base);bb=[int(bx.min()),int(by.min()),int(bx.max()+1),int(by.max()+1)]
        a=np.array(src.crop((i*src.width//4,0,(i+1)*src.width//4,src.height)));lab,_=label(a[:,:,3]>=192);sizes=np.bincount(lab.flat);sizes[0]=0;keep=lab==sizes.argmax();a[~keep,3]=0;sy,sx=np.nonzero(keep);box=[int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)]
        crop=Image.fromarray(a).crop(box);v=normalize(crop,bb[3]-bb[1],rgb,width=bb[2]-bb[0]);ey,ex=np.nonzero(base==14);vy,vx=np.nonzero((v==14)&(np.indices(v.shape)[0]<v.shape[0]//2))
        if not len(vx):
            col=np.array(crop).astype(np.int32);r,g,b=col[:,:,:3].transpose(2,0,1);eye=(g>r+10)&(g>b+10)&(g>60)&(col[:,:,3]>=192);eye[crop.height//2:]=False;gy,gx=np.nonzero(eye);vx=gx*v.shape[1]/crop.width;vy=gy*v.shape[0]/crop.height
        require(len(vx)>0,f'Generated eye absent: {n}');dx=round(float(ex.mean()-vx.mean()));dy=round(float(ey.mean()-vy.mean()));cx,cy=round(float(ex.mean())),round(float(ey.mean()))
        target=np.zeros_like(base);target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v;hip=HIPS[n];lower=hip+3
        for y in range(lower,bb[3]):
            target[y]=0
            for l,r in intervals(base[y]>0):
                target[y,l:r+1]=1
                if r>l+1:
                    target[y,l+1:r]=5 if y>=bb[3]-4 else 12
                    if r-l>=4 and y<bb[3]-4:target[y,r-1]=11
        target[:bb[1]]=0;target[bb[3]:]=0;target[(target==14)&(base!=14)]=2
        face=[cx-2,cy-2,cx+6,cy+6]
        for x,y,x2,y2 in [face]+CONTACTS[n]:target[y:y2,x:x2]=base[y:y2,x:x2]
        dist,idx=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0);require(float(dist[missing].max(initial=0))<=6,'Costume too far from native pose');target[missing]=target[tuple(idx[:,missing])]
        for x,y,x2,y2 in [face]+CONTACTS[n]:target[y:y2,x:x2]=base[y:y2,x:x2]
        delta=np.where(target!=base,target,0).astype(np.uint8);layers[n]={b:np.zeros_like(base) for b in LAYERS.values()}
        head=(xx>=cx-6)&(xx<cx+10)&(yy>=cy-9)&(yy<cy+7)
        leg=(yy>=hip)|((xx>=cx+10)&(yy>=max(cy+4,bb[3]-16)))
        arm=(xx>=cx-7)&(xx<cx+9)&(yy>=cy+5)&(yy<cy+21)&~head
        for b,mask in ((5,head),(8,leg),(7,arm)):layers[n][b][mask]=delta[mask];delta[mask]=0
        layers[n][6]=delta;records.append({'frame':n,'source_cell':i,'source_box':box,'placement':[dx,dy],'native_size':list(v.shape[::-1]),'face_box':face,'contacts':CONTACTS[n],'lower_y':lower,'boundary_pixels':int(missing.sum()),'max_boundary_distance':float(dist[missing].max(initial=0))})
    for n,source in HEADS.items():
        base=render(arc,n)[1];_,sb,sf,sraw=render(arc,source);full=sb.copy()
        for b in (8,5,7,6):v=canvas_from_parts(sraw,sf['tile_count'],composition_frame(c,b,source));full=np.where(v,v,full)
        ey,ex=np.nonzero(base==14);sy,sx=np.nonzero(sb==14);top_eye=sy==sy.min();sy,sx=sy[top_eye],sx[top_eye];cx,cy=round(float(ex.mean())),round(float(ey.mean()));scx,scy=round(float(sx.mean())),round(float(sy.mean()))
        left,top=cx-6,cy-10;target=base.copy();piece=full[scy-10:scy+6,scx-6:scx+10].copy();region=target[top:top+16,left:left+16];target[top:top+16,left:left+16]=np.where(piece,piece,region)
        layers[n]={b:np.zeros_like(base) for b in LAYERS.values()};layers[n][5]=np.where(target!=base,target,0).astype(np.uint8)
        records.append({'frame':n,'accepted_head_source':source,'accepted_crop':[scx-6,scy-10,scx+10,scy+6],'placement':[left,top],'eye':[cx,cy],'head_only':True})
    plan=json.loads((SOURCE.parent/'plan.json').read_text('utf8'))
    for q in plan['records']:
        n=q['frame']
        if n in layers:continue
        if n==198:layers[n]={b:np.zeros((160,160),np.uint8) for b in LAYERS.values()};records.append({'frame':n,'blank_preserved':True});continue
        first=q['aliases'][0];a=composition_frame(c,0,first)['parts'][0];b=composition_frame(c,0,n)['parts'][0];dx,dy=b['x']-a['x'],b['y']-a['y'];layers[n]={k:translate(v,dx,dy) for k,v in layers[first].items()};records.append({'frame':n,'shared_costume':first,'translation':[dx,dy]})
    board=Image.new('RGB',(4*256,3*280),'#242934');draw=ImageDraw.Draw(board)
    for n in FRAMES:
        target=render(arc,n)[1].copy()
        for b in (8,5,7,6):target=np.where(layers[n][b],layers[n][b],target)
        for name,b in LAYERS.items():save_image(layers[n][b].tobytes(),(160,160),words,out/f'{name}_{n:03}.png')
        save_image(target.tobytes(),(160,160),words,out/f'full_{n:03}.png')
    for i,n in enumerate([0,37,94]+ORDER+list(HEADS)):
        im=render(arc,n,True)[0] if n in (0,37,94) else Image.open(out/f'full_{n:03}.png').convert('RGBA')
        tile=im.crop((40,36,104,100)).resize((256,256),Image.Resampling.NEAREST);board.paste(tile,(i%4*256,i//4*280+24),tile);draw.text((i%4*256+4,i//4*280+4),str(n),fill='white')
    board.save(out/'family_4x.png');write(out/'layers.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frames':FRAMES,'edited_frames':EDITED_FRAMES,'blank_preserved':[198],'canvas_size':[160,160],'origin':[80,80],'palette_words':list(words),'source':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':SOURCE_SHA,'registration':records,'native_body_unchanged':True,'runtime_verified':False});print({'frames':len(EDITED_FRAMES),'blank_preserved':198,'output':str(out)})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
