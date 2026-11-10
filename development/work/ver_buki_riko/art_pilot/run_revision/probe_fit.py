from pathlib import Path
import sys, json, struct
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_riko_jump import components
from scripts.repack_zero import read_inputs
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_frame_edit import frame_coverage
P=Path(__file__).parent
_,_,_,_,gfx,parts,_=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
bank=graphics_bank(gfx,0)
selected=json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text())
words=struct.unpack('<16H',(ROOT/selected['indexed_png']).with_name('candidate_palette.bin').read_bytes())
colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words[1:]],dtype=int)
def crops(name,n):
    im=Image.open(P/name).convert('RGBA');g=components(im,n)
    if n==8:g.sort(key=lambda q:(q[0][1]>im.height//2,q[0][0]))
    return g
groups=crops('paired8_clean.png',8)
groups[3]=crops('paired8_legorder.png',8)[3]
groups[1]=crops('paired8_down.png',8)[1]
groups[5]=crops('down_far.png',1)[0]
groups+=crops('start2.png',2)
slots=[[7],[8,9],[10],[11,12,13],[14],[15,16],[17],[18,19,20],[3],[4]]
result=[];board=Image.new('RGBA',(320*5,360*2),(42,45,54));draw=ImageDraw.Draw(board)
for i,((box,crop),ns) in enumerate(zip(groups,slots)):
    h=([47,46,47,48]*2+[47,47])[i];w=round(crop.width*h/crop.height*.85)
    rgba=np.array(crop.resize((w,h),Image.Resampling.NEAREST));visible=rgba[:,:,3]>=128
    idx=np.zeros((h,w),dtype=np.uint8);idx[visible]=np.argmin(((rgba[:,:,:3][visible].astype(int)[:,None]-colors[None])**2).sum(2),axis=1)+1
    ys,xs=np.nonzero((idx==5)&(rgba[:,:,0].astype(int)>rgba[:,:,1].astype(int)+20)&(rgba[:,:,2].astype(int)>rgba[:,:,0].astype(int)+10)&(np.indices(idx.shape)[0]<h*.45));eye=float(np.mean(xs))
    masks=[]
    for n in ns:
        f=bank['frames'][n];comp=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        cov,size,b=frame_coverage(raw,f['tile_count'],comp);safe=np.array([len(c)==1 for c in cov]).reshape(size[1],size[0])
        for part in comp['parts']:
            if part['tile']%16==0:safe[part['y']-b[1]:part['y']-b[1]+16,part['x']-b[0]]=False
        world=np.zeros((96,96),dtype=bool);world[48+b[1]:48+b[3],48+b[0]:48+b[2]]=safe;masks.append(world)
    common=np.logical_and.reduce(masks);yy=24-h
    fits=[x for x in range(-32,min(16,49-w)) if not np.any(visible&~common[48+yy:48+yy+h,48+x:48+x+w])]
    if i==5:print('BAD5',np.argwhere(visible & ~common[48+yy:48+yy+h,48-11:48-11+w]).tolist())
    print(i,ns,(w,h),'eye',eye,'x fits',fits,'eye range',[round(x+eye,1) for x in fits])
    if not fits:continue
    x=min(fits,key=lambda x:abs(x+eye+6))
    pic=np.zeros((h,w,4),dtype=np.uint8);pic[visible,:3]=colors[idx[visible]-1];pic[visible,3]=255
    tile=Image.new('RGBA',(64,72),(42,45,54));tile.alpha_composite(Image.fromarray(pic),(32+x,40+yy));tile=tile.resize((320,360),Image.Resampling.NEAREST)
    bx=i%5*320;by=i//5*360;board.alpha_composite(tile,(bx,by));draw.text((bx+4,by+4),str((i,ns,x,yy)),fill='white')
    result.append({'key':i,'frames':ns,'x':x,'y':yy,'eye_x':x+eye})
board.save(P/'fit_board.png');(P/'fit_probe.json').write_text(json.dumps(result,indent=2))





