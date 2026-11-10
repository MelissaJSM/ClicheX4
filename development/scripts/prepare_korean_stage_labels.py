"""Translate the stage thumbnail captions while retaining their photographs."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_korean_ui import label
from scripts.prepare_riko_illustrations import repack_one_bank
from scripts.inventory_korean_ui import grey
from scripts.inventory_shibuki_ui import sheet
from scripts.discover_inputs import sha256
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static

NAMES=['정글','스노 베이스','바이오 랩','볼케이노','마린 베이스','사이버 공간','에어 포스','군용 열차','우주항','최종 병기']

def main(output):
    output.mkdir(exist_ok=False);files={};checks={};items=[]
    for name in ('ST0D_0X.ARC','ST0D_0Z.ARC'):
        raw=(D/'ui_inventory'/name).read_bytes();g=entry(raw,0x10102);p=entry(raw,10);offsets=struct.unpack('<'+'I'*(len(entry(raw,12))//4),entry(raw,12));start=offsets[1];end=min(v for v in offsets if v>start);bank=g[start:end];targets={}
        for n,text in enumerate(NAMES):
            c=local_composition(aliased_composition(p,1,n));px,size,_,_=compose_static(bank,c);a=np.frombuffer(px,np.uint8).reshape(size[1],size[0]).copy()
            a[-16:]=label(text,(size[0],16),12,15,border=1);targets[n]=(a.tobytes(),size);items.append((f'{name} {n}',grey(a.tobytes(),size)))
        ng,np_,proof=repack_one_bank(bank,p,1,targets)
        for n in range(10):
            c=local_composition(aliased_composition(np_,1,n));new,size,_,_=compose_static(ng,c);old=compose_static(bank,local_composition(aliased_composition(p,1,n)))[0]
            if new[:size[0]*(size[1]-16)]!=old[:size[0]*(size[1]-16)]:raise ValueError('Stage photograph changed above caption')
        new=replace_entry(replace_entry(raw,0x10102,g[:start]+ng+g[end:]),10,np_)
        (output/name).write_bytes(new);files[name]={'before':sha256(raw),'after':sha256(new),'size':len(new)};checks[name]=proof
    sheet(items,output/'preview.png',5,(180,130));(output/'proposal.json').write_text(json.dumps({'kind':'korean_stage_label_proposal','bin_applied':False,'files':files,'checks':checks},indent=2));print(json.dumps({'files':list(files),'labels':20}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
