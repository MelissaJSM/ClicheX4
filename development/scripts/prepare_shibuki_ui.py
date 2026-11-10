"""Prepare isolated Shibuki UI overlays, preserving accepted gameplay/Riko data."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_shibuki_ui import load,D,PARENT,background,sheet
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_riko_illustrations import repack_one_bank,regrid_ui_parts,background_replace
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256,psx_arc
from scripts.project import digest
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels,repack_frames
from src.psx_static_effect import compose_static,patch_static
from src.psx_player import graphics_bank,decode_stream,compose_indices,composition_frame

RGB=[(0,0,0),(28,24,49),(67,49,105),(115,83,164),(166,139,213),(218,197,246),
     (246,246,255),(172,197,238),(99,131,197),(115,24,49),(205,41,65),(246,115,131),
     (238,156,123),(255,222,189),(230,172,57),(255,180,189)]
WORDS=[0]+[0x8000|((r>>3)|((g>>3)<<5)|((b>>3)<<10)) for r,g,b in RGB[1:]]
PAL=struct.pack('<16H',*WORDS)

def native(path,size,box=None,pos=None,crop=None,flip=False):
    im=Image.open(path).convert('RGBA')
    if crop:im=im.crop(crop)
    a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>=192,255,0);im=Image.fromarray(a);bbox=im.getchannel('A').getbbox()
    if bbox is None:raise ValueError('Empty generated image')
    im=im.crop(bbox)
    if flip:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    im=im.convert('RGBa');im.thumbnail(box or size,Image.Resampling.LANCZOS);im=im.convert('RGBA')
    canvas=Image.new('RGBA',size);canvas.alpha_composite(im,pos or ((size[0]-im.width)//2,size[1]-im.height))
    a=np.array(canvas);colors=np.array(RGB[1:],np.int32)
    distance=((a[:,:,:3].astype(np.int32)[:,:,None,:]-colors)**2).sum(3)
    return np.where(a[:,:,3]>=128,distance.argmin(2)+1,0).astype('uint8')

def save(arr,path,pal=WORDS):return save_image(arr.tobytes(),(arr.shape[1],arr.shape[0]),pal,path)

def text_mask(font,text,height):
    glyphs=[]
    for ch in text:
        if ch==' ':glyphs.append(np.zeros((height,max(3,height//3)),bool));continue
        a=np.frombuffer(tile_pixels(font,'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'.index(ch)),dtype='uint8').reshape(16,16)
        im=Image.fromarray(np.uint8(a>=8)*255);im=im.crop(im.getbbox());im=im.resize((round(im.width*height/im.height),height),Image.Resampling.NEAREST)
        glyphs.append(np.array(im)>0)
    gap=max(1,height//12);mask=np.zeros((height,sum(a.shape[1] for a in glyphs)+gap*(len(glyphs)-1)),bool);x=0
    for a in glyphs:mask[:,x:x+a.shape[1]]=a;x+=a.shape[1]+gap
    return mask

def label(font,text,size,height):
    mask=text_mask(font,text,height)
    while mask.shape[1]>size[0]-6:height-=1;mask=text_mask(font,text,height)
    full=np.zeros((size[1],size[0]),bool);x=(size[0]-mask.shape[1])//2;y=(size[1]-height)//2;full[y:y+height,x:x+mask.shape[1]]=mask
    border=np.zeros_like(full)
    for dy in (-1,0,1):
        for dx in (-1,0,1):border|=np.roll(np.roll(full,dy,0),dx,1)
    out=np.zeros(full.shape,dtype='uint8');out[np.roll(border,1,0)]=2;out[border]=1;out[full]=15
    out[y+height*3//4:][full[y+height*3//4:]]=14
    return out

def actual(arc,n,bank=0):
    g=entry(arc,2);p=entry(arc,3);f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n]
    raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    return compose_indices(raw,f['tile_count'],local_composition(composition_frame(p,bank,n)))[:3]

def transfer_geometry(parts,bank,target,source,flip=False,dy=0):
    p=bytearray(parts);c=aliased_composition(parts,bank,target)
    if len(c['parts'])<len(source['parts']):raise ValueError('UI/player part count mismatch')
    src=source['parts']+[source['parts'][0]]*(len(c['parts'])-len(source['parts']))
    for old,new in zip(c['parts'],src):
        off=old['record_offset'];p[off]=((old['flags']&15)|((new['flags']&0xc0)^(64 if flip else 0)))
        x=-new['x']-16 if flip else new['x'];p[off+2:off+4]=bytes((x&255,(new['y']+dy)&255))
    return bytes(p)

def register(frame,size,bounds,flip=False):
    data,ss,bb=frame;a=np.frombuffer(data,dtype='uint8').reshape(ss[1],ss[0]);a=a[:,::-1] if flip else a
    # Flip about the original world origin, preserving anchor and sole height.
    bx=-bb[2] if flip else bb[0];by=bb[1];out=np.zeros((size[1],size[0]),dtype='uint8')
    for yy,xx in zip(*np.nonzero(a)):
        x=int(xx)+bx-bounds[0];y=int(yy)+by-bounds[1]
        if not (0<=x<size[0] and 0<=y<size[1]):raise ValueError(f'UI sprite outside canvas at {x,y}')
        out[y,x]=a[yy,xx]
    return out

def static_repack(texture,parts,targets,cluts=None):
    """Repack selected static frames while protecting every other static bank."""
    from src.psx_ui_atlas import write_tile
    selected=set(targets);comps={}
    for b in range(struct.unpack_from('<I',parts)[0]//4):
        if b in (0,5,6,7,8):continue
        for n in range(aliased_composition(parts,b,0)['bank_frame_count']):
            c=aliased_composition(parts,b,n)
            try:compose_static(texture,local_composition(c))
            except ValueError:continue
            comps[b,n]=c
    protected={p['page']*256+p['tile'] for k,c in comps.items() if k not in selected for p in c['parts']}
    free=iter(t for t in range(len(texture)//128) if t not in protected);allocated={tile_pixels(texture,t):t for t in sorted(protected)}
    outg,outp=bytearray(texture),bytearray(parts);demands={}
    for key,arr in sorted(targets.items()):
        c=comps[key];_,size,bb,sources=compose_static(texture,local_composition(c));data=arr.ravel()
        if arr.shape!=(size[1],size[0]) or arr.max()>15:raise ValueError('Static replacement shape/palette mismatch')
        if any(v and not loc for v,loc in zip(data,sources)):raise ValueError('Static pixel has no part')
        owners=np.full(arr.shape,-1)
        for j,p in enumerate(c['parts']):owners[p['y']-bb[1]:p['y']-bb[1]+16,p['x']-bb[0]:p['x']-bb[0]+16]=j
        for j,p in enumerate(c['parts']):
            x,y=p['x']-bb[0],p['y']-bb[1];tile=np.where(owners[y:y+16,x:x+16]==j,arr[y:y+16,x:x+16],0).astype('uint8')
            if p['flip_x']:tile=tile[:,::-1]
            if p['flip_y']:tile=tile[::-1]
            px=tile.tobytes()
            if px not in allocated:
                slot=next(free,None)
                if slot is None:raise ValueError('Static atlas capacity exceeded')
                allocated[px]=slot;write_tile(outg,slot,px)
            slot=allocated[px];flags=(p['flags']&~3)|(slot//256)
            if cluts and key in cluts:flags=(flags&~12)|(cluts[key]<<2)
            value=bytes((flags,slot%256));off=p['record_offset']
            if off in demands and demands[off]!=value:raise ValueError('Static alias conflict')
            demands[off]=value;outp[off:off+2]=value
    for key,c in comps.items():
        new=aliased_composition(outp,*key);px,size,bb,_=compose_static(outg,local_composition(new))
        expected=targets[key].tobytes() if key in targets else compose_static(texture,local_composition(c))[0]
        if px!=expected:raise ValueError('Static protected frame changed')
        if key not in selected and new!=c:raise ValueError('Static protected parts changed')
    return bytes(outg),bytes(outp),{'target_frames':[list(k) for k in sorted(selected)],'protected_static_frames':len(comps)-len(selected),'protected_tiles':len(protected),'allocated_patterns':len(allocated)}

def compact_regrid(parts,bank,targets):
    from scripts.solve_sprite_cover import cover
    out=bytearray(parts);demands={};cache={};group_rects={}
    diskpath=D/'hq_layout_cache.json';disk=json.loads(diskpath.read_text('utf8')) if diskpath.exists() else {}
    original_targets=dict(targets)
    for n,(px,size) in targets.items():
        c=aliased_composition(parts,bank,n);bx=min(p['x'] for p in c['parts']);by=min(p['y'] for p in c['parts']);a=np.frombuffer(px,dtype='uint8').reshape(size[1],size[0])
        oldw=max(p['x']+16 for p in c['parts'])-bx;oldh=max(p['y']+16 for p in c['parts'])-by
        bx-=(size[0]-oldw)//2;by-=size[1]-oldh
        group=[0,1,2,11] if n in (0,1,2,10,11) else [3,4,5] if n in (3,4,5) else [6,7,8] if n in (6,7,8) else [n]
        mask=np.zeros_like(a,dtype=bool)
        for k in group:mask|=np.frombuffer(original_targets[k][0],dtype='uint8').reshape(a.shape)>0
        key=(size,mask.tobytes(),len(c['parts']));dk=sha256(mask.tobytes()+bytes(size)+bytes([len(c['parts'])]))
        if tuple(group) in group_rects:cache[key]=group_rects[tuple(group)]
        if key not in cache:
            if dk in disk:cache[key]=disk[dk]
            else:
                result=cover(mask,len(c['parts']),25);cache[key]=result['rects'] if result['fits'] else None
                if result['fits']:disk[dk]=result['rects'];diskpath.write_text(json.dumps(disk),encoding='utf8')
        rects=cache[key]
        if rects is None:raise ValueError(f'UI frame {n} cannot fit original part budget')
        if len(rects)>len(c['parts']):raise ValueError('Shared UI layout exceeds part budget')
        group_rects[tuple(group)]=rects
        if n==10:rects=[[size[0]-16-x,y] for x,y in rects]
        positions=[list(r) for r in rects];positions+=[positions[-1]]*(len(c['parts'])-len(positions))
        for p,(x,y) in zip(c['parts'],positions):
            off=p['record_offset'];value=bytes(((p['flags']&15)|(64 if n==10 else 0),p['tile'],(bx+x)&255,(by+y)&255))
            if off in demands and demands[off]!=value:raise ValueError('UI geometry alias conflict')
            demands[off]=value;out[off:off+4]=value
        x0=min(x for x,y in positions);y0=min(y for x,y in positions);x1=max(x+16 for x,y in positions);y1=max(y+16 for x,y in positions)
        targets[n]=(a[y0:y1,x0:x1].tobytes(),(x1-x0,y1-y0))
    return bytes(out)

def panel_layout(mask,part_count):
    """Deterministic strip cover, including both canvas anchors."""
    height,width=mask.shape;best=None
    for shift in range(16):
        rects=[]
        for y in sorted(set([0,height-16]+list(range(shift,height-15,16)))):
            last=-1
            for x in np.flatnonzero(mask[y:y+16].any(0)):
                if x<=last:continue
                x=min(int(x),width-16);rects.append([x,y]);last=x+15
        for i in range(len(rects)-1,-1,-1):
            uncovered=mask.copy()
            for j,(x,y) in enumerate(rects):
                if i!=j:uncovered[y:y+16,x:x+16]=False
            if not uncovered.any():rects.pop(i)
        for anchor in ([0,0],[width-16,height-16]):
            if anchor not in rects:rects.append(anchor)
        if best is None or len(rects)<len(best):best=rects
    return {'fits':len(best)<=part_count,'rects':best}

def prepare(out):
    out.mkdir(exist_ok=False);records,original,current=load();changes={};checks={};previews=[]
    def get(n):return changes.get(n,current[n])
    def setpal(n,row,pal=PAL):
        raw=get(n);p=bytearray(entry(raw,5));p[row*32:(row+1)*32]=pal;changes[n]=replace_entry(raw,5,bytes(p))
    def preview(arr,name,pal=WORDS):
        im=save(arr,out/(name+'.png'),pal).convert('RGBA');previews.append((name,im));return im
    # Selection portrait shares its original CLUT with Riko's name; give it row7.
    # Row7's PLAYER SELECT title is remapped without changing its silhouette.
    name='ST0E_U1.ARC';raw=get(name);g=entry(raw,0x10102);p=entry(raw,10);bank=g[40960:90112]
    arr=native(D/'selection_generated.png',(192,160),(190,158),(0,2))
    # Original slanted panel, matching the original X outline footprint.
    c=aliased_composition(p,1,0);_,size,bb,sources=compose_static(bank,local_composition(c))
    edge=Image.new('L',(192,160));ImageDraw.Draw(edge).polygon([(1,1),(124,1),(190,158),(1,158)],outline=3,width=4)
    panel=Image.new('L',(192,160));ImageDraw.Draw(panel).polygon([(1,1),(124,1),(190,158),(1,158)],fill=1)
    arr=np.where(np.array(panel),np.where(arr,arr,np.array(edge)),0).astype('uint8')
    # The old X part footprint has interior holes. Repack the whole slanted panel
    # instead of erasing new sleeves/body pixels to match that old silhouette.
    layout=panel_layout(arr>0,len(c['parts']));positions=[tuple(r) for r in layout['rects']]
    for pos in ((0,0),(176,144)):
        if pos not in positions:positions.append(pos)
    cover=np.zeros(arr.shape,bool)
    for x,y in positions:cover[y:y+16,x:x+16]=True
    if not layout['fits'] or len(positions)>len(c['parts']) or np.any((arr>0)&~cover):raise ValueError('Selection part layout does not cover the full illustration')
    positions+=[positions[-1]]*(len(c['parts'])-len(positions));pp=bytearray(p)
    for part,(x,y) in zip(c['parts'],positions):pp[part['record_offset']+2:part['record_offset']+4]=bytes(((bb[0]+x)&255,(bb[1]+y)&255))
    p=bytes(pp);preview(arr,'selection_portrait')
    font=entry(original['LOAD_U.ARC'],0x10001);targets={0:(arr.tobytes(),size)};cluts={0:3}
    for n,sz,h in [(3,(128,32),14),(5,(256,48),18)]:
        a=label(font,'TENKO SHIBUKI',sz,h);preview(a,f'selection_name_{n}',struct.unpack_from('<16H',entry(current['COL0E_U1.ARC'],5),6*32));targets[n]=(a.tobytes(),sz);cluts[n]=2
    c=aliased_composition(p,1,6);_,sz,_,_=compose_static(bank,local_composition(c));targets[6]=(bytes(sz[0]*sz[1]),sz);cluts[6]=2
    c=aliased_composition(p,1,2);px,sz,_,_=compose_static(bank,local_composition(c));oldwords=struct.unpack_from('<16H',entry(current['COL0E_U1.ARC'],5),7*32)
    oldrgb=np.array([[(v>>s&31)*255//31 for s in (0,5,10)] for v in oldwords]);newrgb=np.array(RGB)
    lut=np.array([0]+[min(range(1,7),key=lambda j:int(((oldrgb[i]-newrgb[j])**2).sum())) for i in range(1,16)],dtype='uint8');a=lut[np.frombuffer(px,dtype='uint8')].reshape(sz[1],sz[0]);targets[2]=(a.tobytes(),sz);cluts[2]=3
    p=regrid_ui_parts(p,1,{n:v for n,v in targets.items() if n in (3,5)})
    ng,p,checks['selection_large']=repack_one_bank(bank,p,1,targets,cluts);g=g[:40960]+ng+g[90112:];setpal('COL0E_U1.ARC',7)
    # Native gameplay silhouettes reused at native scale in the selection demo.
    mapping={0:0,1:85,2:86,3:87,4:88,5:89,6:90,7:91,8:92,18:207,19:156,20:157,21:158,22:159,24:161}
    targets={};player=current['PL00_U.ARC'];palbase=entry(player,9)[:32]
    for n,k in mapping.items():
        c=aliased_composition(p,2,n);_,sz,bb,_=compose_static(g[90112:],local_composition(c));fr=actual(player,k);flip=n in (19,20)
        p=transfer_geometry(p,2,n,composition_frame(entry(player,3),0,k),flip,bb[3]-fr[2][3])
        a=np.frombuffer(fr[0],dtype='uint8').reshape(fr[1][1],fr[1][0]);a=a[:,::-1].copy() if flip else a
        targets[n]=(a.tobytes(),fr[1]);preview(a,f'select_sprite_{n:02}',struct.unpack('<16H',palbase))
    ng,p,checks['selection_small']=repack_one_bank(g[90112:],p,2,targets,{n:0 for n in targets});g=g[:90112]+ng
    # CLUT 0x7840 is VRAM (0,481): COL uploads 16 rows per scanline,
    # so this is palette row16. Row64 belongs to the selection background.
    changes[name]=replace_entry(replace_entry(raw,0x10102,g),10,p);setpal('COL0E_U1.ARC',16,palbase)
    checks['selection_mapping']=mapping
    # Save/load base and all four independent equipment overlays use gameplay poses.
    menu=get('MOJIPAT.ARC');loadarc=get('LOAD_U.ARC');g=entry(loadarc,0x10008);targets={}
    # US menu constructor 0x8001BEB8: frames45..48 use bits1,2,4,8.
    # Arm type2 changes frame47's base CLUT from7808 to780A (+part offset1).
    for n,b in [(44,0),(45,5),(46,6),(47,7),(48,8)]:
        co=composition_frame(entry(player,3),b,0);menu=transfer_geometry(menu,2,n,co)
        fr=actual(player,0,b);targets[n]=fr[:2];preview(np.frombuffer(fr[0],dtype='uint8').reshape(fr[1][1],fr[1][0]),f'save_{n}',struct.unpack('<16H',palbase if b==0 else entry(player,9)[32:64]))
    ng,menu,checks['save_sprites']=repack_one_bank(g,menu,2,targets)
    po=struct.unpack_from('<I',menu,4)[0];menu=bytearray(menu);menu[po+8*32:po+9*32]=palbase;menu[po+9*32:po+10*32]=entry(player,9)[32:64]
    menu[po+11*32:po+12*32]=entry(player,9)[64:96]
    changes['MOJIPAT.ARC']=bytes(menu);changes['LOAD_U.ARC']=replace_entry(loadarc,0x10008,ng)
    # Eight X/armor dialogue frames, with only the mouth region varying per outfit.
    ref=original['ST00_00.ARC'];oldhead=entry(ref,0x10102)[204800:217088];p=entry(ref,10)
    closed=native(D/'dialogue_generated.png',(112,96),(112,96),(0,0));opened=native(D/'dialogue_open_generated.png',(112,96),(112,96),(0,0))
    armor=native(D/'dialogue_armor_generated.png',(112,96),(112,96),(0,0));targets={}
    for n in range(8):
        # US animation table 800F2E20: idle0..3; speech pairs n/n+4.
        # Low bits are independently equipped head/body armor, not mouth states.
        a=closed.copy()
        if n&1:a[:66]=armor[:66]
        if n&2:a[66:]=armor[66:]
        if n&4:a[57:63,64:71]=opened[57:63,64:71]
        targets[n]=(a.tobytes(),(112,96));preview(a,f'dialogue_{n}')
    checks['dialogue_frame_mapping']={n:{'head_armor':bool(n&1),'body_armor':bool(n&2),'mouth_open':bool(n&4)} for n in range(8)}
    start=struct.unpack_from('<I',p,11*4)[0];end=struct.unpack_from('<I',p,13*4)[0];oldparts=p[start:end]
    p=regrid_ui_parts(p,11,targets)
    ng,np_,checks['dialogue_atlas']=repack_one_bank(oldhead,p,11,targets,{n:0 for n in targets})
    newparts=np_[start:end]
    texcopies=[];partcopies=[]
    for name,source in original.items():
        if not name.startswith('ST'):continue
        raw=get(name)
        for e in records[name].get('entries',[]):
            if int(e['type'],16)>>16!=1:continue
            data=source[e['offset']:e['offset']+e['size']];pos=data.find(oldhead)
            if pos>=0:
                if data.find(oldhead,pos+1)>=0:raise ValueError('Ambiguous dialogue texture copy')
                off=e['offset']+pos
                if raw[off:off+len(oldhead)]!=oldhead:raise ValueError('Parent X dialogue unexpectedly modified')
                raw=raw[:off]+ng+raw[off+len(oldhead):];texcopies.append([name,off])
        if any(e['type']=='0xa' for e in records[name].get('entries',[])):
            pp=entry(raw,10)
            if oldparts in pp:partcopies.append([name,pp.count(oldparts)]);raw=replace_entry(raw,10,pp.replace(oldparts,newparts))
        if raw!=get(name):changes[name]=raw
    checks['dialogue_texture_copies']=texcopies;checks['dialogue_part_copies']=partcopies
    palmatches=[]
    # Row63 is Zero's portrait, not a second X outfit palette. All new X parts
    # explicitly use CLUT0, so only the X base row62 and its copies are needed.
    sourcepals=[entry(original['COL00_0X.ARC'],5)[62*32:63*32]]
    for name,source in original.items():
        if not name.startswith('COL'):continue
        p=entry(source,5)
        for row in range(len(p)//32):
            if p[row*32:(row+1)*32] in sourcepals:setpal(name,row);palmatches.append([name,row])
    checks['dialogue_palette_copies']=palmatches
    # Hunter HQ: reuse a stable face for idle/blink/talk, preserving frame timing.
    name='ST0D_0X.ARC';raw=get(name);g=entry(raw,0x10102);p=entry(raw,10);targets={}
    cells=[(i%3*512,i//3*512,i%3*512+512,i//3*512+512) for i in range(6)]
    for n in range(12):
        c=aliased_composition(p,2,n);_,sz,bb,_=compose_static(g[63488:75776],local_composition(c))
        pose=0 if n<3 or n>=10 else 1 if n<6 else 2 if n<9 else 3
        if n in (3,4,5):sz=(80,96)
        if n==9:sz=(96,96)
        crop=(0,512,580,1024) if n==9 else cells[pose]
        box=(74,90) if n in (3,4,5) else (88,88) if n==9 else (sz[0]-2,94)
        a=native(D/'hq_generated.png',sz,box,crop=crop)
        if n==10:a=a[:,::-1].copy()
        if n in (1,2):
            # Native idle is open -> half -> closed -> half, never a talk loop.
            blink=native(D/'hq_generated.png',sz,(sz[0]-2,94),crop=(590,512,1024,1024))
            if n==1:a[24,35:40]=blink[26,34:39]
            else:a[24:27,35:40]=blink[26:29,34:39]
        if n in (3,4):
            a[27:29,41:45]=13;a[28,42:44]=12 if n==3 else 9
        if n in (7,8):a[29,53:55]=[12,12] if n==7 else [9,11]
        targets[n]=(a.tobytes(),sz);preview(a,f'hq_{n:02}')
    p=compact_regrid(p,2,targets);ng,p,checks['hunter_base']=repack_one_bank(g[63488:75776],p,2,targets,{n:0 for n in targets})
    changes[name]=replace_entry(replace_entry(raw,0x10102,g[:63488]+ng+g[75776:]),10,p);setpal('COL0D_0X.ARC',35)
    # Pause portrait: native 64x80 frame, independent palette row10.
    raw=get('PL00_U.ARC');g=entry(raw,0x10007);p=struct.pack('<I',4)+entry(raw,0x12);c=local_composition(aliased_composition(p,0,10))
    _,sz,_,sources=compose_static(g[96*128:],c);a=native(D/'dialogue_generated.png',sz,(64,80));cov=np.array([bool(s) for s in sources]).reshape(sz[1],sz[0]);a[~cov]=0;preview(a,'pause_portrait')
    ng=patch_static(g[96*128:],{10:c},{10:(a.tobytes(),sz)});raw=replace_entry(raw,0x10007,g[:96*128]+ng)
    p=bytearray(entry(raw,0x11));p[10*32:11*32]=PAL;raw=replace_entry(raw,0x11,bytes(p))
    # Native HUD mark and warm white/gold death energy use existing shared palettes.
    g=entry(raw,0x10206);p=entry(raw,3);targets={}
    mark=Image.open(ROOT/'character/ver_buki_riko/buki(zero)_mark.webp').convert('RGBA').getchannel('A').resize((15,11),Image.Resampling.BOX);mask=np.array(mark)
    hudpal=struct.unpack('<16H',(ROOT/'work/ver_buki_riko/art_pilot/hud_mark_v1/hud_palette.bin').read_bytes())
    for n in range(69,78):
        px,sz,bb,_=compose_static(g,local_composition(aliased_composition(p,1,n)));a=np.frombuffer(px,dtype='uint8').reshape(sz[1],sz[0]).copy()
        # The emblem is at a common world-space location in all max-HP frames.
        top=26-bb[1];left=-18-bb[0]
        a[top:top+15,left-1:left+22]=0
        badge=Image.new('L',(21,14));dr=ImageDraw.Draw(badge)
        dr.polygon([(2,0),(18,0),(20,2),(20,11),(18,13),(2,13),(0,11),(0,2)],fill=14,outline=12)
        a[top:top+14,left:left+21]=np.array(badge)
        region=a[top+1:top+12,left+3:left+18];region[mask>=110]=10;region[(mask>=55)&(mask<110)]=11
        targets[1,n]=a
        if n in (69,77):preview(a,f'hud_{n}',hudpal)
    lut=np.arange(16,dtype='uint8');lut[[5,6,7,8,9,10,11,12]]=[5,1,2,3,4,2,2,3]
    for n in range(105,114):
        px,sz,_,_=compose_static(g,local_composition(aliased_composition(p,1,n)));a=lut[np.frombuffer(px,dtype='uint8')].reshape(sz[1],sz[0]);targets[1,n]=a;preview(a,f'death_{n}',struct.unpack_from('<16H',entry(current['COL00_0X.ARC'],5),2*32))
    ng,np_,checks['hud_death']=static_repack(g,p,targets)
    raw=replace_entry(replace_entry(raw,0x10206,ng),3,np_);changes['PL00_U.ARC']=raw
    # The separate Ultimate resource has identical UI assets. Preserve its body data.
    ultimate=get('PL02_U.ARC')
    for kind in (0x10007,0x11):
        if entry(ultimate,kind)!=entry(current['PL00_U.ARC'],kind):raise ValueError('Unexpected alternate UI source')
        ultimate=replace_entry(ultimate,kind,entry(raw,kind))
    ug,up,checks['alternate_hud_death']=static_repack(entry(ultimate,0x10206),entry(ultimate,3),targets)
    changes['PL02_U.ARC']=replace_entry(replace_entry(ultimate,0x10206,ug),3,up)
    # Same original large X art in title and both weapon-acquisition archives.
    title=native(D/'action_generated.png',(256,256),(188,240),(4,8));preview(title,'weapon_title')
    checks['backgrounds']={}
    for name,screen in [('ST0E_U0.ARC',6),('ST0F_UX.ARC',5),('ST0F_UZ.ARC',5)]:
        # Original X uses multiple background palettes; new artwork has a dedicated row.
        changes[name],checks['backgrounds'][name]=background_replace(get(name),[screen],title,81)
    for name in ('COL0E_U0.ARC','COL0F_U0.ARC'):setpal(name,81)
    # Validate protected gameplay entries and every Riko-only file.
    for e in psx_arc(current['PL00_U.ARC']):
        if int(e['type'],16) not in (3,0x10206,0x10007,0x11):
            a=e['offset'];b=a+e['size']
            if current['PL00_U.ARC'][a:b]!=changes['PL00_U.ARC'][a:b]:raise ValueError('Gameplay entry changed')
    files=[]
    for name,data in sorted(changes.items()):
        if data==current[name]:continue
        if len(data)!=len(current[name]):raise ValueError('ARC resize')
        (out/name).write_bytes(data);files.append({'source':records[name],'parent_sha256':sha256(current[name]),'file':name,'sha256':sha256(data),'changed_bytes':sum(a!=b for a,b in zip(current[name],data))})
    recipe={'schema_version':1,'kind':'shibuki_ui_illustrations','source_sha256':json.loads((PARENT/'manifest.json').read_text('utf8'))['source_sha256'],'parent_build':str(PARENT.relative_to(ROOT)),'parent_bin_sha256':digest(PARENT/'shibuki_riko.bin'),'parent_manifest_sha256':digest(PARENT/'manifest.json'),'files':files,'checks':checks,'generated_assets':{p.name:digest(p) for p in D.glob('*generated.png')},'runtime_verified':False,'text_pending':True,'exe_changed':False,'gameplay_preserved':True}
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf8');(out/'palette.bin').write_bytes(PAL);sheet(previews,out/'review.png',6,(260,220));print(json.dumps({'output':str(out),'files':len(files),'checks':list(checks)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output.resolve())
