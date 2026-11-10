"""Preserve each version's measured selection-copy origin while using v2 guards."""
import argparse,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import build_sprite_style_selection_v2 as previous
from scripts import build_sprite_consistency as builder

def check_selection_body(plan):
    from scripts.export_x_consistency import Archive
    from scripts.build_sprite_style_album import selection_image
    from scripts.c01_audio_build import read_disc
    builder.require(plan['project'] in ('ver_buki_riko','ver_rin_nana'),'Unknown selection origin mapping')
    source=ROOT/plan['source_bin']
    builder.require(builder.file_hash(source)==plan['source_sha256'],'Parent hash mismatch')
    assets=read_disc(source,('PL00_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0]
    for name in assets:
        if name in plan['resources']:
            row=plan['resources'][name];data=(ROOT/row['path']).read_bytes()
            builder.require(builder.sha(data)==row['after'],'Selection/body resource hash mismatch')
            assets[name]=data
    model=Archive(assets['PL00_U.ARC']);mapping=[(18,207),(19,156),(20,157),(21,158)]
    if plan.get('sync_shibuki_selection_beam',False):
        builder.require(plan['project']=='ver_buki_riko','Beam origin requires BR mapping');mapping.append((23,160))
    for ref,body in mapping:
        picture=np.array(model.composite(body,0)[0]);expected=np.zeros_like(picture)
        yy,xx=np.where(picture[:,:,3]>0)
        if ref in (18,23):tx,ty=xx,yy-1
        elif ref in (19,20):tx,ty=319-xx,yy+(1 if plan['project']=='ver_buki_riko' else 0)
        else:tx,ty=xx,yy
        builder.require(bool(np.all((tx>=0)&(tx<picture.shape[1])&(ty>=0)&(ty<picture.shape[0]))),'Selection transform outside canvas')
        expected[ty,tx]=picture[yy,xx]
        builder.require(np.array_equal(np.array(selection_image(assets,{'bank':2,'ref':ref})),expected),f'Selection {ref} differs from gameplay {body} at original {plan["project"]} origin')

def guarded_build(path):
    original=previous.check_selection_body
    try:
        previous.check_selection_body=check_selection_body
        return previous.guarded_build(path)
    finally:previous.check_selection_body=original

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('plan',type=Path);args=parser.parse_args();guarded_build(args.plan)
