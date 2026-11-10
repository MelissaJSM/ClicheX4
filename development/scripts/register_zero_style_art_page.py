"""새 원화를 고정 해상도와 원팔레트로 등록하고 원래 발 위치에서 비교한다."""
import argparse
from pathlib import Path
import json
import struct
import sys

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.overhaul_sprites_audit import render, rgba
from scripts.prepare_riko_ui import entry
from scripts.prepare_rin_run import quantize
from scripts.export_x_consistency import page
from scripts.prepare_sprite_style_unification import WORK,write
from src.psx_disc import file_hash


def main():
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
    d=a.directory.resolve();assert d.is_relative_to(WORK)
    info=json.loads((d/'inputs.json').read_text('utf8'));source=ROOT/info['source_bin']
    assert file_hash(source)==info['source_sha256']
    arc=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC']
    pal=list(struct.unpack_from('<16H',entry(arc,9)));black=list(struct.unpack_from('<16H',entry(arc,9),13*32))
    colors=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in pal[1:]],np.int32)
    im=Image.open(d/'generated.png').convert('RGBA');cw,ch=im.width/info['columns'],im.height/info['rows']
    nw,nh=info['native_cell'];assert abs(cw/ch-nw/nh)<.001
    scale=nw/cw;out=d/'native';assert not out.exists();out.mkdir();records=[];items={v:[] for v in ('normal','black')}
    idle=render(arc,0,0,147)[0]
    for f in info['frames']:
        x,y=f['cell'];crop=im.crop((round(x*cw),round(y*ch),round((x+1)*cw),round((y+1)*ch)))
        v=quantize(crop,colors,scale);assert v.shape==(nh,nw)
        target=np.zeros((384,384),np.uint8);x0,y0,x1,y1=info['crop'];target[y0:y1,x0:x1]=v
        old=render(arc,f['bank'],f['bank']*5,f['ref'])[0]
        bb=rgba(target,pal).getbbox();oldbb=rgba(old,pal).getbbox();assert bb
        dy=oldbb[3]-bb[3];assert abs(dy)<=6,(f['key'],dy)
        if dy:target=np.roll(target,dy,axis=0)
        Image.fromarray(target).save(out/(f['key']+'_indices.png'))
        for name,words in [('normal',pal),('black',black)]:
            pic=rgba(target,words);pic.save(out/(name+'_'+f['key']+'.png'))
            items[name].extend([(f['key']+' before',rgba(old,words)),(f['key']+' detailed',pic)])
        records.append({**f,'translate':[0,dy],'after_bounds':rgba(target,pal).getbbox(),
                        'new_art_pixels':int((target>0).sum()),'old_head_or_body_overwritten':False})
    for name,words in [('normal',pal),('black',black)]:
        page(items[name],rgba(idle,words),out/(name+'_comparison.png'),cols=2,scale=4)
    write(out/'registration.json',{'source_art_sha256':file_hash(d/'generated.png'),'scale':scale,
          'palette_unchanged':True,'records':records,'applied':False})
    print(json.dumps({'out':str(out),'frames':len(records),'scale':scale}))


if __name__=='__main__':main()
