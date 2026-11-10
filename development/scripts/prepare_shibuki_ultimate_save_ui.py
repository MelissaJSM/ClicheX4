"""얼티밋 저장 아이콘의 별도 팔레트31/30 및 전신52를 교체한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_ui import transfer_geometry,actual
from scripts.prepare_riko_illustrations import repack_one_bank
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from scripts.verify_shibuki_save_icon import rgba
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels
from src.psx_static_effect import compose_static
from src.psx_player import composition_frame
from src.epsxe_state import framebuffer,match_sprite

def render(menu,tex,mask):
    po=struct.unpack_from('<I',menu,4)[0];out=np.zeros((160,160),np.uint16)
    for n,row in [(44,31)]+([(52,30)] if mask else []):
        cp=aliased_composition(menu,2,n)
        for p in cp['parts']:
            pal=np.array(struct.unpack_from('<16H',menu,po+(row+p['clut'])*32),np.uint16)
            px,size,bb,_=compose_static(tex,local_composition({**cp,'parts':[p]}));a=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);region=out[bb[1]+80:bb[3]+80,bb[0]+80:bb[2]+80];region[a>0]=pal[a[a>0]]
    return out

def main(out):
    source=D/'save_ui_observed01';out=out.resolve()
    if not out.is_relative_to(D):raise ValueError('Expected isolated task output')
    out.mkdir(exist_ok=False)
    menu=(source/'MOJIPAT.ARC').read_bytes();load=(source/'LOAD_U.ARC').read_bytes();tex=entry(load,0x10008)
    if sha256(menu)!='9850cbb2214c5489e5f8cf5da9b69769e9ed35c99dada11b829ee4d0f751617b' or sha256(load)!='8917738345de7fd4ba7a3fc602f75456e1f14484a034d12ff0d39e1eeff43a04':raise ValueError('Unexpected parent menu resources')
    player=(D/'base_fix02/PL02_U.ARC').read_bytes()
    if sha256(player)!='2ea5ed73ec35549f571591008748c45dc31598d02128089a966073a5ff8650ef':raise ValueError('Unexpected approved sprite source')
    pal=entry(player,9);cp=composition_frame(entry(player,3),5,0)
    nm=transfer_geometry(menu,2,52,cp);frame=actual(player,0,5)
    old52={q['page']*256+q['tile'] for q in aliased_composition(menu,2,52)['parts']}
    # The load atlas also contains non-sprite menu graphics. Never allocate into
    # space merely because it is unreferenced by this one composition bank.
    reserved=set(range(len(tex)//128))-old52
    nt,nm,packing=repack_one_bank(tex,nm,2,{52:frame[:2]},{52:0},reserved_tiles=reserved)
    if any(tile_pixels(tex,t)!=tile_pixels(nt,t) for t in reserved):raise ValueError('Non-icon atlas pixels changed')
    packing['all_non_ultimate_icon_tiles_preserved']=len(reserved)
    nm=bytearray(nm);po=struct.unpack_from('<I',menu,4)[0]
    nm[po+30*32:po+31*32]=pal[32:64];nm[po+31*32:po+32*32]=pal[:32];nm=bytes(nm)
    expected_base=np.array(Image.open(D/'pilot01/base_000.png'));expected_armor=np.array(Image.open(D/'pilot01/overlay_000.png'));words=np.array(struct.unpack_from('<16H',pal),np.uint16);armorwords=np.array(struct.unpack_from('<16H',pal,32),np.uint16)
    for mask in range(16):
        got=render(nm,nt,mask);expected=words[expected_base]
        if mask:expected=np.where(expected_armor>0,armorwords[expected_armor],expected)
        if not np.array_equal(got,expected):raise ValueError(f'Save UI does not match approved native pose, mask {mask}')
    checks=0
    for n in range(aliased_composition(menu,2,0)['bank_frame_count']):
        if n==52:continue
        a,b=aliased_composition(menu,2,n),aliased_composition(nm,2,n)
        if a!=b or compose_static(tex,local_composition(a))[:3]!=compose_static(nt,local_composition(b))[:3]:raise ValueError('Other save icon changed')
        checks+=1
    allowed={i for p in aliased_composition(menu,2,52)['parts'] for i in range(p['record_offset'],p['record_offset']+4)}|set(range(po+30*32,po+32*32))
    if len(nm)!=len(menu) or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(menu,nm))):raise ValueError('Other menu bytes changed')
    for row in range(30):
        if menu[po+row*32:po+(row+1)*32]!=nm[po+row*32:po+(row+1)*32]:raise ValueError('Protected palette changed')
    nl=replace_entry(load,0x10008,nt);(out/'MOJIPAT.ARC').write_bytes(nm);(out/'LOAD_U.ARC').write_bytes(nl)
    vr=(source/'vram.bin').read_bytes();oldmatches=[];sheet=Image.new('RGB',(1000,430),'#253546');dr=ImageDraw.Draw(sheet)
    for i,(m,t,mask,title) in enumerate([(menu,tex,0,'Before capsule - old'),(nm,nt,0,'Before capsule - fixed'),(menu,tex,15,'Ultimate - old'),(nm,nt,15,'Ultimate - fixed')]):
        im=rgba(render(m,t,mask));crop=im.crop(im.getbbox());crop.save(out/f'icon_{i}.png');large=crop.resize((crop.width*5,crop.height*5),Image.Resampling.NEAREST);sheet.paste(large,(i*250+25,65),large);dr.text((i*250+10,10),title,fill='white')
        if i in (0,2):
            for page in (0,256):
                screen=framebuffer(vr,0,page);hits=match_sprite(screen,crop)
                if hits:oldmatches.append({'mask':mask,'page':page,'matches':hits});screen.save(out/f'observed_old_{mask}_{page}.png')
    sheet.save(out/'review.png')
    report={'kind':'ultimate_save_icon_fix','parent_bin_sha256':'af885c18568aceb787adb2eeb0e87c0b1722d37e89238891d6b7e7f92ba3fbe0','palette_rows':[30,31],'base_frame':44,'ultimate_frame':52,'us_base_clut':'0x784F','us_armor_clut':'0x784E','mask_combinations_checked':16,'other_save_frames_preserved':checks,'other_palette_rows_preserved':30,'old_screen_matches':oldmatches,'packing':packing,'files':{name:{'before':sha256((source/name).read_bytes()),'after':sha256((out/name).read_bytes()),'size':len((out/name).read_bytes())} for name in ('MOJIPAT.ARC','LOAD_U.ARC')},'runtime_new_verified':False,'exe_changed':False}
    if not oldmatches:raise ValueError('Observed failure not reproduced from parent resources')
    (out/'recipe.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=D/'save_ui_fix01');a=p.parse_args();main(a.output)
