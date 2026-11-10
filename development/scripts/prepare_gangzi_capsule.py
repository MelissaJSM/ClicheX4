"""Fit generated GangZi art to the original capsule's fixed tile budget."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_ui_revision import load,D
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.inventory_shibuki_ui import sheet
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels,write_tile
from src.psx_static_effect import compose_static

RGB=[(0,0,0),(16,16,32),(32,32,57),(49,49,82),(74,74,115),(115,115,156),
     (173,173,197),(222,222,230),(255,255,247),(156,82,66),(222,140,107),
     (255,189,148),(255,222,189),(123,74,16),(222,156,24),(255,222,99)]
WORDS=[0]+[0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10) for r,g,b in RGB[1:]]

def native_body():
    im=Image.open(D/'gangzi_generated.png').convert('RGBA');a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>=192,255,0)
    im=Image.fromarray(a);im=im.crop(im.getchannel('A').getbbox());nearest=im.resize((round(im.width*46/im.height),46),Image.Resampling.NEAREST);im=im.convert('RGBa');im.thumbnail((28,46),Image.Resampling.LANCZOS);im=im.convert('RGBA')
    canvas=Image.new('RGBA',(32,48));canvas.alpha_composite(im,((32-im.width)//2,48-im.height));a=np.array(canvas)
    # The subpixel gold eyes disappear under filtering. Preserve exact source
    # sampling across the face while filtering the larger costume clusters.
    sharp=Image.new('RGBA',(32,48));sharp.alpha_composite(nearest,((32-nearest.width)//2,2));a[13:19,13:24]=np.array(sharp)[13:19,13:24]
    d=((a[:,:,:3].astype(np.int32)[:,:,None,:]-np.array(RGB[1:],np.int32))**2).sum(3)
    return np.where(a[:,:,3]>=128,d.argmin(2)+1,0).astype('uint8')

def patch_capsules(current,changes,output):
    get=lambda n:changes.get(n,current[n]);a=native_body();layout=json.loads((D/'gangzi_cover.json').read_text());rects=layout['rects']
    if not layout['fits'] or len(rects)!=5:raise ValueError('GangZi five-tile cover missing')
    owner=np.full(a.shape,-1)
    for i,(x,y) in enumerate(rects):owner[y:y+16,x:x+16]=i
    if np.any((a>0)&(owner<0)):raise ValueError('GangZi outside capsule cover')
    # Preserve the native green hologram flash with a separate five-tile image.
    light=np.array([0]+[round(.2126*r+.7152*g+.0722*b) for r,g,b in RGB[1:]])
    flash=np.where(a==0,0,np.where(light[a]>205,1,np.where(light[a]>135,2,np.where(light[a]>65,3,4)))).astype('uint8')
    mouth=np.zeros((16,16),np.uint8);mouth[0,0:2]=9
    previews=[];proofs=[]
    for info in json.loads((D/'capsule_layout.json').read_text()):
        name=info['name'];bank=info['bank'];lo=info['offset'];hi=lo+10240;raw=get(name);g=entry(raw,0x10102);p=entry(raw,10);texture=g[lo:hi]
        comps={n:aliased_composition(p,bank,n) for n in range(58)}
        protected={q['page']*256+q['tile'] for n,c in comps.items() for i,q in enumerate(c['parts']) if n not in (6,7,21) or i<26}
        free=iter(t for t in range(80) if t not in protected);ng=bytearray(texture);np_=bytearray(p);patterns={tile_pixels(texture,t):t for t in sorted(protected)}
        def allocate(px):
            key=px.tobytes()
            if key not in patterns:
                t=next(free,None)
                if t is None:raise ValueError('Capsule atlas capacity exceeded')
                patterns[key]=t;write_tile(ng,t,key)
            return patterns[key]
        for n in (6,7,21):
            body=a if n!=21 else flash;parts=comps[n]['parts'][26:32]
            for i,q in enumerate(parts):
                k=min(i,4);x,y=rects[k];px=np.where(owner[y:y+16,x:x+16]==k,body[y:y+16,x:x+16],0).astype('uint8');t=allocate(px);off=q['record_offset']
                np_[off:off+4]=bytes(((3 if n!=21 else 1)<<2,t,(x-16)&255,(y-58)&255))
            if n==7:
                q=comps[n]['parts'][32];off=q['record_offset'];np_[off:off+4]=bytes((12,allocate(mouth),(18-16)&255,(18-58)&255))
        protected_frames=0
        for n,c in comps.items():
            nc=aliased_composition(np_,bank,n)
            oldpart=c if n not in (6,7,21) else {**c,'parts':c['parts'][:26]}
            newpart=nc if n not in (6,7,21) else {**nc,'parts':nc['parts'][:26]}
            if compose_static(texture,local_composition(oldpart))[:3]!=compose_static(ng,local_composition(newpart))[:3]:raise ValueError('Capsule machine/untargeted frame changed')
            if n not in (6,7,21):protected_frames+=1
        for t in protected:
            if tile_pixels(ng,t)!=tile_pixels(texture,t):raise ValueError('Protected capsule tile changed')
        changes[name]=replace_entry(replace_entry(raw,0x10102,g[:lo]+bytes(ng)+g[hi:]),10,bytes(np_))
        pals=[]
        for suffix in ('X','Z'):
            cn=f'COL{name[2:4]}_{name[6]}{suffix}.ARC';cr=get(cn);pal=bytearray(entry(cr,5));row=info['pal_base']+3
            expected=struct.pack('<16H',0,*([0x8000]*15))
            if pal[row*32:(row+1)*32]!=expected:raise ValueError('Capsule private palette is not blank')
            pal[row*32:(row+1)*32]=struct.pack('<16H',*WORDS);changes[cn]=replace_entry(cr,5,bytes(pal));pals.append([cn,row])
        proofs.append({'file':name,'bank':bank,'texture_offset':lo,'protected_frames':protected_frames,'protected_tiles':len(protected),'total_patterns':len(patterns),'palette_copies':pals,'mouth_frame':7,'hologram_frame':21,'original_animation_data_preserved':True})
        if len(proofs)==1:
            for n in (6,7,21):
                c=aliased_composition(np_,bank,n);px,sz,bb,_=compose_static(ng,local_composition(c));canvas=Image.new('RGBA',sz)
                pal=entry(get(pals[0][0]),5)
                for q in c['parts']:
                    words=struct.unpack_from('<16H',pal,(info['pal_base']+q['clut'])*32);tile=Image.frombytes('P',(16,16),tile_pixels(ng,q['tile']));colors=[]
                    for w in words:colors.extend((w>>s&31)*255//31 for s in (0,5,10))
                    tile.putpalette(colors+[0]*(768-len(colors)));tile.info['transparency']=0;tile=tile.convert('RGBA')
                    if q['flip_x']:tile=tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    if q['flip_y']:tile=tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    canvas.alpha_composite(tile,(q['x']-bb[0],q['y']-bb[1]))
                canvas.save(output/f'gangzi_capsule_{n}.png');previews.append((f'capsule {n}',canvas.resize((sz[0]*3,sz[1]*3),Image.Resampling.NEAREST)))
    sheet(previews,output/'gangzi_capsule_review.png',3,(310,420))
    save_image(a.tobytes(),(32,48),WORDS,output/'gangzi_native.png')
    return {'copies':proofs,'source_sha256':digest(D/'gangzi_generated.png'),'reference_sha256':digest(ROOT/'character/dr_light/light.webp'),'body_rects':rects,'runtime_verified':False}

def plan():
    from scripts.solve_sprite_cover import cover
    a=native_body();save_image(a.tobytes(),(32,48),WORDS,D/'gangzi_native.png')
    result=cover(a>0,5,25);(D/'gangzi_cover.json').write_text(json.dumps(result,indent=2))
    print(result)

if __name__=='__main__':plan()
