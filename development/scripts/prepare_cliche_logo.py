"""Pack one generated wordmark into native, fixed-size PS1 logo resources."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_cliche_logo import D,PARENT,PARENT_HASH,SOURCE_HASH,REFERENCE_HASH,load,indexed
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.inventory_shibuki_ui import background,sheet
from scripts.discover_inputs import sha256
from scripts.project import digest
from src.psx_ui_atlas import aliased_composition,local_composition,repack_frames,tile_pixels,write_tile
from src.psx_static_effect import compose_static
from src.psx_ui_render import render_static_rgba

TITLE_FRAMES=(0,10,11,12,13,14,15,16,17)

def colors(words):
    return np.array([((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,0 if i==0 else 255) for i,w in enumerate(words)],np.uint8)

def image_indices(a,words):return Image.fromarray(colors(words)[a])

def quantize(im,words):
    a=np.array(im.convert('RGBA'));c=colors(words)[1:,:3].astype(np.int32)
    dist=((a[:,:,:3].astype(np.int32)[:,:,None,:]-c)**2).sum(3)
    return np.where(a[:,:,3]>=128,dist.argmin(2)+1,0).astype(np.uint8)

def generated_word():
    im=Image.open(D/'cliche_word_generated.png').convert('RGBA');a=np.array(im)
    a[:,:,3]=np.where(a[:,:,3]>=192,255,0);im=Image.fromarray(a)
    return im.crop(im.getchannel('A').getbbox())

def fit_title_parts(parts,targets):
    out=bytearray(parts);demands={}
    for n,(pixels,size) in targets.items():
        c=aliased_composition(parts,0,n);bx=min(p['x'] for p in c['parts']);by=min(p['y'] for p in c['parts'])
        a=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0]);positions=[]
        for x in range(0,size[0],16):
            x=min(x,size[0]-16);y=0
            while y<size[1]:
                ys=np.where(a[y:,x:x+16].any(1))[0]
                if not len(ys):break
                y=min(y+int(ys[0]),size[1]-16);positions.append((x,y));y+=16
        for xy in ((0,0),(size[0]-16,size[1]-16)):
            if xy not in positions:positions.append(xy)
        if len(positions)>len(c['parts']):raise ValueError(f'Title part budget {n}: {len(positions)}')
        positions += [positions[-1]]*(len(c['parts'])-len(positions))
        for p,(x,y) in zip(c['parts'],positions):
            offset=p['record_offset']+2;value=bytes(((bx+x)&255,(by+y)&255))
            if offset in demands and demands[offset]!=value:raise ValueError('Title alias differs')
            demands[offset]=value;out[offset:offset+2]=value
    return bytes(out)

def words_at(raw,row):return struct.unpack_from('<16H',raw,row*32)

def background_indices(raw):
    g=entry(raw,0x10000);mp=np.frombuffer(entry(raw,0),'<u2');info=np.frombuffer(entry(raw,1),'<u4')
    a=np.zeros((240,320),np.uint8);rows=np.zeros_like(a)
    for y in range(15):
        for x in range(20):
            v=int(mp[256+(x//16)*256+y*16+x%16]);attr=int(info[v&16383])
            tile=np.frombuffer(tile_pixels(g,attr>>16&4095),np.uint8).reshape(16,16)
            if v&0x4000:tile=np.fliplr(tile)
            if v&0x8000:tile=np.flipud(tile)
            a[y*16:y*16+16,x*16:x*16+16]=tile;rows[y*16:y*16+16,x*16:x*16+16]=(attr>>8&63)+64
    return a,rows

def write_background(raw,pixels):
    g=bytearray(entry(raw,0x10000));mp=np.frombuffer(entry(raw,0),'<u2');info=np.frombuffer(entry(raw,1),'<u4');demands={}
    protected={int(info[int(i)&16383])>>16&4095 for i in np.r_[mp[:256],mp[768:]] if i&16383}
    for y in range(15):
        for x in range(20):
            v=int(mp[256+(x//16)*256+y*16+x%16]);tid=int(info[v&16383])>>16&4095
            tile=pixels[y*16:y*16+16,x*16:x*16+16]
            if v&0x4000:tile=np.fliplr(tile)
            if v&0x8000:tile=np.flipud(tile)
            data=tile.tobytes()
            if tid in protected or tid in demands and demands[tid]!=data:raise ValueError('Conflicting background tile')
            demands[tid]=data;write_tile(g,tid,data)
    return replace_entry(raw,0x10000,bytes(g)),sorted(demands)

def mono_logo(im,noise,words):
    """Fit the common generated art to an existing low-contrast native palette."""
    rgb=colors(words)[1:,:3].astype(float);lum=rgb@np.array([.2126,.7152,.0722])
    levels=(lum-lum.min())/max(1,lum.max()-lum.min())
    rgba=np.array(im);face=rgba[:,:,:3]@np.array([.2126,.7152,.0722])/255
    value=np.where(rgba[:,:,3]>=128,.08+.88*face,noise)
    return (np.abs(value[:,:,None]-levels).argmin(2)+1).astype(np.uint8)

def prepare(out):
    if not out.resolve().is_relative_to(D.resolve()):raise ValueError('Wrong candidate path')
    rr,old=load();out.mkdir(exist_ok=False);new={};checks={};word=generated_word();items=[]
    # Keep native X4, copyright, menu text, effects and palette animation.
    name='ST0E_U0.ARC';raw=old[name];g=entry(raw,0x10002);p=struct.pack('<I',4)+entry(raw,0x12)
    pal=entry(old['COL0E_U0.ARC'],5);targets={}
    for n in TITLE_FRAMES:
        c=aliased_composition(p,0,n);px,size,bounds,_=compose_static(g,local_composition(c))
        a=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);ys,xs=np.where(a)
        box=(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)
        width=round((box[2]-box[0])*.8)
        canvas=Image.new('RGBA',size);canvas.alpha_composite(word.resize((width,box[3]-box[1]),Image.Resampling.LANCZOS),(box[0]+(box[2]-box[0]-width)//2,box[1]))
        arr=quantize(canvas,words_at(pal,0));targets[n]=(arr.tobytes(),size)
        np.save(out/f'title_{n}.npy',arr);im=image_indices(arr,words_at(pal,0));im.save(out/f'title_{n}.png');items.append((f'TITLE {n}',im))
    nparts=fit_title_parts(p,targets);ng,np1,checks['title']=repack_frames(g,nparts,0,targets)
    new[name]=replace_entry(replace_entry(raw,0x10002,ng),0x12,np1[4:])
    # Loading uses a hard-coded 80x32 rectangle. Keep its missing transparent
    # upper-left tile and the accepted SHIBUKI/RIKO name allocations untouched.
    menu=old['MOJIPAT.ARC'];starts=struct.unpack_from('<4I',menu);lp=menu[starts[1]:starts[2]]
    raw=old['LOAD_U.ARC'];g=entry(raw,0x10008);a=indexed(g).copy();canvas=Image.new('RGBA',(80,32))
    canvas.alpha_composite(word.resize((64,21),Image.Resampling.LANCZOS),(16,7))
    arr=quantize(canvas,words_at(lp,2));assert not arr[:16,:16].any()
    a[112:144,:80]=arr;np.save(out/'loading_word.npy',arr)
    im=image_indices(arr,words_at(lp,2));im.save(out/'loading_word.png');items.append(('LOADING word',im))
    # The original loading X4 is a separate 64x32 piece at UV(80,112), drawn
    # 48px to the right of the word. The same composition is the motif master.
    x4=indexed(g)[112:144,80:144];logo=Image.new('RGBA',(112,32))
    logo.alpha_composite(image_indices(x4,words_at(lp,3)),(48,0));logo.alpha_composite(im,(0,0));logo.save(out/'combined_small.png')
    # Native save/load renderer 80016124: UV(0,208) 112x48 logo, UV(112,208)
    # 96x48 filler, CLUT 0x784c = (y481,x192) = palette 28. Keep filler/icons.
    filler=indexed(g)[208:256,112:208];frgb=colors(words_at(lp,28))[filler][:,:,:3].mean(2)
    normalized=(frgb-frgb.min())/max(1,float(frgb.max()-frgb.min()))
    yy,xx=np.indices((48,112));noise=.48+.18*normalized[yy,xx%96]
    stamp=Image.new('RGBA',(112,48));stamp.alpha_composite(logo,(0,2))
    save_logo=mono_logo(stamp,noise,words_at(lp,28))
    # Preserve the filler grain's exact color indices around the new lettering.
    a[208:256,:112]=np.where(np.array(stamp)[:,:,3]>=128,save_logo,filler[yy,(xx-112)%96])
    np.save(out/'save_pattern.npy',a[208:256,:112]);image_indices(a[208:256,:208],words_at(lp,28)).save(out/'save_pattern.png')
    flat=a.reshape(-1);packed=(flat[::2]|flat[1::2]<<4).tobytes();new['LOAD_U.ARC']=replace_entry(raw,0x10008,packed)
    checks['loading']={'word_rect':[0,112,80,32],'save_logo_rect':[0,208,112,48],'save_palette':28,'exe_unchanged':True,'mojipat_unchanged':True}
    # Tile the common motif over the original grain sample, using the exact
    # per-row palettes and map cells. Preserve all player illustration tiles.
    backdrop=Image.new('RGBA',(320,240))
    for row in range(-1,5):
        for col in range(-1,3):
            backdrop.alpha_composite(logo,(col*208+(row%2)*64+12,row*64+12))
    yy,xx=np.indices((240,320));noise=.52+.12*normalized[yy%48,(xx+(yy//48)*19)%96]
    checks['backgrounds']={}
    for name,palname in [('ST0E_U1.ARC','COL0E_U1.ARC'),('ST0F_UX.ARC','COL0F_U0.ARC'),('ST0F_UZ.ARC','COL0F_U0.ARC')]:
        raw=old[name];before,rows=background_indices(raw);pal=entry(old[palname],5);arr=np.empty_like(before)
        for row in np.unique(rows):
            mono=mono_logo(backdrop,noise,words_at(pal,int(row)));arr[rows==row]=mono[rows==row]
        new[name],tiles=write_background(raw,arr);checks['backgrounds'][name]={'tiles':tiles,'screens':[1,2]}
        np.save(out/f'{name}_background.npy',arr)
        preview=Image.new('RGBA',(320,240));preview.paste(background(new[name],pal,1),(0,0));preview.paste(background(new[name],pal,2).crop((0,0,64,240)),(256,0));preview.save(out/f'{name}_background.png');items.append((name+' pattern',preview))
    sheet(items,out/'overview.png',3,(360,270))
    files={}
    for name,raw in new.items():
        if len(raw)!=len(old[name]):raise ValueError('Resource resized')
        (out/name).write_bytes(raw);files[name]={'before':sha256(old[name]),'after':sha256(raw),'changed_bytes':sum(a!=b for a,b in zip(old[name],raw))}
    recipe={'kind':'cliche_logo','parent':str(PARENT.relative_to(ROOT)),'parent_sha256':PARENT_HASH,'source_sha256':SOURCE_HASH,'reference_sha256':REFERENCE_HASH,'generated_sha256':digest(D/'cliche_word_generated.png'),'files':files,'records':{n:rr[n] for n in new},'checks':checks}
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2));print(json.dumps({'output':str(out),'files':list(files)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
