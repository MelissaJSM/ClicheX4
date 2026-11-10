"""체이서 누락 및 42..49 불완전 원본 참조를 실제 미국판 데이터로 조사한다."""
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_ui_inventory import load, entry, BUILDS
from scripts.overhaul_sprites_audit import render, rgba, sha
from src.psx_player import graphics_bank, composition_frame, decode_stream, indexed_atlas
OUT=ROOT/'work/overhaul_20261105/ui/riko_chaser'

def offset(address):return address-0x80010000+0x800

def main():
    OUT.mkdir(exist_ok=True)
    raw,_=load('ver_buki_riko');original,_=load('original');rin,_=load('ver_rin_nana')
    exe=raw['SLUS_005.61'];originalexe=original['SLUS_005.61']
    # Read the PS1 instructions, not the newer PC/Saturn replacement source.
    jal=0x0c000000|((0x8003b458>>2)&0x3ffffff)
    callers=[0x80010000+i-0x800 for i in range(0x800,len(exe)-3,4) if struct.unpack_from('<I',exe,i)[0]==jal]
    expected=[0x8003b5f8,0x8003bbd4,0x8003bd1c,0x8003c024,0x8003c174,0x8003c278,0x8003c3bc,0x8003c45c,0x8003c958,0x8003caec]
    assert callers==expected
    code={hex(a):exe[offset(a)-64:offset(a)+8].hex() for a in callers}
    for a in callers:assert exe[offset(a)-64:offset(a)+8]==originalexe[offset(a)-64:offset(a)+8]
    tables={hex(a):list(exe[offset(a):offset(a)+4]) for a in (0x800f910c,0x800f9110,0x800f9114)}
    assert tables=={'0x800f910c':[73,72,71,0],'0x800f9110':[76,75,74,0],'0x800f9114':[69,67,65,0]}
    animations={}
    for n in range(65,81):
        p=struct.unpack_from('<I',exe,offset(0x8011aff0)+4*n)[0];i=0;seen=set();steps=[]
        while i not in seen:
            seen.add(i);d,e,r,f=struct.unpack_from('<bbbB',exe,offset(p)+4*i);steps.append(dict(step=i,ticks=d,event=e,relative=r,frame=f));i+=r
        animations[str(n)]={'address':hex(p),'bank':exe[offset(0x8011af60)+n],'steps':steps}
    incomplete={};board=Image.new('RGB',(8*180,3*190),(28,34,45));draw=ImageDraw.Draw(board)
    for row,(project,assets) in enumerate([('original',original),('ver_buki_riko',raw),('ver_rin_nana',rin)]):
        arc=assets['PL01_U.ARC'];g=entry(arc,2);c=entry(arc,3);words=struct.unpack_from('<64H',entry(arc,9));meta=[]
        for col,n in enumerate(range(42,50)):
            f=graphics_bank(g,1)['frames'][n];co=composition_frame(c,5,n);dec=decode_stream(g,f['offset'],f['limit'],128*f['tile_count'])
            assert f['tile_count']==1
            atlas,_,_=indexed_atlas(dec.data,1);atlas=np.frombuffer(atlas,np.uint8).reshape(16,256)
            tile=rgba(atlas[:,:16],words).resize((128,128),Image.Resampling.NEAREST)
            board.paste(tile,(col*180+20,row*190+38),tile);draw.text((col*180+4,row*190+4),f'{project}\n{n}: 1/24 tiles',fill='white')
            meta.append({'frame':n,'tile_count':1,'referenced_tiles':[p['tile'] for p in co['parts']], 'decoded_sha256':sha(dec.data),'compressed_range':[f['offset'],dec.end],'unknown_tiles':sorted({p['tile'] for p in co['parts'] if p['tile']!=0})})
        incomplete[project]=meta
    board.save(OUT/'partial_uploads_42_49.png')
    # Same-size pose and design guides. Original character is only a pose guide.
    poses=Image.new('RGBA',(384,80));refs=Image.new('RGBA',(384,80));guidemeta={}
    opal=struct.unpack_from('<64H',entry(original['PL01_U.ARC'],9));rpal=struct.unpack_from('<64H',entry(raw['PL01_U.ARC'],9))
    for i,n in enumerate((14,22,30,38)):
        a,m=render(original['PL01_U.ARC'],1,5,n);poses.alpha_composite(rgba(a,opal).crop((112,120,208,200)),(i*96,0));guidemeta[str(n)]=m
    for i,n in enumerate((147,7,12,57)):
        a,m=render(raw['PL01_U.ARC'],0,0,n);refs.alpha_composite(rgba(a,rpal).crop((112,120,208,200)),(i*96,0))
    for name,im in [('poses',poses),('approved_riko',refs)]:
        im.save(OUT/(name+'_native.png'));im.resize((im.width*6,im.height*6),Image.Resampling.NEAREST).save(OUT/(name+'.png'))
    report={'baseline':BUILDS['ver_buki_riko'],'original':BUILDS['original'],'riko_original_body_identical':list(range(14,42)),
        'ride_animation_setter':hex(0x8003b458),'setter_callers':list(map(hex,callers)),'caller_machine_code':code,'dynamic_tables':tables,
        'reachable_chaser_animation_ids':list(range(65,77)),'unselected_chaser_animation_ids':list(range(77,81)),
        'animations':animations,'partial_streams':incomplete,'pose_guides':guidemeta,
        'findings':['All ten actual USA Ride Chaser animation-setter calls and all three dynamic selector tables select 65..76 only.',
        '77..80 point to 42..49 loops but no normal Ride Chaser transition selects them.',
        '42..49 contain one uploaded tile since original USA; composition needs tiles through23. No complete image is in these streams.',
        'The actual upload routine overwrites only one 16x16 tile. Other tiles would be previous VRAM contents, not a unique reconstructible frame.',
        'Do not invent prior VRAM history or claim complete rendering; preserve these eight original incomplete/unselected references. Runtime force-injection is not normal reachability evidence.'],
        'runtime_verified':False}
    (OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(OUT),'caller_count':len(callers),'body_reference_count':28,'unselected_incomplete':8}))

if __name__=='__main__':main()
