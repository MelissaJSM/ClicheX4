"""정지 사격의 권총 모듈을 각 자세의 기존 총구 기준점에 그대로 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_nana_ultimate_shot_arm import D,full,pack_resources
from scripts.prepare_nana_fourth_pilot import entry,require,write
from scripts.extract_zero import save_image
from scripts.prepare_riko_ui import replace_entry
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.prepare_shibuki_capsule_nova import raster
from src.psx_player import graphics_bank,composition_frame,decode_stream,indexed_atlas
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_shot_arm_20261104T075213161189Z'
PARENT_SHA='26af8f917006ef22e5d3ef3290d2ca3cb5fd5170cfd6c1453bcae92578226ab4'
ARC_SHA='9a7ef0fb4357b4615d7d8020e0bae15082b2f33d5668026906ee56c325aed60c'
FRAMES=[*range(1,33),85,86]
SHOTS=[*range(2,33,2),85,86]

def artwork(arc):
    require(sha256(arc)==ARC_SHA,'Unsupported gun parent');prior=json.loads((PARENT/'ultimate_shot_arm/registration.json').read_text('utf8'));anchors={}
    targets={n:full(arc,n) for n in FRAMES}
    for n in SHOTS:
        q=next(q for q in prior if q['frames'][0]==n);x,y,_,_=q['pistol_mask_bbox'];region=targets[n][y-4:y+12,x:x+6];ys,xs=np.nonzero(np.isin(region,(5,6,7,8,9)));require(len(ys)>0,'Pistol barrel missing');tip=int(ys.min())+y-4;anchors[n]=(x,tip)
    x,y=anchors[85];module=targets[85][y-1:y+6,x:x+8].copy();require(module.shape==(7,8),'Wrong module');proof=[]
    for n in SHOTS:
        x,y=anchors[n];old=targets[n].copy();targets[n][y-1:y+6,x:x+8]=module
        proof.append({'frames':[n,n],'muzzle_anchor':[x,y],'pistol_mask_bbox':[x,y-1,x+8,y+6],'gun_module_box':[x,y-1,x+8,y+6],'module_sha256':sha256(module.tobytes()),'old_barrel_color_pixels':int(np.count_nonzero(np.isin(old[y,x:x+6],(5,6,7,8,9)))),'new_barrel_color_pixels':int(np.count_nonzero(np.isin(module[1,:6],(5,6,7,8,9)))),'changed_pixels':int(np.count_nonzero(old!=targets[n]))})
    return targets,proof,module

def correct_base(arc):
    targets,proof,module=artwork(arc)
    return patch_gun_base(arc,proof,module)

def patch_gun_base(arc,proof,module):
    g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);replacements={};baseproof=[]
    for q in proof:
        n=q['frames'][-1];x0,y0,x1,y1=q['gun_module_box'];f=bank['frames'][n];ns=[a['index'] for a in bank['frames'] if a['offset']==f['offset']];require(ns==([n] if n in (85,86) else [n-1,n]),'Unexpected gun sharing');raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;data=bytearray(raw);atlas,locations,_=indexed_atlas(raw,f['tile_count']);pixels=np.frombuffer(atlas,np.uint8).reshape(-1,256);parts=composition_frame(c,0,n)['parts'];protected={p['tile'] for v in ns for cb in (0,6,7,8) if v!=n or cb!=0 for p in composition_frame(c,cb,v)['parts']};old=raster(g,c,0,0,n);wanted=old.copy();wanted[y0:y1,x0:x1]=module
        def address(p,x,y):
            tx=x-80-p['x'];ty=y-80-p['y'];tx=15-tx if p['flip_x'] else tx;ty=15-ty if p['flip_y'] else ty;return (p['tile']//16*16+ty)*256+p['tile']%16*16+tx
        for y in range(y0,y1):
            for x in range(x0,x1):
                if old[y,x]==wanted[y,x]:continue
                hits=[p for p in parts if p['x']+80<=x<p['x']+96 and p['y']+80<=y<p['y']+96];require(bool(hits),'Gun module outside base coverage')
                editable=[p for p in hits if p['tile'] not in protected];require(bool(editable),'Gun needs a shared body tile');paint=editable[-1]
                for p in hits:
                    i=address(p,x,y);v=int(wanted[y,x]) if p is paint else 0;pos,shift=locations[i];before=(data[pos]>>shift)&15
                    if before==v:continue
                    require(p['tile'] not in protected,'Protected body pixel would change');data[pos]=(data[pos]&~(15<<shift))|(v<<shift)
        from src.psx_sprite_batch import canvas_from_parts
        from src.psx_ui_atlas import local_composition
        for v in ns:
            for cb in (0,6,7,8):
                expected=wanted if v==n and cb==0 else raster(g,c,0,cb,v)
                require(np.array_equal(canvas_from_parts(bytes(data),f['tile_count'],local_composition(composition_frame(c,cb,v))),expected),'Gun edit changes another base layer')
        for v in ns:replacements[v]=encode_stream(bytes(data))
        baseproof.append({'frame':n,'gun_module_box':q['gun_module_box'],'changed_base_pixels':int(np.count_nonzero(old!=wanted)),'all_other_base_pixels_preserved':True})
    ng,_=repack_graphics_bank(g,0,replacements);return replace_entry(arc,2,ng),baseproof

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D) and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent BIN changed');source=(PARENT/'PL02_U.ARC').read_bytes();targets,proof,module=artwork(source);words=struct.unpack_from('<16H',entry(source,9),32);out.mkdir();write(out/'registration.json',proof);save_image(module.tobytes(),(8,7),words,out/'pistol_module.png')
    for n,a in targets.items():save_image(a.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png')
    board=Image.new('RGB',(1152,576),'#252c3c');draw=ImageDraw.Draw(board)
    for i,n in enumerate((85,2,14)):
        q=next(q for q in proof if q['frames'][0]==n);x,y=q['muzzle_anchor']
        for row in (0,1):
            v=full(source,n) if row==0 else targets[n];rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in words],np.uint8);rgba=np.concatenate((rgb[v],((v>0)*255).astype(np.uint8)[...,None]),axis=2);p=Image.fromarray(rgba,'RGBA').crop((x-2,y-2,x+16,y+10)).resize((288,192),Image.Resampling.NEAREST);board.paste(p,(i*384+16,row*288+36),p);draw.text((i*384+16,row*288+8),('BEFORE ' if row==0 else 'AFTER ')+str(n),fill='white')
    board.save(out/'gun_before_after_16x.png')
    if art_only:return
    base,baseproof=correct_base(source);result,packed=pack_resources(base,targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',{'task':'ultimate_armor_nana','kind':'ultimate_gun_size','parent_sha256':PARENT_SHA,'parent_arc_sha256':ARC_SHA,'canonical_source_frame':85,'module_sha256':sha256(module.tobytes()),'frames':FRAMES,'registration':proof,'base_correction':baseproof,**packed,'files':{'PL02_U.ARC':sha256(result)},'full_ultimate_complete':False});print(json.dumps({'output':str(out),'sha256':sha256(result),'verification':packed['verification']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
