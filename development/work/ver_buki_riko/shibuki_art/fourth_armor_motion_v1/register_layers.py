"""생성 의상을 수용된 이동/사격의 실루엣에 등록하고 파츠 마스터를 분리한다."""
import argparse
import json
from pathlib import Path
import struct
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.analyze_shibuki_armor import entries
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank, decode_stream, composition_frame
from src.psx_sprite_batch import canvas_from_parts

D = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output', default='layers01')
args = parser.parse_args()
OUT = D / args.output
OUT.mkdir(exist_ok=False)
parent = ROOT / 'out/ver_buki_riko/shibuki_fourth_idle_20261027T002313205126Z'
es = entries((parent/'modified.arc').read_bytes())
g,c,pal = es[2],es[3],es[9]
bank = graphics_bank(g,0,allow_bank_aliases=True)
basewords = list(struct.unpack_from('<16H',pal))
meta = json.loads((D/'normalized01/normalization.json').read_text())
words = meta['palette_words']
yy,xx = np.indices((160,160))
head_source = np.array(Image.open(D.parent/'fourth_armor_v1/layers03/head_000.png'))
sheet = Image.new('RGB',(4*400,4*340),'#253546')
draw=ImageDraw.Draw(sheet)
records=[]


def raster(n):
    f=bank['frames'][n]
    return canvas_from_parts(decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data,f['tile_count'],composition_frame(c,0,n))


def intervals(mask, gap=0):
    coords=np.flatnonzero(mask)
    if not len(coords):return []
    groups=np.split(coords,np.flatnonzero(np.diff(coords)>gap+1)+1)
    return [(int(q[0]),int(q[-1])) for q in groups]


