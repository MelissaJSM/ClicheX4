"""Native indexed Riko illustration overlays with protected atlas resources."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_riko_illustrations import read_sources,D
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.project import digest
from scripts.discover_inputs import DiscReader,psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_ui_atlas import aliased_composition,local_composition,repack_frames,tile_pixels,write_tile
from src.psx_static_effect import compose_static,patch_static
from src.psx_text import rename_zero

RGB=[(0,0,0),(16,24,45),(41,52,76),(91,102,132),(156,167,189),(239,247,247),
     (16,80,72),(49,144,128),(132,198,156),(198,231,165),(214,140,107),(247,189,148),
     (255,222,181),(0,181,173),(148,115,198),(99,49,74)]
WORDS=[0]+[(r>>3)|((g>>3)<<5)|((b>>3)<<10)|0x8000 for r,g,b in RGB[1:]]
PAL=struct.pack('<16H',*WORDS)

def native(path,size,box=None,position=None,flip=False,source_crop=None):
    im=Image.open(path).convert('RGBA');a=np.array(im)
    if source_crop is not None:im=im.crop(source_crop);a=np.array(im)
    # Convert the generated alpha to the game's binary transparent index.
    a[:,:,3]=np.where(a[:,:,3]>=192,255,0)
    im=Image.fromarray(a);im=im.crop(im.getchannel('A').getbbox())
    if flip:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    im.thumbnail(box or size,Image.Resampling.LANCZOS)
    pos=position if position is not None else ((size[0]-im.width)//2,size[1]-im.height)
    canvas=Image.new('RGBA',size);canvas.alpha_composite(im,pos);a=np.array(canvas)
    colors=np.array(RGB[1:],np.int32)
    distance=((a[:,:,:3].astype(np.int32)[:,:,None,:]-colors)**2).sum(3)
    return np.where(a[:,:,3]>=128,distance.argmin(2)+1,0).astype('uint8')

def coverage(texture,c):
    px,size,bounds,sources=compose_static(texture,local_composition(c))
    return np.array([bool(s) for s in sources]).reshape(size[1],size[0]),size,bounds

def save(arr,path):save_image(arr.tobytes(),(arr.shape[1],arr.shape[0]),WORDS,path)

def native_body(path,size,bounds):
    im=Image.open(path).convert('RGBA');a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>=192,255,0)
    im=Image.fromarray(a);im=im.crop(im.getchannel('A').getbbox())
    im=im.resize((round(im.width*104/im.height),104),Image.Resampling.LANCZOS)
    a=np.array(im);ys,xs=np.where(a[82:,:,3]>=128)
    center=(int(xs.min())+int(xs.max())+1)//2
    canvas=Image.new('RGBA',size);canvas.alpha_composite(im,(-bounds[0]-center,size[1]-104));a=np.array(canvas)
    distance=((a[:,:,:3].astype(np.int32)[:,:,None,:]-np.array(RGB[1:],np.int32))**2).sum(3)
    return np.where(a[:,:,3]>=128,distance.argmin(2)+1,0).astype('uint8')

def repack_one_bank(g,p,bank,targets,overrides=None,reserved_tiles=()):
    first=struct.unpack_from('<I',p)[0];offsets=struct.unpack_from('<'+'I'*(first//4),p)
    start=offsets[bank];end=min((x for x in offsets if x>start),default=len(p))
    one=struct.pack('<I',4)+p[start:end]
    ng,np,report=repack_frames(g,one,0,targets,overrides,reserved_tiles=reserved_tiles)
    result=p[:start]+np[4:]+p[end:]
    assert len(result)==len(p)
    return ng,result,report

def regrid_ui_parts(parts,bank,targets):
    """Fit new UI silhouettes in the existing part budget; keep frame anchors/counts."""
    out=bytearray(parts);demands={}
    for n,(pixels,size) in targets.items():
        c=aliased_composition(parts,bank,n);xs=[p['x'] for p in c['parts']];ys=[p['y'] for p in c['parts']]
        bx,by=min(xs),min(ys);a=np.frombuffer(pixels,dtype='uint8').reshape(size[1],size[0]);positions=[]
        for y in range(0,size[1],16):
            for x in range(0,size[0],16):
                xx=min(x,size[0]-16);yy=min(y,size[1]-16)
                if a[yy:yy+16,xx:xx+16].any() and (xx,yy) not in positions:positions.append((xx,yy))
        for pos in [(0,0),(size[0]-16,size[1]-16)]:
            if pos not in positions:positions.append(pos)
        if len(positions)>len(c['parts']):raise ValueError('UI part budget exceeded')
        positions += [positions[-1]]*(len(c['parts'])-len(positions))
        for p,(x,y) in zip(c['parts'],positions):
            offset=p['record_offset']+2;value=bytes(((bx+x)&255,(by+y)&255))
            if offset in demands and demands[offset]!=value:raise ValueError('Conflicting UI coordinate alias')
            demands[offset]=value;out[offset:offset+2]=value
    return bytes(out)

def name_labels(font):
    small=np.zeros((32,64),dtype='uint8');large=np.zeros((48,208),dtype='uint8')
    for j,ch in enumerate('RIKO'):
        index='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'.index(ch)
        glyph=np.array(Image.frombytes('L',(16,16),tile_pixels(font,index)))
        small[8:24,j*16:(j+1)*16]=glyph
        glyph=Image.frombytes('L',(16,16),tile_pixels(font,index+64)).resize((32,32),Image.Resampling.NEAREST)
        a=np.array(glyph);colored=np.where(a==0,0,np.where(a>=12,2,np.where(a>=8,4,np.where(a>=4,12,1)))).astype('uint8')
        large[8:40,8+j*52:40+j*52]=colored
    return small,large

def background_replace(raw,screen_ids,picture,palette_row,preserve_zero_tile=False):
    """Repack two 256px screen blocks, preserving every other background tile."""
    g=entry(raw,0x10000);mp=entry(raw,0);info=entry(raw,1)
    vals=struct.unpack('<'+'I'*(len(info)//4),info)
    maps=struct.unpack('<'+'H'*(len(mp)//2),mp)
    reserved_ids={v&0x3fff for i,v in enumerate(maps) if i//256 not in screen_ids}-{0}
    # New callers can explicitly preserve the transparent map0 backing tile.
    # Keep the historical default so frozen first-mode recipes stay reproducible.
    if preserve_zero_tile:reserved_ids.add(0)
    reserved_tiles={vals[i]>>16&0xfff for i in reserved_ids}
    available_ids=iter(i for i in range(1,len(vals)) if i not in reserved_ids)
    available_tiles=iter(i for i in range(len(g)//128) if i not in reserved_tiles)
    outg,outm,outi=bytearray(g),bytearray(mp),bytearray(info);patterns={};used=[]
    for sidx,s in enumerate(screen_ids):
        for y in range(16):
            for x in range(16):
                tile=picture[y*16:(y+1)*16,(sidx*16+x)*16:(sidx*16+x+1)*16].tobytes()
                if not any(tile):tid=0
                else:
                    if tile not in patterns:
                        tid=next(available_ids,None);slot=next(available_tiles,None)
                        if tid is None or slot is None:raise ValueError('Background fixed tile capacity exceeded')
                        patterns[tile]=tid;used.append(slot);write_tile(outg,slot,tile)
                        struct.pack_into('<I',outi,tid*4,(slot<<16)|((palette_row-64)<<8))
                    tid=patterns[tile]
                struct.pack_into('<H',outm,s*512+y*32+x*2,tid)
    for tid in reserved_ids:
        if outi[tid*4:tid*4+4]!=info[tid*4:tid*4+4]:raise AssertionError('Other background attribute changed')
    for tile in reserved_tiles:
        if tile_pixels(g,tile)!=tile_pixels(outg,tile):raise AssertionError('Other background pixels changed')
    for i in range(len(mp)//512):
        if i not in screen_ids and outm[i*512:(i+1)*512]!=mp[i*512:(i+1)*512]:raise AssertionError('Other screen changed')
    raw=replace_entry(replace_entry(replace_entry(raw,0x10000,bytes(outg)),0,bytes(outm)),1,bytes(outi))
    return raw,{'screens':screen_ids,'new_patterns':len(patterns),'protected_tiles':len(reserved_tiles),'palette_row':palette_row}

def prepare(parent,out):
    out.mkdir(exist_ok=False);sources=read_sources();original={r['name'].split(';')[0]:b for r,b in sources};records={r['name'].split(';')[0]:r for r,b in sources}
    manifest=json.loads((parent/'manifest.json').read_text());current={}
    with (parent/manifest['bin_file']).open('rb') as f:
        d=DiscReader(f,(parent/manifest['bin_file']).stat().st_size)
        for name,r in records.items():current[name]=d.read(r['lba'],r['size'])
    changes={};checks={}
    def get(name):return changes.get(name,current[name])
    def setpal(name,row,pal=PAL):
        raw=get(name);p=bytearray(entry(raw,5));p[row*32:(row+1)*32]=pal;changes[name]=replace_entry(raw,5,bytes(p))

    # The rejected large select portrait is replaced; accepted small sprites stay exact.
    raw=get('ST0E_U1.ARC');g=entry(raw,0x10102);p=entry(raw,0xa);bank=g[40960:90112]
    cov,size,_=coverage(bank,aliased_composition(p,1,1))
    arr=native(D/'selection_generated.png',size,(190,158),(1,1));clipped=int(np.count_nonzero(arr[~cov]));arr[~cov]=0
    edge=Image.new('L',size);ImageDraw.Draw(edge).polygon([(1,1),(190,1),(190,158),(52,158)],outline=6,width=4)
    arr=np.where(arr,arr,np.array(edge)).astype('uint8');arr[~cov]=0
    save(arr,out/'select_portrait.png')
    smallname,bigname=name_labels(entry(original['LOAD_U.ARC'],0x10001))
    select_targets={1:(arr.tobytes(),size),4:(smallname.tobytes(),(64,32)),7:(bigname.tobytes(),(208,48))}
    ng,newparts,checks['selection']=repack_one_bank(bank,p,1,select_targets,{7:0})
    for n,a,row in [(4,smallname,6),(7,bigname,4)]:
        pal=entry(original['COL0E_U1.ARC'],5)[row*32:(row+1)*32]
        save_image(a.tobytes(),(a.shape[1],a.shape[0]),struct.unpack('<16H',pal),out/f'name_{n}.png')
    changes['ST0E_U1.ARC']=replace_entry(replace_entry(raw,0x10102,g[:40960]+ng+g[90112:]),0xa,newparts)
    setpal('COL0E_U1.ARC',5);checks['select_coverage_clipped_pixels']=clipped

    # Shared dialogue 3-frame atlas: one head and only the mouth-region variants.
    raw=original['ST00_00.ARC'];p=entry(raw,0xa);head=entry(raw,0x10102)[217088:223232]
    closed=native(D/'dialogue_generated.png',(112,96),(104,92),(2,0))
    opened=native(D/'dialogue_open_generated.png',(112,96),(104,92),(2,0))
    talking=closed.copy();talking[57:66,70:81]=opened[57:66,70:81]
    small=closed.copy();small[60:64,70:81]=opened[59:63,70:81]
    targets={0:(talking.tobytes(),(112,96)),1:(closed.tobytes(),(112,96)),2:(small.tobytes(),(112,96))}
    newhead,newp,checks['dialogue']=repack_one_bank(head,p,13,targets)
    oldbank=p[struct.unpack_from('<I',p,13*4)[0]:];newbank=newp[struct.unpack_from('<I',newp,13*4)[0]:]
    for n,(px,size) in targets.items():save_image(px,size,WORDS,out/f'dialogue_{n}.png')
    copies=[]
    for name,source in original.items():
        if not name.startswith('ST'):continue
        raw=get(name)
        for e in records[name].get('entries',[]):
            if int(e['type'],16)>>16!=1:continue
            data=raw[e['offset']:e['offset']+e['size']];start=data.find(head)
            if start<0:continue
            if data.find(head,start+1)>=0:raise ValueError('Ambiguous dialogue copy')
            raw=raw[:e['offset']+start]+newhead+raw[e['offset']+start+len(head):]
            copies.append({'file':name,'entry':e['index'],'graphics_offset':start})
        # Part copies are shared/aliased independently of the texture copies.
        if any(e['type']=='0xa' for e in records[name].get('entries',[])):
            parts=entry(raw,0xa);count=parts.count(oldbank)
            if count:raw=replace_entry(raw,0xa,parts.replace(oldbank,newbank))
        if raw!=get(name):changes[name]=raw
    checks['dialogue_copies']=copies
    p0=entry(original['COL00_0Z.ARC'],5)[63*32:64*32];palette_copies=[]
    for name,source in original.items():
        if not name.startswith('COL'):continue
        pal=entry(source,5)
        for row in range(len(pal)//32):
            if pal[row*32:(row+1)*32]==p0:setpal(name,row);palette_copies.append((name,row))
    checks['dialogue_palette_copies']=palette_copies

    # Hunter base: preserve original frame count, timings, part geometry and foot line.
    name='ST0D_0Z.ARC';raw=get(name);g=entry(raw,0x10102);p=entry(raw,0xa);lo,hi=63488,81920;targets={};clip=[]
    for n in range(14):
        c=aliased_composition(p,2,n);cov,size,bounds=coverage(g[lo:hi],c)
        pose='idle_v2' if n<=5 else 'talk' if n<=9 else 'alert' if n<=12 else 'fly'
        box=(62,104) if n<13 else (76,88)
        if n<13:
            arr=native_body(D/f'base_{pose}_generated.png',size,bounds)
            cx=-bounds[0]
            if n in (1,2):
                blink=native_body(D/'base_blink_generated.png',size,bounds)
                arr[18:26,cx-8:cx+10]=blink[18:26,cx-8:cx+10]
            if n in (3,4,5):
                talk=native_body(D/'base_talk_generated.png',size,bounds)
                arr[25:29,cx:cx+8]=talk[25:29,cx:cx+8]
            if n in (8,11):
                closed=native_body(D/'base_idle_v2_generated.png',size,bounds)
                arr[25:29,cx:cx+8]=closed[25:29,cx:cx+8]
        else:arr=native(D/f'base_{pose}_generated.png',size,box)
        clip.append(int(np.count_nonzero(arr[~cov])))
        save(arr,out/f'base_{n:02d}.png');targets[n]=(arr.tobytes(),size)
    p=regrid_ui_parts(p,2,targets)
    ng,newparts,checks['base']=repack_one_bank(g[lo:hi],p,2,targets,{n:0 for n in targets})
    checks['base_clipping_prevented_by_ui_grid']=clip
    checks['base_part_positions_changed_within_original_canvas']=True
    changes[name]=replace_entry(replace_entry(raw,0x10102,g[:lo]+ng+g[hi:]),0xa,newparts)
    setpal('COL0D_0Z.ARC',35)

    # Pause portrait uses a fixed tile base +0x60, original menu shape and CLUT 74.
    name='PL01_U.ARC';raw=get(name);g=entry(raw,0x10007);p=struct.pack('<I',4)+entry(raw,0x12)
    c=local_composition(aliased_composition(p,0,10));cov,size,_=coverage(g[96*128:],c)
    arr=native(D/'dialogue_generated.png',size,(62,78),(1,1),source_crop=(370,30,1230,1120));arr[~cov]=0;save(arr,out/'pause_portrait.png')
    newg=patch_static(g[96*128:],{10:c},{10:(arr.tobytes(),size)})
    raw=replace_entry(raw,0x10007,g[:96*128]+newg);pal=bytearray(entry(raw,0x11));pal[10*32:11*32]=PAL
    raw=replace_entry(raw,0x11,bytes(pal));text,checks['text_changes']=rename_zero(entry(raw,0x15));raw=replace_entry(raw,0x15,text);changes[name]=raw

    # The same large saber art is used by title and the weapon/skill acquisition scene.
    title=native(D/'title_generated.png',(320,256),(308,230),(4,18));save(title,out/'title_portrait.png')
    full=np.zeros((256,512),dtype='uint8');full[:,:320]=title
    checks['backgrounds']={}
    for name,ss in [('ST0E_U0.ARC',[1,2]),('ST0F_UZ.ARC',[3,4]),('ST0F_UX.ARC',[3,4])]:
        changes[name],checks['backgrounds'][name]=background_replace(get(name),ss,full,80)
    for name in ['COL0E_U0.ARC','COL0F_U0.ARC']:setpal(name,80)

    # Keep a bound, reviewable recipe; no BIN is written by this preparation step.
    files=[]
    for name,data in sorted(changes.items()):
        old=current[name]
        if len(data)!=len(old):raise ValueError('Illustration resource resize')
        (out/name).write_bytes(data)
        files.append({'source':records[name],'parent_sha256':sha256(old),'file':name,'sha256':sha256(data),
                      'changed_bytes_from_parent':sum(a!=b for a,b in zip(old,data))})
    (out/'palette.bin').write_bytes(PAL)
    recipe={'schema_version':1,'source_sha256':manifest['source_sha256'],'parent_build':str(parent.resolve()),
            'parent_manifest_sha256':digest(parent/'manifest.json'),'files':files,'checks':checks,
            'generated_assets':{p.name:digest(p) for p in D.glob('*generated.png')}}
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf8')
    print(json.dumps({'output':str(out),'files':len(files),'text_changes':len(checks['text_changes']),
                      'dialogue_copies':len(checks['dialogue_copies']),'base_tiles':checks['base']['allocated_patterns']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();prepare(a.parent,a.output)
