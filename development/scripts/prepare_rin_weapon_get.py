"""린 기술 획득/타이틀 공유 액션 그림. 기존 배경 타일 예산 안에서 교체한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_illustrations import background_replace
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_rin_dialogue import WORDS,PALETTE
from scripts.inventory_shibuki_ui import background
from scripts.extract_zero import save_image
from scripts.discover_inputs import DiscReader,sha256
from scripts.project import digest

PARENT=ROOT/'out/ver_rin_nana/rin_pause_20261029T024843444660Z'
PARENT_SHA='72ee194dd9370a6654474018a2cd448b997e38807071f058fb5cd0248515c4ff'
ART=ROOT/'work/ver_rin_nana/illustrations/weapon_get_v1'
SCREENS={'ST0E_U0.ARC':('COL0E_U0.ARC',[1,2]),'ST0F_UX.ARC':('COL0F_U0.ARC',[3,4]),'ST0F_UZ.ARC':('COL0F_U0.ARC',[3,4])}

def sources():
    if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Accepted pause parent differs')
    names=sorted(set(SCREENS)|{v[0] for v in SCREENS.values()});records={};raw={}
    with (PARENT/'rin_nana.bin').open('rb') as f:
        disc=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size);iso={r['name'].split(';')[0]:r for r in disc.inspect()['files']}
        for name in names:
            rec=iso[name];raw[name]=disc.read(rec['lba'],rec['size']);records[name]={**rec,'sha256':sha256(raw[name])}
    return records,raw

def native():
    source=Image.open(ART/'generated.png').convert('RGBA');box=source.getchannel('A').getbbox();source=source.crop(box)
    scale=min(308/source.width,230/source.height);dims=(round(source.width*scale),round(source.height*scale))
    source=source.convert('RGBa').resize(dims,Image.Resampling.LANCZOS).convert('RGBA')
    position=((320-dims[0])//2,250-dims[1]);canvas=Image.new('RGBA',(512,256));canvas.paste(source,position);a=np.array(canvas)
    colors=np.array([[(v>>s&31)*255//31 for s in (0,5,10)] for v in WORDS[1:]],np.int32)
    distance=((a[:,:,:3].astype(np.int32)[:,:,None,:]-colors)**2).sum(3)
    return np.where(a[:,:,3]>=128,distance.argmin(2)+1,0).astype(np.uint8),{'source_bbox':box,'uniform_scale':scale,'size':dims,'position':position,'canvas':[512,256],'visible_canvas':[320,256]}

def overlay(original,picture):
    new=dict(original);packing={}
    for name,(palname,ids) in SCREENS.items():
        new[name],packing[name]=background_replace(original[name],ids,picture,80,preserve_zero_tile=True)
    for palname in {v[0] for v in SCREENS.values()}:
        data=entry(original[palname],5);new[palname]=replace_entry(original[palname],5,data[:2560]+PALETTE+data[2592:])
    return new,packing

def verify(original,new,picture):
    if picture.shape!=(256,512) or picture.dtype!=np.uint8 or picture.max()>15 or picture[:,320:].any():raise ValueError('Invalid native action illustration')
    if set(new)!=set(original) or new!=overlay(original,picture)[0]:raise ValueError('Unexpected bytes beyond action artwork')
    expected=np.zeros((256,512,4),np.uint8)
    for i,w in enumerate(WORDS[1:],1):expected[picture==i]=[*(int(w>>s&31)*255//31 for s in (0,5,10)),255]
    preserved=0;changed=[]
    for name,(palname,ids) in SCREENS.items():
        oldpal,newpal=entry(original[palname],5),entry(new[palname],5)
        for screen in range(len(entry(original[name],0))//512):
            before=background(original[name],oldpal,screen);after=background(new[name],newpal,screen)
            if screen in ids:
                j=ids.index(screen)
                if not np.array_equal(np.array(after),expected[:,j*256:(j+1)*256]):raise ValueError('Background tile/palette readback differs')
                changed.append([name,screen])
            else:
                if before.tobytes()!=after.tobytes():raise ValueError('Other screen or character changed')
                preserved+=1
    return {'copied_artwork_blocks':changed,'other_screens_rgba_exact':preserved,'other_arc_bytes_exact':True,
        'player_untouched':True,'fixed_resource_lengths':True,'palette_row':80,'opaque_colors':len(set(picture.tobytes())-{0}),
        'actual_tilemap_palette_render_equal':True,'runtime_verified':False}

def prepare(out):
    records,original=sources();picture,conversion=native();new,packing=overlay(original,picture);v=verify(original,new,picture)
    out.mkdir(parents=True,exist_ok=False)
    for name,data in new.items():(out/name).write_bytes(data)
    preview=save_image(picture.tobytes(),(512,256),WORDS,out/'action.png');preview.crop((0,0,320,256)).resize((960,768),Image.Resampling.NEAREST).save(out/'action_3x.png')
    (out/'palette.bin').write_bytes(PALETTE)
    r={'kind':'rin_weapon_get','parent_sha256':PARENT_SHA,'tool':'built-in image_gen',
        'art':(ART/'generated.png').relative_to(ROOT).as_posix(),'art_sha256':digest(ART/'generated.png'),
        'prompt':(ART/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(ART/'prompt.txt'),
        'action_sha256':digest(out/'action.png'),'conversion':conversion,'packing':packing,'verification':v,
        'files':[{'file':n,'source':records[n],'sha256':sha256(new[n])} for n in sorted(new)]}
    (out/'recipe.json').write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'packing':packing,'verification':v}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);prepare(p.parse_args().output)