for i, item in enumerate(meta['frames']):
    n=item['frame'];b=raster(n);s=raster(n+1)
    generated=np.array(Image.open(D/'normalized01'/f'costume_{n:03}.png'))
    by,bx=np.nonzero(b);gy,gx=np.nonzero(generated)
    top=int(by.min());neck=top+20;bottom=int(by.max());g_bottom=int(gy.max())
    # Preserve the accepted foot height. Register clothing below the fixed neck;
    # never resize the accepted face, full body, or original animation geometry.
    registered=np.zeros_like(generated)
    for y in range(neck,bottom+1):
        sy=round(neck+(y-neck)*(g_bottom-neck)/max(1,bottom-neck))
        registered[y]=generated[sy]
    red=np.isin(b,[1,4,10,11])&(yy>=neck)&(yy<=neck+13)
    ry,rx=np.nonzero(red)
    cx=int(round(np.median(rx))) if len(rx) else int(round((bx.min()+bx.max())/2))
    hip=neck+13
    hair=np.isin(b,[5,8,14])&(xx>=cx+3)&(yy>=neck)&((yy<hip-3)|((xx>=cx+14)&(yy<hip+3)))
    # A one-cell outline belongs to the same hair/tail only outside the torso.
    expanded=hair.copy()
    for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
        expanded|=np.roll(np.roll(hair,dy,0),dx,1)&np.isin(b,[2,15])&(xx>=cx+7)
    hair=expanded
    common=(b==s)&(b>0)
    diff=(b!=s)
    preserved_skin=np.isin(b,[12,13])&(yy<neck+7)
    garment=(b>0)&(yy>=neck)&~hair&~preserved_skin
    mapped=np.zeros_like(b);registration=[]
    for y,x in np.argwhere(garment):
        # Map edge coverage from actual generated garment pixels. Stocking/boot
        # rows exclude lavender tail colors to keep the leg material consistent.
        candidates=(registered>0)
        if y>=hip:
            candidates &= ~np.isin(registered,[4,5,6])
        coords=np.argwhere(candidates)
        dist=(coords[:,0]-y)**2*3+(coords[:,1]-x)**2
        k=int(np.argmin(dist));sy,sx=coords[k]
        mapped[y,x]=registered[sy,sx]
        registration.append([int(x),int(y),int(sx),int(sy)])
    # Fit each stocking/boot cross-section to the approved leg silhouette.
    # This preserves the actual stride and gaps between the legs, while mapping
    # contiguous generated cloth clusters instead of copying stray nearest dots.
    for y in range(hip,bottom+1):
        for left,right in intervals(garment[y],gap=0):
            candidates=[]
            for sy in range(max(hip,y-3),min(bottom,y+3)+1):
                garment_row=(registered[sy]>0)&~np.isin(registered[sy],[4,5,6])
                for lo,hi in intervals(garment_row,gap=2):
                    score=abs((lo+hi)-(left+right))*.5+abs(sy-y)*3+abs((hi-lo)-(right-left))*.2
                    candidates.append((score,sy,lo,hi))
            if not candidates:continue
            _,sy,lo,hi=min(candidates)
            for x in range(left,right+1):
                sx=round(lo+(x-left)*(hi-lo)/max(1,right-left))
                value=registered[sy,sx]
                if not value or value in (4,5,6):
                    valid=np.flatnonzero((registered[sy,lo:hi+1]>0)&~np.isin(registered[sy,lo:hi+1],[4,5,6]))+lo
                    sx=int(min(valid,key=lambda q:abs(q-sx)));value=registered[sy,sx]
                mapped[y,x]=value
                registration.append([int(x),int(y),int(sx),int(sy)])
    # The head accessory uses the accepted armor pilot, positioned by the base
    # sprite's existing pink accessory. Base face/ears are never overwritten.
    pink=np.isin(b,[4,10,11])&(yy<neck)&(yy>=top+4)&(xx>=int((bx.min()+min(bx.max(),cx+10))/2)+4)
    py,px=np.nonzero(pink)
    head=np.zeros_like(b)
    if len(px):
        dx=int(px.min())-83;dy=int(py.min())-63
        for y,x in np.argwhere(head_source):
            head[y+dy,x+dx]=head_source[y,x]
    leg=np.where(garment&(yy>=hip),mapped,0).astype(np.uint8)
    near_arm=(xx<cx-4)&(yy<hip)
    far_arm=garment&(xx>cx+7)&(yy<hip)
    if min(len(composition_frame(c,7,f)['parts']) for f in (n,n+1))<2:
        # The original pose has one visible arm part; its rear shoulder/cloth
        # is included in the torso layer, as in the game's own part allocation.
        far_arm[:]=False
    arm_run=np.where(garment&(near_arm|far_arm)&(yy<hip),mapped,0).astype(np.uint8)
    body=np.where(garment&~near_arm&~far_arm&(yy<hip),mapped,0).astype(np.uint8)
    # All shooting changes stay in the front arm layer; retain the approved
    # buster shape and muzzle. The garment texture is registered to the raised
    # sleeve only, below the unchanged hand/buster.
    arm_shot=np.where(far_arm,arm_run,0).astype(np.uint8)
    shot_garment=near_arm&(xx>=cx-20)&(s>0)&(yy>=neck)&(yy<hip)&~np.isin(s,[12,13])
    coord=np.argwhere(registered>0)
    for y,x in np.argwhere(shot_garment):
        dist=(coord[:,0]-y)**2*3+(coord[:,1]-x)**2;k=int(np.argmin(dist));sy,sx=coord[k]
        arm_shot[y,x]=registered[sy,sx]
    layers={'head':head,'body':body,'leg':leg}
    for frame,base,arm in ((n,b,arm_run),(n+1,s,arm_shot)):
        actual={**layers,'arm':arm}
        pic=save_image(base.tobytes(),(160,160),basewords,OUT/f'base_{frame:03}.png').convert('RGBA')
        for key in ('leg','head','arm','body'):
            layer=save_image(actual[key].tobytes(),(160,160),words,OUT/f'{key}_{frame:03}.png').convert('RGBA')
            pic.alpha_composite(layer)
        pic.save(OUT/f'full_{frame:03}.png')
        if frame==n:
            tile=pic.crop((45,45,110,112)).resize((260,268),Image.Resampling.NEAREST)
            sheet.paste(tile,(i%4*400+65,i//4*340+35),tile)
            draw.text((i%4*400+10,i//4*340+10),str(n),fill='white')
    records.append({'frame':n,'shot':n+1,'neck':neck,'hip':hip,'center_x':cx,'base_bottom':bottom,'generated_bottom':g_bottom,'registered_pixels':registration,
                    'layers':{k:int(np.count_nonzero(v)) for k,v in {**layers,'arm_run':arm_run,'arm_shot':arm_shot}.items()}})
sheet.save(OUT/'review.png')
(OUT/'layers.json').write_text(json.dumps({'frames':sorted([v for r in records for v in (r['frame'],r['shot'])]),'canvas_size':[160,160],'origin':[80,80],'palette_words':words,'source':'run_generated.png','registration':records,'runtime_verified':False},indent=2))
print(json.dumps({'output':str(OUT),'frames':32,'common_base_body_preserved':True}))
