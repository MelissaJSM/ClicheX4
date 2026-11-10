"""수용 상체를 재사용하고 호버 다리를 원작 추진 발 위치에 등록한다."""
import argparse,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import label,distance_transform_edt
from PIL import Image,ImageDraw,ImageOps
from scripts.prepare_nana_fourth_hover_reference import PARENT,PARENT_SHA,FRAMES,REUSE,CUTS
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.prepare_nana_fourth_run_art import intervals,LAYERS
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.extract_zero import save_image
from src.psx_player import composition_frame,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
SOURCE=ROOT/'work/ver_rin_nana/nana_fourth_armor/hover_reference_v1/generated.png'
SOURCE_SHA='3ba8d6dc236c336c4a9b2818f929a95516a9474a89e7b1aa55d78791375ca94b'
# 생성 다리만 추출한다. 앞/뒤 발의 세로 축척은 원작 결합 지점에 맞춘다.
LEGS={221:{'crop':[700,314,914,466],'box':[73,85,98,106],'front_bottom':390,'front_target':102,'mirror':False},
      223:{'crop':[700,314,914,466],'box':[72,86,99,106],'front_bottom':390,'front_target':101,'mirror':False},
      225:{'crop':[210,782,368,920],'box':[69,85,88,107],'mirror':True},
      227:{'crop':[726,790,870,920],'box':[66,87,85,106],'mirror':True},
      229:{'crop':[1225,780,1337,956],'box':[74,85,88,110],'mirror':False}}

def clean(src):
    a=np.array(src.convert('RGBA'));lab,_=label(a[:,:,3]>=192);sizes=np.bincount(lab.flat);sizes[0]=0;keep=lab==sizes.argmax();a[~keep,3]=0;return Image.fromarray(a)

def lower(src,n,rgb):
    q=LEGS[n];x,y,x2,y2=q['crop'];left,top,right,bottom=q['box'];im=src.crop((x,y,x2,y2));a=np.array(im);a[a[:,:,3]<192,3]=0
    if n in (221,223):a[:348-y,800-x:,3]=0
    im=Image.fromarray(a)
    if q['mirror']:im=ImageOps.mirror(im)
    if 'front_bottom' in q:
        mesh=[]
        for xx in range(right-left):
            frac=(xx+.5)/(right-left);t=max(0,min(1,(frac-.36)/.20));sb=q['front_bottom']-y+(y2-q['front_bottom'])*t;db=q['front_target']-top+(bottom-q['front_target'])*t
            sx0=xx*im.width/(right-left);sx1=(xx+1)*im.width/(right-left);sy=(bottom-top)*sb/db
            mesh.append(((xx*4,0,(xx+1)*4,(bottom-top)*4),(sx0,0,sx0,sy,sx1,sy,sx1,0)))
        im=im.transform(((right-left)*4,(bottom-top)*4),Image.Transform.MESH,mesh,Image.Resampling.BICUBIC)
    v=normalize(im,bottom-top,rgb,width=right-left);result=np.zeros((160,160),np.uint8);result[top:bottom,left:right]=v;return result

