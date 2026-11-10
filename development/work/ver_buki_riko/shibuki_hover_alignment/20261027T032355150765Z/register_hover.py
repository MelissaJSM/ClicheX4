"""생성한 두 다리를 원작 호버의 발 위치에 등록하고 기존 상체를 보존한다."""
import argparse,json,sys,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_armor import entries
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from scripts.project import digest
D=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('--output',default='layers01');a=p.parse_args();out=D/a.output;out.mkdir(exist_ok=False)
parent=ROOT/'out/ver_buki_riko/shibuki_fourth_remaining_20261027T014647676089Z'
es=entries((parent/'modified.arc').read_bytes());bank=graphics_bank(es[2],0,allow_bank_aliases=True)
source=Image.open(D/'hover_generated.png').convert('RGBA')
settings={221:{'crop':[455,515,775,740],'target_x':[73,98],'front_source_bottom':667,'front_target_bottom':102,'rear_target_bottom':106,'blend':[590,675],'cut':84},223:{'crop':[1120,537,1450,780],'target_x':[69,99],'front_source_bottom':685,'front_target_bottom':101,'rear_target_bottom':106,'blend':[1250,1360],'cut':87}}
def quantize(im,words):
    colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    pix=np.array(im);delta=pix[:,:,:3].astype(np.int32)[:,:,None,:]-colors[1:][None,None,:,:]
    idx=(np.argmin((delta*delta).sum(3),axis=2)+1).astype(np.uint8);idx[pix[:,:,3]<128]=0
    unseen=set(map(tuple,np.argwhere(idx>0)))
    while unseen:
        seed=unseen.pop();group={seed};todo=[seed]
        while todo:
            y,x=todo.pop()
            for dy in [-1,0,1]:
                for dx in [-1,0,1]:
                    q=(y+dy,x+dx)
                    if q in unseen:unseen.remove(q);group.add(q);todo.append(q)
        if len(group)<=2:
            for y,x in group:idx[y,x]=0
    return idx
sheet=Image.new('RGB',(960,640),'#253546');draw=ImageDraw.Draw(sheet)
for group,n in enumerate([221,223]):
    s=settings[n];crop=s['crop'];clipped=Image.new('RGBA',source.size);clipped.paste(source.crop(crop),(crop[0],crop[1]))
    scale=4;mesh=[];left,right=s['target_x'];top=s['cut'];bottom=110
    def srcpoint(x,y):
        sx=crop[0]+(x-left)*(crop[2]-crop[0])/(right-left)
        t=max(0,min(1,(sx-s['blend'][0])/(s['blend'][1]-s['blend'][0])))
        sybottom=s['front_source_bottom']*(1-t)+crop[3]*t;dybottom=s['front_target_bottom']*(1-t)+s['rear_target_bottom']*t
        return sx,crop[1]+(y-top)*(sybottom-crop[1])/(dybottom-top)
    for x in range(left,right):
        quad=(*srcpoint(x,top),*srcpoint(x,bottom),*srcpoint(x+1,bottom),*srcpoint(x+1,top))
        mesh.append(((x*scale,top*scale,(x+1)*scale,bottom*scale),quad))
    warped=clipped.transform((160*scale,160*scale),Image.Transform.MESH,mesh,Image.Resampling.BICUBIC).resize((160,160),Image.Resampling.BOX)
    indices={bi:quantize(warped,struct.unpack_from('<16H',es[9],0 if bi==0 else 32)) for bi in [0,8]}
    for k in [n,n+1]:
        f=bank['frames'][k];raw=decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data
        before=Image.new('RGBA',(160,160));after=Image.new('RGBA',(160,160))
        for bi in [0,8,5,7,6]:
            old=canvas_from_parts(raw,f['tile_count'],composition_frame(es[3],bi,k));v=old.copy();words=struct.unpack_from('<16H',es[9],0 if bi==0 else 32)
            if bi==0:v[s['cut']:]=0
            if bi==8:v[s['cut']:]=indices[bi][s['cut']:]
            im=save_image(v.tobytes(),(160,160),words,out/f'bank{bi}_{k:03}.png');after.alpha_composite(im.convert('RGBA'))
            oldim=save_image(old.tobytes(),(160,160),words,out/f'before_bank{bi}_{k:03}.png');before.alpha_composite(oldim.convert('RGBA'))
            assert np.array_equal(v[:s['cut']],old[:s['cut']])
        after.save(out/f'full_{k:03}.png')
        for j,im in enumerate([before,after]):
            pic=im.crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);x=(group*2+k-n)*240;y=j*320+32;sheet.paste(pic,(x,y),pic);draw.text((x+4,j*320+4),f'{k} '+('BEFORE' if j==0 else 'AFTER'),fill='white')
sheet.save(out/'review.png')
meta={'frames':[221,222,223,224],'canvas_size':[160,160],'origin':[80,80],'settings':settings,'source_image_sha256':digest(D/'hover_generated.png'),'source_prompt':'hover_edit_prompt.txt','image_mode':'built-in image_gen','upper_body_preserved_above_cut':True,'unchanged_layer_banks':[5,6,7],'lower_body_entirely_owned_by_leg_armor':True,'hover_requires_leg_armor_bit':8}
(out/'layers.json').write_text(json.dumps(meta,indent=2),encoding='utf-8');print(out)
