"""공통 의상 원화를 기존 몸과 같은 좌표에 등록한다. 기본 몸은 변경하지 않는다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation,binary_closing,distance_transform_edt
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_armor import entries
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_armor_motion import fit
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
D=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',default='layers01');a=p.parse_args();OUT=D/a.output;OUT.mkdir(exist_ok=False)
plan=json.loads((D/'plan.json').read_text());groups=json.loads((D/'master_groups.json').read_text())
es=entries((ROOT/plan['parent']/'modified.arc').read_bytes());g,c,pal=es[2],es[3],es[9];bank=graphics_bank(g,0,allow_bank_aliases=True)
words=list(struct.unpack_from('<16H',pal,32));basewords=list(struct.unpack_from('<16H',pal));rgb=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words],np.int32)
yy,xx=np.indices((160,160));sources={};bases={};report=[]
head_source=np.array(Image.open(D.parent/'fourth_armor_v1/layers03/head_000.png'))
def raster(n):
    if n not in bases:
        f=bank['frames'][n];bases[n]=canvas_from_parts(decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data,f['tile_count'],composition_frame(c,0,n))
    return bases[n]
def bbox(mask):
    y,x=np.nonzero(mask);return int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)
def component(mask):
    lab,num=label(mask,np.ones((3,3)))
    if not num:return mask
    sizes=np.bincount(lab.ravel());sizes[0]=0;return lab==int(sizes.argmax())
def quantize(im,size):
    rgba=np.array(im);labels=np.zeros(rgba.shape[:2],np.uint8)
    for y in range(im.height):
        d=rgba[y,:,:3].astype(np.int32)[:,None,:]-rgb[1:][None,:,:];labels[y]=np.argmin((d*d).sum(2),axis=1)+1
    votes=[np.array(Image.fromarray(np.where(labels==k,rgba[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX)) for k in range(1,16)]
    v=(np.argmax(np.stack(votes),axis=0)+1).astype(np.uint8);alpha=np.array(im.getchannel('A').resize(size,Image.Resampling.BOX));v[alpha<128]=0;return v
for name,frames in groups.items():
    sheet=Image.open(D/f'{name}_generated.png').convert('RGBA')
    for i,n in enumerate(frames):
        cell=sheet.crop((round(i%4*sheet.width/4),round(i//4*sheet.height/4),round((i%4+1)*sheet.width/4),round((i//4+1)*sheet.height/4)))
        rgba=np.array(cell);mask=component(rgba[:,:,3]>=200);rgba[:,:,3]=np.where(mask,rgba[:,:,3],0);bb=bbox(mask);im=Image.fromarray(rgba).crop(bb)
        b=raster(n);box=bbox(b>0);v=quantize(im,(box[2]-box[0],box[3]-box[1]));canvas=np.zeros((160,160),np.uint8);canvas[box[1]:box[3],box[0]:box[2]]=v;sources[n]=canvas
        save_image(canvas.tobytes(),(160,160),words,OUT/f'master_{n:03}.png')
    
def choose(n,b):
    if n in sources:return n
    if 184<=n<=203:return None
    if 144<=n<=153: pool=[144,145,146,148,151,152,153]
    elif 67<=n<=84:pool=[67,71,77,83]
    elif n in (217,220):pool=[217]
    elif 33<=n<=66 or 221<=n<=230:pool=[33,35,37,39,41,43,45,49,55,57,59,65]
    elif 120<=n<=125:pool=[120]
    elif n in (138,139,95,96):pool=[138]
    elif 162<=n<=174 or n>=233:pool=[100,143,154,162,174]
    elif 204<=n<=207 or n in (231,232):pool=[204,207,101,138]
    else:pool=list(sources)
    def score(m):
        s=raster(m);common=(b>0)&(s>0)
        return np.count_nonzero((b>0)!=(s>0))*2+np.count_nonzero(common&(b!=s))
    return min(pool,key=score)

for item in plan['frames']:
    n=item['frame'];b=raster(n);layers={k:np.zeros_like(b) for k in ('head','body','arm','leg')};master=choose(n,b)
    # Original transparent armor references are preserved, including teleport effects.
    if not any(item['opaque'].values()):
        mode='original_transparent_armor'
    elif master is None:
        mode='small_head_accessory'
        # Ride-armor heads are separately reduced in the original game.
        small=np.array(Image.fromarray(head_source[60:76,80:96]).resize((7,7),Image.Resampling.NEAREST))
        by,bx=np.nonzero(b);left=int(bx.max())-6;top=int(by.min())+2
        layers['head'][top:top+7,left:left+7]=small
    else:
        mode='registered_generated_costume';generated=sources[master];sb=raster(master)
        # Registration is on the clothing texture; the accepted body geometry is never resized.
        paired=(34<=n<=84 and n%2==0) or (222<=n<=230 and n%2==0)
        anchor=raster(n-1) if paired else raster(217) if n==220 else b
        box=bbox(anchor>0);sbox=bbox(sb>0);reg=np.zeros_like(generated)
        native=Image.fromarray(generated).crop(sbox).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.NEAREST)
        reg[box[1]:box[3],box[0]:box[2]]=np.array(native)
        hair_seed=np.isin(anchor,[5,8,14])&(yy<box[1]+min(26,(box[3]-box[1])*0.65))
        hairhead=component(binary_closing(hair_seed,structure=np.ones((2,2))))
        hy,hx=np.nonzero(hairhead);cx=int(np.median(hx)) if len(hx) else (box[0]+box[2])//2
        head_top=int(hy.min()) if len(hy) else box[1]
        face_mask=np.isin(b,[12,13])&(xx>=cx-11)&(xx<=cx+8)&(yy>=head_top+9)&(yy<head_top+23)
        fc=component(face_mask);fy,fx=np.nonzero(fc)
        neck=int(fy.max())+1 if len(fy)>3 else head_top+20
        neck=max(head_top+15,min(head_top+22,neck));hip=neck+12
        back=n in (144,145,146,147,151,152,153,183)
        if not back:
            skinlabels,num=label(np.isin(anchor,[12,13])&(yy<box[1]+30),np.ones((3,3)))
            if num:
                sizes=np.bincount(skinlabels.ravel());sizes[0]=0;face=skinlabels==sizes.argmax();fy,fx=np.nonzero(face)
                if len(fx)>=8 and abs(int(fy.max())+1-neck)<=3:cx=int(np.median(fx))+3;neck=int(fy.max())+1;hip=neck+12
        hair=np.isin(b,[5,8,14])&(((yy<neck)&(xx>cx-11)&(xx<cx+12))|((xx>cx+7)&(yy<hip+3)))
        if back:hair|=np.isin(b,[5,8,14])&(xx>=cx-8)&(xx<=cx+8)&(yy<neck+5)
        hair|=binary_dilation(hair)&np.isin(b,[2,15])&((yy<neck)|(xx>cx+9))
        core=component(binary_closing(np.isin(anchor,[5,8,14]),structure=np.ones((2,2))))
        hair|=core&np.isin(b,[5,8,14])
        hair|=binary_dilation(core)&np.isin(b,[2,15])
        head_protect=(xx>=cx-11)&(xx<=cx+10)&(yy<neck)
        # Raised sleeves outside the head are retained as clothing. Face and hands stay skin.
        skin=np.isin(b,[12,13])&((yy<neck+5)|((xx<cx-7)|(xx>cx+9)))
        garment=(b>0)&~hair&~head_protect&~skin
        upper_sleeve=np.isin(b,[3,6,9])&((xx<cx-10)|(xx>cx+10))
        garment &= (yy>=neck)|binary_dilation(upper_sleeve,iterations=1)
        # A charged-shot arc and the powered-dash aura are effects, not cloth.
        if n==88:garment &= yy>=neck-9
        if n in (217,220):garment &= binary_dilation(raster(217)>0,iterations=0) if n==217 else binary_dilation(raster(217)>0,iterations=1)
        # Existing buster barrel and muzzle remain the accepted basic silhouette.
        if paired or n in (85,86,87,91,92,150,155):
            garment &= ~((xx<cx-8)&(yy<neck+2))
        # Preserve non-character sparks and aura outside the original master silhouette.
        if n in (107,108,111,136,141,142,157,220,235,236):
            garment &= binary_dilation(sb>0,iterations=2)
        coords=np.argwhere((reg>0)&~np.isin(reg,[4,5,6,9]))
        mapped=np.zeros_like(b)
        for y,x in np.argwhere(garment):
            dist=(coords[:,0]-y)**2*2+(coords[:,1]-x)**2;sy,sx=coords[int(np.argmin(dist))];mapped[y,x]=reg[sy,sx]
        # Shift the approved flower to the existing ornament, preserving face/ears.
        pink=np.isin(b,[4,10,11])&(yy<neck-2)&(yy>=head_top+4)&(xx>cx+3)
        py,px=np.nonzero(pink)
        if len(px):
            dx=int(px.min())-83;dy=int(py.min())-63
            for y,x in np.argwhere(head_source):
                if 0<=y+dy<160 and 0<=x+dx<160:layers['head'][y+dy,x+dx]=head_source[y,x]
        legs=garment&(yy>=hip)
        arms=garment&~legs&((xx<cx-5)|(xx>cx+7)|(yy<neck))
        if n in (217,220):
            legs=garment&(xx>=cx+23)
            arms=garment&~legs&(xx<cx+5)
        if item['counts']['7']==1:
            arms &= xx<cx-5
        body=garment&~legs&~arms
        layers['body']=np.where(body,mapped,0).astype(np.uint8)
        layers['arm']=np.where(arms,mapped,0).astype(np.uint8)
        layers['leg']=np.where(legs,mapped,0).astype(np.uint8)
        # If a sleeve includes the far shoulder, assign that shoulder to the
        # torso layer, keeping the final costume raster exactly unchanged.
        if fit(layers['arm']>0,item['counts']['7']) is None:
            arm=layers['arm'];remaining=arm.copy();keep=np.zeros_like(arm)
            for _ in range(item['counts']['7']):
                integral=np.pad((remaining>0).astype(np.int32),((1,0),(1,0))).cumsum(0).cumsum(1)
                sums=integral[16:,16:]-integral[:-16,16:]-integral[16:,:-16]+integral[:-16,:-16]
                y,x=np.unravel_index(sums.argmax(),sums.shape)
                keep[y:y+16,x:x+16]=remaining[y:y+16,x:x+16];remaining[y:y+16,x:x+16]=0
            layers['arm']=keep
            overflow=remaining>0;layers['body'][overflow]=remaining[overflow]
        report.append({'frame':n,'master':master,'neck':neck,'hip':hip,'cx':cx,'clothing_pixels':int(garment.sum()),'mode':mode})
    if mode!='registered_generated_costume':report.append({'frame':n,'master':master,'mode':mode})
    if (34<=n<=84 and n%2==0) or (222<=n<=230 and n%2==0):
        for kind in ('head','body','leg'):
            layers[kind]=np.array(Image.open(OUT/f'{kind}_{n-1:03}.png'))
    if n==220:
        for kind in layers: layers[kind]=np.array(Image.open(OUT/f'{kind}_217.png'))
    pic=save_image(b.tobytes(),(160,160),basewords,OUT/f'base_{n:03}.png').convert('RGBA')
    for k in ('leg','head','arm','body'):
        layer=save_image(layers[k].tobytes(),(160,160),words,OUT/f'{k}_{n:03}.png').convert('RGBA');pic.alpha_composite(layer)
    pic.save(OUT/f'full_{n:03}.png')
registration_reuse=[]
def reuse(dst,src,kinds=('head','body','arm','leg'),allow_flip=False):
    base=raster(src);target=raster(dst);best=None
    for flip in ((False,True) if allow_flip else (False,)):
        a=base[:,::-1] if flip else base
        for dy in range(-5,6):
            for dx in range(-10,11):
                shifted=np.roll(np.roll(a,dy,0),dx,1);common=(shifted>0)&(target>0)
                score=int(np.count_nonzero(common&(shifted==target))*3-np.count_nonzero((shifted>0)!=(target>0)))
                candidate=(score,-abs(dx)-abs(dy),not flip,dx,dy,flip)
                if best is None or candidate>best:best=candidate
    _,_,_,dx,dy,flip=best
    for kind in kinds:
        v=np.array(Image.open(OUT/f'{kind}_{src:03}.png'));v=v[:,::-1] if flip else v;v=np.roll(np.roll(v,dy,0),dx,1)
        save_image(v.tobytes(),(160,160),words,OUT/f'{kind}_{dst:03}.png')
    registration_reuse.append({'frame':dst,'source':src,'layers':list(kinds),'dx':dx,'dy':dy,'flip':flip,'base_matching_score':best[0]})
for dst,src in ((73,71),(74,72),(88,89),(107,106),(108,106),(111,110),(157,156)):
    reuse(dst,src)
for group in ((162,163,164,165),(166,167,168,169),(170,171,172,173)):
    for dst in group[1:]:reuse(dst,group[0])
reuse(145,144,allow_flip=True);reuse(147,146,allow_flip=True)
reuse(149,148)
reuse(150,148,kinds=('head','body','leg'))
for item in plan['frames']:
    n=item['frame'];pic=Image.open(OUT/f'base_{n:03}.png').convert('RGBA')
    for k in ('leg','head','arm','body'):pic.alpha_composite(Image.open(OUT/f'{k}_{n:03}.png').convert('RGBA'))
    pic.save(OUT/f'full_{n:03}.png')
for start in range(0,len(plan['frames']),48):
    sheet=Image.new('RGB',(1440,1104),'#253546');draw=ImageDraw.Draw(sheet)
    for i,item in enumerate(plan['frames'][start:start+48]):
        n=item['frame'];im=Image.open(OUT/f'full_{n:03}.png').crop((30,30,130,122)).resize((180,166),Image.Resampling.NEAREST);x=i%8*180;y=i//8*184;sheet.paste(im,(x,y+18),im);draw.text((x+8,y+2),str(n),fill='white')
    sheet.save(OUT/f'review_{start//48}.png')
(OUT/'layers.json').write_text(json.dumps({'frames':[v['frame'] for v in plan['frames']],'canvas_size':[160,160],'origin':[80,80],'palette_words':words,'registration':report,'shared_costume_registration':registration_reuse,'runtime_verified':False},indent=2))
print(json.dumps({'output':str(OUT),'frames':len(report)}))