def clear_base_below(raw,count,c,aliases,cuts):
    """호버에서 다리 아머가 담당할 중복 하체만 기존 기본 타일에서 제거."""
    _,locations,_=indexed_atlas(raw,count);dst=bytearray(raw);changed=set();expected={}
    for n in aliases:
        cut=cuts[n];comp=composition_frame(c,0,n);v=canvas_from_parts(raw,count,comp);v[cut:]=0;expected[n]=v
        for p in comp['parts']:
            for sy in range(16):
                if p['y']+80+sy<cut:continue
                ty=15-sy if p['flip_y'] else sy
                for sx in range(16):
                    tx=15-sx if p['flip_x'] else sx;t=p['tile'];off,shift=locations[(t//16*16+ty)*256+t%16*16+tx]
                    dst[off]&=~(15<<shift)&255;changed.add(t)
    dst=bytes(dst)
    for n,v in expected.items():require(np.array_equal(canvas_from_parts(dst,count,composition_frame(c,0,n)),v),'Lower-body erasure affects upper shared pixel')
    return dst,changed,expected

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh art path required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(SOURCE)==SOURCE_SHA,'Source changed')
    arc=(PARENT/'modified.arc').read_bytes();c=entry(arc,3);words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    src=Image.open(SOURCE).convert('RGBA');lo,hi=src.getchannel('A').getextrema();require(lo==0 and hi>=250,'Transparent source required');out.mkdir(parents=True);layers={};bases={};records=[];yy,xx=np.indices((160,160))
    for n,source in REUSE.items():
        _,base,f,raw=render(arc,source);bases[n]=base.copy();layers[n]={b:canvas_from_parts(raw,f['tile_count'],composition_frame(c,b,source)) for b in LAYERS.values()}
        if n in CUTS:
            cut=CUTS[n];bases[n][cut:]=0
            for b in (5,6,7):require(not np.any(layers[n][b][cut:]),'Accepted upper layer below leg boundary')
            first=n if n%2 else n-1;v=lower(src,first,rgb);old=base.copy()
            for b in (8,5,7,6):old=np.where(layers[n][b],layers[n][b],old)
            # 생성 하체를 원래 허리 접점에 점진적으로 등록한다. 아래 발은 고정한다.
            anchors=np.flatnonzero((old[cut-1]>0)&(xx[cut-1]<90))
            require(len(anchors)>0,'No native thigh seam')
            topx=np.flatnonzero(v[cut]>0)
            if len(topx):
                shift=int(round((anchors.min()+anchors.max()-topx.min()-topx.max())/2))
                for y in range(cut,min(cut+7,160)):
                    dx=round(shift*(1-(y-cut)/7));row=v[y].copy();v[y]=0
                    if dx>=0:v[y,dx:]=row[:160-dx]
                    else:v[y,:dx]=row[-dx:]
            layers[n][8][cut:]=v[cut:]
        records.append({'frame':n,'reuse_source':source,'upper_preserved_before_y':CUTS.get(n,160),'leg_source':LEGS.get(n if n%2 else n-1),'base_lower_owned_by_leg_armor':n in CUTS})
    n=94;base=render(arc,n)[1];im=clean(src.crop((0,0,src.width//3,src.height//2)));box=im.getbbox();v=normalize(im.crop(box),34,rgb);ey,ex=np.nonzero(base==14);gy,gx=np.nonzero((v==14)&(np.indices(v.shape)[0]<v.shape[0]//2));require(len(gx)>0,'Dash eye absent');dx=round(float(ex.mean()-gx.mean()));dy=round(float(ey.mean()-gy.mean()));target=np.zeros_like(base);target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
    face=(74,64,83,73);contact=(70,67,81,76)
    for x,y,x2,y2 in (face,contact):target[y:y2,x:x2]=base[y:y2,x:x2]
    target[(target==14)&(base!=14)]=2
    # 대시 발 위치와 외곽은 이미 수용된 기본형 그대로 유지한다.
    for y in range(82,92):
        target[y]=0
        for l,r in intervals(base[y]>0):
            target[y,l:r+1]=1
            if r>l+1:target[y,l+1:r]=5 if y>=89 else 12
    target[:58]=0;target[92:]=0;dist,indices=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0);require(float(dist[missing].max(initial=0))<=5,'Dash registration too far');target[missing]=target[tuple(indices[:,missing])]
    for x,y,x2,y2 in (face,contact):target[y:y2,x:x2]=base[y:y2,x:x2]
    delta=np.where(target!=base,target,0).astype(np.uint8);layers[n]={b:np.zeros_like(base) for b in LAYERS.values()};head=(xx>=70)&(xx<86)&(yy>=58)&(yy<74);leg=(yy>=79)|((xx>=85)&(yy>=70));arm=((xx>=69)&(xx<85)&(yy>=70)&(yy<86))&~head
    for b,mask in ((5,head),(8,leg),(7,arm)):layers[n][b][mask]=delta[mask];delta[mask]=0
    layers[n][6]=delta;bases[n]=base;records.append({'frame':94,'source_cell':0,'source_box':box,'native_size':list(v.shape[::-1]),'placement':[dx,dy],'face_box':face,'contacts':[contact],'lower_y':82})
    board=Image.new('RGB',(4*256,4*280),'#242934');d=ImageDraw.Draw(board)
    for i,n in enumerate([0,37]+FRAMES):
        if n in (0,37):im=render(arc,n,True)[0]
        else:
            target=bases[n].copy()
            for b in (8,5,7,6):target=np.where(layers[n][b],layers[n][b],target)
            for name,b in LAYERS.items():save_image(layers[n][b].tobytes(),(160,160),words,out/f'{name}_{n:03}.png')
            save_image(bases[n].tobytes(),(160,160),words,out/f'base_{n:03}.png');im=save_image(target.tobytes(),(160,160),words,out/f'full_{n:03}.png').convert('RGBA')
        tile=im.crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);board.paste(tile,(i%4*256,i//4*280+24),tile);d.text((i%4*256+4,i//4*280+4),str(n),fill='white')
    board.save(out/'family_4x.png');write(out/'layers.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frames':FRAMES,'canvas_size':[160,160],'origin':[80,80],'palette_words':list(words),'source':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':SOURCE_SHA,'registration':records,'base_lower_cut':CUTS,'hover_requires_leg_armor':True,'runtime_verified':False});print({'frames':len(FRAMES),'output':str(out)})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
