"""Compare current native vehicle/rider composition with captured framebuffers."""
from pathlib import Path
import argparse,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from src.epsxe_state import framebuffer,match_sprite
p=argparse.ArgumentParser();p.add_argument('--name',default='rn43_fourth_chaser01');args=p.parse_args();assert args.name.isidentifier()
P=O/args.name;e=json.loads((P/'evidence.json').read_text());character=e.get('character','nana');is_zero=character in ('rin','riko');ram=(P/'ram.bin').read_bytes();src=json.loads((W/('staging_br_v31.json'if character in ('shibuki','riko')else 'staging_rn_v43.json')).read_text())['resources']['PL01_U.ARC' if is_zero else 'PL00_U.ARC'];arc=(ROOT/src['path']).read_bytes();assert hashlib.sha256(arc).hexdigest()==src['after']
display=struct.unpack_from('<4h',ram,0x166c10);assert display[0]==0 and display[1] in (0,240) and display[2:]==(320,240),'Unexpected display environment'
if is_zero:
    from scripts.build_sprite_style_album import zero_palettes,zero_image
    palettes=zero_palettes(arc)
else:a=Archive(arc)
def body(ram,video,cp,n):
    v=np.frombuffer(video,dtype='<u2').reshape(512,1024);h=struct.unpack_from('<I',ram,cp+n*4)[0];parts=[struct.unpack_from('<BBbb',ram,cp+(h>>16)*4+i*4)for i in range(h&65535)];out=np.zeros((128,128,4),np.uint8)
    for fl,t,x,y in parts:
        clut=(0x784a if is_zero else 0x7848)+((fl>>2)&3);words=v[clut>>6,(clut&63)*16:(clut&63)*16+16];pal=np.array([[((int(w)>>z)&31)*255//31 for z in(0,5,10)]+[255 if i else 0]for i,w in enumerate(words)],np.uint8)
        tile=v[t//16*16:t//16*16+16,384+t%16*4:388+t%16*4];ix=np.stack([(tile>>z)&15 for z in(0,4,8,12)],axis=2).reshape(16,16);q=pal[ix]
        if fl&64:q=q[:,::-1]
        if fl&128:q=q[::-1]
        dst=out[64+y:80+y,64+x:80+x];mask=q[:,:,3]>0;dst[mask]=q[mask]
    return Image.fromarray(out)
rows=[];board=Image.new('RGB',(1280,len(e['samples'])*260),'#26313f');d=ImageDraw.Draw(board)
for i,s in enumerate(e['samples']):
    video=(P/f'vram{i:02}.bin').read_bytes();pl=bytes.fromhex(s['player_hex']);bike=bytes.fromhex(s['bike_hex']);cp=struct.unpack_from('<I',bike,0x3c)[0]&0x1fffff;pr=pl[0x47];br=bike[0x47]
    assert pl[8:16]==bike[8:16]
    native=(zero_image(arc,character,{'id':f'normal:b1_{pr:03}','form':'normal','bank':1,'ref':pr},palettes) if is_zero else a.composite(pr,15)[0]).crop((96,96,224,224));vehicle=body(ram,video,cp,br)
    combos={'rider_over_bike':Image.alpha_composite(vehicle,native),'bike_over_rider':Image.alpha_composite(native,vehicle)};matches={}
    for order,im in combos.items():
        bb=im.getbbox();matches[order]=[{'page':py,'hits':match_sprite(framebuffer(video,0,py),im.crop(bb))}for py in(0,240)]
    y=i*260
    for j,py in enumerate((0,240)):
        pic=framebuffer(video,0,py).resize((480,360),Image.Resampling.NEAREST).crop((0,110,480,350));board.paste(pic,(j*480,y+20))
    q=combos['rider_over_bike'].resize((256,256),Image.Resampling.NEAREST);board.paste(q,(1000,y),q);d.text((4,y+3),f'{i}: rider {pr}, bike {br}; two GPU buffers, native composition at right',fill='white')
    rows.append({'sample':i,'rider_ref':pr,'bike_ref':br,'common_world_origin':True,'matches':matches})
board.save(P/'screen_context_display.png')
for i in range((board.height+1039)//1040):board.crop((0,i*1040,1280,min(board.height,(i+1)*1040))).save(P/f'screen_display_{i}.png')
report={'rows':rows,'display_environment':display,'framebuffer_pages':[0,240],'source_arc_sha256':src['after'],'matched_samples':sum(any(q['hits']for q in r['matches']['rider_over_bike'])for r in rows),'reverse_order_matched_samples':sum(any(q['hits']for q in r['matches']['bike_over_rider'])for r in rows),'memory_written':False,'actually_viewed':False}
(P/'screen_match_display.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps({'matched':report['matched_samples'],'reverse':report['reverse_order_matched_samples'],'samples':len(rows)}))
