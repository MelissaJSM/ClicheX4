"""나나 기술 획득/타이틀 공유 액션 그림. 수용 린/로고 배경을 보존한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_illustrations import background_replace
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_nana_dialogue import WORDS,PAL as PALETTE
from scripts.inventory_shibuki_ui import background
from scripts.extract_zero import save_image
from scripts.discover_inputs import DiscReader,sha256
from scripts.project import digest

PARENT=ROOT/'out/ver_rin_nana/nana_pause_20261030T030037246376Z'
PARENT_SHA='7e37be210bc3afe161396301738c2e188340523341c6fa75080f7368165a3f56'
ART=ROOT/'work/ver_rin_nana/illustrations/nana_weapon_get_v1'
SCREENS={'ST0E_U0.ARC':('COL0E_U0.ARC',[6]),'ST0F_UX.ARC':('COL0F_U0.ARC',[5]),'ST0F_UZ.ARC':('COL0F_U0.ARC',[5])}

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
    # Align the silhouette to fit the title resource's 96 free map IDs.
    scale=min(188/source.width,237/source.height);dims=(round(source.width*scale),round(source.height*scale))
    source=source.convert('RGBa').resize(dims,Image.Resampling.LANCZOS).convert('RGBA')
    position=(192-dims[0],248-dims[1]);canvas=Image.new('RGBA',(256,256));canvas.paste(source,position);a=np.array(canvas)
    colors=np.array([[(v>>s&31)*255//31 for s in (0,5,10)] for v in WORDS[1:]],np.int32)
    distance=((a[:,:,:3].astype(np.int32)[:,:,None,:]-colors)**2).sum(3)
    return np.where(a[:,:,3]>=192,distance.argmin(2)+1,0).astype(np.uint8),{'source_bbox':box,'uniform_scale':scale,'size':dims,'position':position,'canvas':[256,256],'art_box':[4,8,192,248]}

def overlay(original,picture):
    new=dict(original);packing={}
    for name,(palname,ids) in SCREENS.items():
        new[name],packing[name]=background_replace(original[name],ids,picture,81,preserve_zero_tile=True)
    for palname in {v[0] for v in SCREENS.values()}:
        data=entry(original[palname],5);new[palname]=replace_entry(original[palname],5,data[:2592]+PALETTE+data[2624:])
    return new,packing

def verify(original,new,picture):
    if picture.shape!=(256,256) or picture.dtype!=np.uint8 or picture.max()>15 or picture[:,192:].any() or picture[:8].any() or picture[248:].any():raise ValueError('Invalid native action illustration')
    if set(new)!=set(original) or new!=overlay(original,picture)[0]:raise ValueError('Unexpected bytes beyond action artwork')
    expected=np.zeros((256,256,4),np.uint8)
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
        'player_untouched':True,'fixed_resource_lengths':True,'palette_row':81,'opaque_colors':len(set(picture.tobytes())-{0}),
        'actual_tilemap_palette_render_equal':True,'runtime_verified':False}

def prepare(out):
    records,original=sources();picture,conversion=native();new,packing=overlay(original,picture);v=verify(original,new,picture)
    out.mkdir(parents=True,exist_ok=False)
    for name,data in new.items():(out/name).write_bytes(data)
    preview=save_image(picture.tobytes(),(256,256),WORDS,out/'action.png');preview.resize((768,768),Image.Resampling.NEAREST).save(out/'action_3x.png')
    (out/'palette.bin').write_bytes(PALETTE)
    r={'kind':'nana_weapon_get','parent_sha256':PARENT_SHA,'parent_manifest_sha256':digest(PARENT/'manifest.json'),'tool':'built-in image_gen',
        'art':(ART/'generated.png').relative_to(ROOT).as_posix(),'art_sha256':digest(ART/'generated.png'),
        'prompt':(ART/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(ART/'prompt.txt'),
        'action_sha256':digest(out/'action.png'),'conversion':conversion,'packing':packing,'verification':v,
        'files':[{'file':n,'source':records[n],'sha256':sha256(new[n])} for n in sorted(new)]}
    (out/'recipe.json').write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'packing':packing,'verification':v}))

def inventory():
    records,raw=sources();ART.mkdir(parents=True,exist_ok=True);items=[]
    from scripts.inventory_shibuki_ui import sheet
    for n,(pn,ids)in SCREENS.items():
        for s in range(len(entry(raw[n],0))//512):
            im=background(raw[n],entry(raw[pn],5),s);im.save(ART/f'{n}_{s}.png');items.append((f'{n} / {s}',im))
    sheet(items,ART/'inventory.png',5,(260,280));(ART/'sources.json').write_text(json.dumps(records,indent=2)+'\n','utf8');print(json.dumps({'files':len(raw),'screens':len(items),'selected':SCREENS}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inventory',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args();inventory()if a.inventory else prepare(a.output)
