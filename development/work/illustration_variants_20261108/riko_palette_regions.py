"""Native-index proposal separating coat, inner clothing and face highlights.

A global palette inversion made outline dithering white and darkened the eyes.
Keep silhouette/coordinates/mouth data; reserve index2 for inner fabric and15
for head highlights. This is a separate preview and does not write a game BIN.
"""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
from black_ui import H,ROOT,words
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import aliased_composition,local_composition,repack_frames
from src.psx_static_effect import compose_static
from src.psx_ui_render import render_static_rgba

D=H/'ver_buki_riko'; OUT=D/'regions_v2';OUT.mkdir(exist_ok=True)
normal,black=words('ver_buki_riko'); newnormal=list(normal)
newnormal[2]=normal[1];newnormal[13]=normal[2];newnormal[15]=normal[5]
black[13]=0x8000|21|22<<5|24<<10;black[15]=normal[5]
def mask(poly,size,bounds):
    im=Image.new('1',size);ImageDraw.Draw(im).polygon([(x-bounds[0],y-bounds[1])for x,y in poly],fill=1);return np.array(im,bool)
reports=[]
board=Image.new('RGB',(1500,880),'#27313f');draw=ImageDraw.Draw(board)
for kind,file,base,limit,bank,ref in [('hq','ST0D_0Z.ARC',63488,81920,2,0),('dialogue','ST00_00.ARC',217088,223232,13,1)]:
    raw=(D/'originals'/file).read_bytes();p=entry(raw,10);g=entry(raw,0x10102)[base:limit]
    offs=struct.unpack_from('<'+'I'*(struct.unpack_from('<I',p)[0]//4),p);start=offs[bank];end=min((i for i in offs if i>start),default=len(p));one=struct.pack('<I',4)+p[start:end]
    targets={}
    for n in range(aliased_composition(p,bank,0)['bank_frame_count']):
        c=aliased_composition(p,bank,n);px,size,bb,_=compose_static(g,local_composition(c));old=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);a=old.copy()
        a[np.isin(old,[2,15])]=1
        a[old==13]=7
        if kind=='hq':
            if n==13:
                head=mask([(-22,-50),(25,-50),(25,-24),(1,-20),(-18,-24)],size,bb)
                inner=mask([(-8,-23),(0,-22),(0,-17),(-7,-10),(-12,-13)],size,bb)
            else:
                head=mask([(-22,-50),(24,-50),(24,-24),(5,-19),(-12,-20),(-22,-24)],size,bb)
                inner=mask([(-3,-20),(6,-19),(10,-10),(4,-8),(-2,-12)],size,bb)
        else:
            # Portrait-local coordinates converted to the native world origin.
            head=mask([(x-56,y-48)for x,y in [(7,0),(112,0),(112,73),(87,80),(64,74),(50,64),(34,53),(9,40)]],size,bb)
            inner=mask([(x-56,y-48)for x,y in [(53,60),(64,68),(78,76),(94,96),(47,96),(43,78)]],size,bb)
        a[head&(old==5)]=15
        a[inner&(old==1)]=2
        a[inner&(old==2)]=13
        assert np.array_equal(a==0,old==0)
        targets[n]=(a.tobytes(),size)
        reports.append({'kind':kind,'frame':n,'changed_indices':int((a!=old).sum()),'opaque':int((old>0).sum()),'alpha_exact':True})
    ng,np_,packing=repack_frames(g,one,0,targets,guard_uv_zero=(kind=='hq'))
    (OUT/f'{kind}_texture.bin').write_bytes(ng);(OUT/f'{kind}_parts.bin').write_bytes(np_[4:])
    groupy=0 if kind=='hq' else 440
    for col,(name,pal,tex,prt) in enumerate([('before',normal,g,one),('normal',newnormal,ng,np_),('black',black,ng,np_)]):
        im,bb=render_static_rgba(tex,aliased_composition(prt,0,ref),{0:pal});im.save(OUT/f'{kind}_{name}.png')
        big=im.resize((im.width*4,im.height*4),0);board.paste(big,(col*500+50,groupy+35),big);draw.text((col*500+50,groupy+10),f'{kind} / {name}',fill='white')
    print(kind,packing)
(OUT/'review.png').write_bytes(b'') if False else None
board.save(OUT/'review.png');(OUT/'report.json').write_text(json.dumps({'normal_palette':newnormal,'black_palette':black,'frames':reports,'runtime_verified':False},indent=2)+'\n','utf8')
