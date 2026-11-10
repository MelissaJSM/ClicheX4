"""Validate save icons with the US runtime bit mapping and per-part CLUTs."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.prepare_shibuki_ui import actual
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image

def icon(menu,texture,mask,arm_type):
    po=struct.unpack_from('<I',menu,4)[0];out=np.zeros((160,160),np.uint16)
    for bit,n in [(0,44),(1,45),(2,46),(4,47),(8,48)]:
        if bit and not mask&bit:continue
        cp=aliased_composition(menu,2,n);base=10 if bit==4 and arm_type==2 else 8
        for p in cp['parts']:
            row=base+p['clut'];pal=np.array(struct.unpack_from('<16H',menu,po+row*32),np.uint16)
            px,size,bb,_=compose_static(texture,local_composition({**cp,'parts':[p]}));a=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);region=out[bb[1]+80:bb[3]+80,bb[0]+80:bb[2]+80];region[a>0]=pal[a[a>0]]
    return out

def rgba(words):
    a=np.stack([(words&31)*255//31,((words>>5)&31)*255//31,((words>>10)&31)*255//31,np.where(words!=0,255,0)],axis=2).astype(np.uint8)
    return Image.fromarray(a)

def verify(build):
    recipe=json.loads((build/'recipe.json').read_text('utf8'));folder=ROOT/recipe['save_ui_candidate'];old=ROOT/'work/ver_buki_riko/shibuki_ui_v1/candidate17'
    menu=(build/'MOJIPAT.ARC').read_bytes();texture=entry((build/'LOAD_U.ARC').read_bytes(),0x10008);player=(build/'modified.arc').read_bytes();pal=entry(player,9)
    exe=(ROOT/'work/ver_buki_riko/shibuki_ui_v1/US_EXE.bin').read_bytes();off=lambda addr:addr-0x80010000+2048
    if exe[off(0x800F1FBC):off(0x800F1FBC)+4]!=bytes([1,2,4,8]) or exe[off(0x8001BF00):off(0x8001BF00)+4]!=bytes.fromhex('0a780224'):raise ValueError('US save renderer differs')
    po=struct.unpack_from('<I',menu,4)[0]
    for row,p in [(8,pal[:32]),(9,pal[32:64]),(11,pal[64:96])]:
        if menu[po+row*32:po+(row+1)*32]!=p:raise ValueError('Wrong live palette binding')
    # Every other native UI composition and palette row remains exact.
    before=(old/'MOJIPAT.ARC').read_bytes();beforetex=entry((old/'LOAD_U.ARC').read_bytes(),0x10008);checked=0
    for b in [2]:
        for n in range(aliased_composition(menu,b,0)['bank_frame_count']):
            if n in [44,45,46,47,48]:continue
            a=aliased_composition(before,b,n);z=aliased_composition(menu,b,n)
            if a!=z or compose_static(beforetex,local_composition(a))[:3]!=compose_static(texture,local_composition(z))[:3]:raise ValueError('Other save UI frame changed')
            checked+=1
    palette_end=struct.unpack_from('<I',menu,8)[0]
    if any(x!=y and not po+11*32<=i<po+12*32 for i,(x,y) in enumerate(zip(before[po:palette_end],menu[po:palette_end]),start=po)):raise ValueError('Unrelated menu palette changed')
    checks=[];out=build/'save_icon_review';out.mkdir(exist_ok=True)
    for arm in [1,2]:
        for mask in range(16):
            expected=np.zeros((160,160),np.uint16)
            for bit,b in [(0,0),(1,5),(2,6),(4,7),(8,8)]:
                if bit and not mask&bit:continue
                px,size,bb=actual(player,0,b);a=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);colors=np.array(struct.unpack_from('<16H',pal,0 if not bit else 64 if bit==4 and arm==2 else 32),np.uint16);region=expected[bb[1]+80:bb[3]+80,bb[0]+80:bb[2]+80];region[a>0]=colors[a[a>0]]
            got=icon(menu,texture,mask,arm)
            for flip in [False,True]:
                if not np.array_equal(got[:,::-1] if flip else got,expected[:,::-1] if flip else expected):raise ValueError('Equipment mask or arm color mismatch')
                checks.append([mask,arm,flip])
            im=rgba(got);im.crop(im.getbbox()).save(out/f'mask{mask:02}_arm{arm}.png')
    report={'build_sha256':json.loads((build/'manifest.json').read_text())['modified_bin']['sha256'],'us_mapping_bytes':'01020408','arm_type2_base_clut':'0x780A','part_clut_offset':1,'combinations_checked':len(checks),'other_save_ui_frames_preserved':checked,'riko_palette_row10_preserved':True,'checks':checks,'runtime_verified':False}
    (out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='checks'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args();verify(a.build.resolve())
