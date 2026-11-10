"""One US title object and a separate readable native-size menu emblem."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_cliche_logo import D,PARENT,PARENT_HASH,SOURCE_HASH,REFERENCE_HASH,load,indexed
from scripts.prepare_cliche_logo import colors,quantize,image_indices,words_at,mono_logo,write_background,background_indices
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.inventory_shibuki_ui import background,sheet
from scripts.project import digest
from scripts.discover_inputs import sha256
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels,write_tile
from src.psx_static_effect import compose_static

TITLE_TARGETS={0,1,10,11,12,13,14,15,16,17,26,27,28,32,33,34}

def full_art():
    im=Image.open(D/'cliche_full_generated.png').convert('RGBA');a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>=192,255,0)
    im=Image.fromarray(a);return im.crop(im.getchannel('A').getbbox())

def micro_art():
    im=Image.open(D/'cliche_micro_generated.png').convert('RGBA');a=np.array(im)
    a[:,:,3]=np.where(a[:,:,3]>=192,255,0);im=Image.fromarray(a)
    im=im.crop(im.getchannel('A').getbbox()).resize((112,24),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(112,32));out.alpha_composite(im,(0,4));return out

def title_palette():
    rgb=[(8,8,32),(16,24,72),(24,32,136),(32,64,216),(88,128,216),
         (120,136,176),(184,208,232),(248,248,248),(64,24,32),(152,48,8),
         (232,72,8),(248,136,8),(248,208,16),(248,240,136),(216,232,248)]
    return (0,)+tuple(round(r*31/255)|(round(g*31/255)<<5)|(round(b*31/255)<<10) for r,g,b in rgb)

def loading_palettes(exe):
    # US func_80013404 calls func_800160F4 every loading frame. It uploads
    # D_800F1660 from the EXE, not the MOJIPAT palette used by old previews.
    base=struct.unpack_from('<I',exe,0x18)[0];offset=0x800F1660-base+0x800
    if exe[:8]!=b'PS-X EXE' or exe[offset:offset+8]!=bytes.fromhex('00002184638ca594'):
        raise ValueError('Unexpected US loading palette table')
    return exe[offset:offset+512]

def small_layers(small,pal):
    warm=warm_mask(small);left=quantize(small,words_at(pal,2))[:,:80];right=quantize(small,words_at(pal,3))[:,48:]
    left[:,48:]=np.where(warm[:,48:80],0,left[:,48:]);right[:,:32]=np.where(warm[:,48:80],right[:,:32],0)
    return left,right

def warm_mask(im):
    a=np.array(im).astype(float)
    return (a[:,:,0]>120)&(a[:,:,0]>a[:,:,2]*1.2)&(a[:,:,1]>a[:,:,2])&(a[:,:,3]>=128)

def old_records(parts,bank):
    out=[]
    for n in range(aliased_composition(parts,bank,0)['bank_frame_count']):
        c=aliased_composition(parts,bank,n);out.append([parts[p['record_offset']:p['record_offset']+4] for p in c['parts']])
    return out

def pack_bank(frames,length):
    """Compact same-bank part lists with exact substream deduplication."""
    headers=bytearray(len(frames)*4);body=bytearray();seen={}
    for n,records in enumerate(frames):
        blob=b''.join(records);start=seen.get(blob)
        if start is None:
            start=next((i for i in range(0,len(body)-len(blob)+1,4) if body[i:i+len(blob)]==blob),None)
        if start is None:start=len(body);body.extend(blob)
        seen[blob]=start;offset=(len(headers)+start)//4
        struct.pack_into('<I',headers,n*4,(offset<<16)|len(records))
    used=len(headers)+len(body)
    if used>length:raise ValueError(f'Fixed bank capacity {used}>{length}')
    return bytes(headers+body+bytes(length-used)),{'used':used,'capacity':length,'spare':length-used}

def grid_parts(arr,origin,clut,allocate):
    h,w=arr.shape;parts=[]
    for y in range(0,h,16):
        for x in range(0,w,16):
            xx=min(x,w-16);yy=min(y,h-16);px=arr[yy:yy+16,xx:xx+16]
            if not px.any():continue
            # Grid overlap at nonmultiples must not double-draw pixels.
            if yy!=y or xx!=x:raise ValueError('Use a padded 16px native canvas')
            tx,ty=origin[0]+x,origin[1]+y
            if not -128<=tx<=127 or not -128<=ty<=127:raise ValueError('Part coordinate overflow')
            tile=allocate(px.tobytes());parts.append(struct.pack('<BBbb',tile//256|(clut<<2),tile%256,tx,ty))
    if not parts:
        tile=allocate(bytes(256));parts=[struct.pack('<BBbb',tile//256|(clut<<2),tile%256,*origin)]
    return parts

def prepare(out):
    if not out.resolve().is_relative_to(D.resolve()):raise ValueError('Wrong candidate path')
    rr,old=load();out.mkdir(exist_ok=False);new={};checks={};art=full_art();items=[]
    # User-requested 8px left shift, limited to the two US loading logo X
    # coordinates. Preserve names, text, UVs, dimensions, palettes and code.
    exe=old['SLUS_005.61'];ne=bytearray(exe);table=0xDED04
    if exe[table+8:table+24]!=bytes.fromhex('d000c000700502020001c00075040203'):
        raise ValueError('US loading logo rectangle table differs')
    struct.pack_into('<h',ne,table+8,200);struct.pack_into('<h',ne,table+16,248)
    edits=[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(exe,ne)) if a!=b]
    if len(edits)!=3:raise ValueError('Loading X-coordinate scope differs')
    new['SLUS_005.61']=bytes(ne)
    checks['loading_position']={'shift_x':-8,'before':[208,256],'after':[200,248],'y':192,'right_margin':8,'exe_data_edits':edits,'user_request':'로딩화면 로고 ... 조금 왼쪽으로 이동해줄래?','code_changed':False}
    raw=old['ST0E_U0.ARC'];g=entry(raw,0x10002);p=struct.pack('<I',4)+entry(raw,0x12);frames=old_records(p,0)
    reserved={q['page']*256+q['tile'] for n in range(35) if n not in TITLE_TARGETS for q in aliased_composition(p,0,n)['parts']}
    free=iter(i for i in range(len(g)//128) if i not in reserved);patterns={tile_pixels(g,t):t for t in sorted(reserved)};ng=bytearray(g)
    def allocate(px):
        if px not in patterns:
            t=next(free,None)
            if t is None:raise ValueError('Title atlas full')
            patterns[px]=t;write_tile(ng,t,px)
        return patterns[px]
    pal=entry(old['COL0E_U0.ARC'],5);main=art.resize((240,64),Image.Resampling.LANCZOS);words=title_palette()
    # US stable title actually draws objects 18/19/0/11/12, not objects 0/1.
    # Put the complete blue/gold emblem in object 0 alone. Blank the old
    # backing and X/4 fragments, keeping all frame IDs and original timing.
    master=quantize(main,words)
    frames[0]=grid_parts(master,(-104,-32),0,allocate);frames[17]=frames[0]
    targets={0:(master,(-104,-32)),17:(master,(-104,-32))}
    for n,h in zip(range(10,17),(8,16,24,32,40,48,56)):
        im=Image.fromarray(np.array(main)).resize((240,h),Image.Resampling.LANCZOS)
        ix=quantize(im,words)
        hh=(h+15)//16*16;arr=np.zeros((hh,240),np.uint8);arr[(hh-h)//2:(hh-h)//2+h]=ix
        origin=(-104,-hh//2);frames[n]=grid_parts(arr,origin,0,allocate);targets[n]=(arr,origin)
    for n in (1,26,27,28,32,33,34):
        arr=np.zeros((16,16),np.uint8);frames[n]=grid_parts(arr,(0,0),0,allocate);targets[n]=(arr,(0,0))
    npart,checks['title_bank']=pack_bank(frames,len(p)-4)
    fade=[]
    for phase in range(15):
        row=[]
        for i,w in enumerate(words):
            channels=[(w>>s)&31 for s in (0,5,10)]
            row.append(0 if i==0 else sum(round(31+(c-31)*phase/14)<<s for c,s in zip(channels,(0,5,10))))
        fade.extend(row*2)
    new['ST0E_U0.ARC']=replace_entry(replace_entry(replace_entry(raw,0x10002,bytes(ng)),0x12,npart),0xD,struct.pack('<480H',*fade))
    new['COL0E_U0.ARC']=replace_entry(old['COL0E_U0.ARC'],5,struct.pack('<16H',*words)+pal[32:])
    checks['title_palette']=list(words)
    checks['stable_title_objects']=[{'object':n,'frame':f,'anchor':[x,72]} for n,f,x in [(18,26,128),(19,32,176),(0,0,144),(11,27,208),(12,28,248)]]
    checks['title_targets']={}
    for n,(arr,origin) in targets.items():
        np.save(out/f'title_{n}.npy',arr);checks['title_targets'][str(n)]={'origin':origin,'size':[arr.shape[1],arr.shape[0]]}
    merged=Image.new('RGBA',(320,144));merged.alpha_composite(image_indices(master,words),(40,40));merged.save(out/'title_complete.png');items.append(('TITLE single object / native 1x',merged))
    # Complete small logo over two fixed loading draw rectangles (overlap32px).
    menu=old['MOJIPAT.ARC'];starts=struct.unpack_from('<4I',menu);lp=menu[starts[1]:starts[2]];small=micro_art()
    # Preserve the already reviewed monochrome motifs exactly; only the
    # loading/demo texture indices need remapping to the actual EXE CLUT.
    motif_left,motif_right=small_layers(small,lp)
    motif=Image.new('RGBA',(112,32));motif.alpha_composite(image_indices(motif_right,words_at(lp,3)),(48,0));motif.alpha_composite(image_indices(motif_left,words_at(lp,2)))
    loading_pal=loading_palettes(old['SLUS_005.61']);left,right=small_layers(small,loading_pal)
    checks['loading_palettes']={'source':'SLUS_005.61 / D_800F1660 / func_800160F4','address':0x800F1660,'row2':list(words_at(loading_pal,2)),'row3':list(words_at(loading_pal,3)),'exe_palette_changed':False}
    raw=old['LOAD_U.ARC'];g=entry(raw,0x10008);a=indexed(g).copy();a[112:144,:80]=left;a[112:144,80:144]=right
    # Restore the full 10-part left rectangle in the shared demo composition.
    mf=old_records(menu,2);mf[1]=[struct.pack('<BBbb',0,112+y*16+x,x*16,y*16) for y in range(2) for x in range(5)]
    # Exchange the former blank left-corner part for the new right layer's
    # genuinely transparent upper-left part. This keeps the bank byte budget.
    if right[:16,:16].any():raise ValueError('Expected transparent right-layer corner')
    omitted=[q for q in mf[2] if q[1]==117]
    if len(omitted)!=1:raise ValueError('Unexpected small logo topology')
    mf[2]=[q for q in mf[2] if q[1]!=117]
    blank=next(t for t in range(112) if not any(tile_pixels(g,t)))
    moved=[]
    for n,records in enumerate(mf):
        if n in (1,2):continue
        for j,q in enumerate(records):
            if q[0]&3==0 and q[1]==112:
                records[j]=q[:1]+bytes([blank])+q[2:];moved.append([n,j])
    checks['blank_aliases']={'old_tile':112,'new_tile':blank,'parts':moved}
    bank,checks['menu_bank']=pack_bank(mf,starts[3]-starts[2]);new['MOJIPAT.ARC']=menu[:starts[2]]+bank+menu[starts[3]:]
    logo=Image.new('RGBA',(112,32));logo.alpha_composite(image_indices(right,words_at(loading_pal,3)),(48,0));logo.alpha_composite(image_indices(left,words_at(loading_pal,2)));logo.save(out/'loading_complete.png');items.append(('LOADING actual EXE palette / native 1x',logo))
    expected=np.array(small)[:,:,3]>=128;actual=np.array(logo)[:,:,3]>0
    if not np.array_equal(expected,actual):raise ValueError('Small logo alpha lost across draw rectangles')
    np.save(out/'loading_left.npy',left);np.save(out/'loading_right.npy',right)
    filler=indexed(g)[208:256,112:208];frgb=colors(words_at(lp,28))[filler][:,:,:3].mean(2);norm=(frgb-frgb.min())/max(1,float(frgb.max()-frgb.min()))
    yy,xx=np.indices((48,112));noise=.48+.18*norm[yy,xx%96];stamp=Image.new('RGBA',(112,48));stamp.alpha_composite(motif,(0,2))
    ix=mono_logo(stamp,noise,words_at(lp,28));a[208:256,:112]=np.where(np.array(stamp)[:,:,3]>=128,ix,filler[yy,(xx-112)%96]);np.save(out/'save_pattern.npy',a[208:256,:112]);image_indices(a[208:256,:208],words_at(lp,28)).save(out/'save_pattern.png')
    flat=a.reshape(-1);new['LOAD_U.ARC']=replace_entry(raw,0x10008,(flat[::2]|flat[1::2]<<4).tobytes())
    backdrop=Image.new('RGBA',(320,240))
    for row in range(-1,5):
        for col in range(-1,3):backdrop.alpha_composite(motif,(col*208+(row%2)*64+12,row*64+12))
    yy,xx=np.indices((240,320));noise=.52+.12*norm[yy%48,(xx+(yy//48)*19)%96];checks['backgrounds']={}
    for name,palname in [('ST0E_U1.ARC','COL0E_U1.ARC'),('ST0F_UX.ARC','COL0F_U0.ARC'),('ST0F_UZ.ARC','COL0F_U0.ARC')]:
        raw=old[name];before,rows=background_indices(raw);pal=entry(old[palname],5);arr=np.empty_like(before)
        for row in np.unique(rows):
            mono=mono_logo(backdrop,noise,words_at(pal,int(row)));arr[rows==row]=mono[rows==row]
        new[name],tiles=write_background(raw,arr);checks['backgrounds'][name]={'tiles':tiles,'screens':[1,2]};np.save(out/f'{name}_background.npy',arr)
        im=Image.new('RGBA',(320,240));im.paste(background(new[name],pal,1),(0,0));im.paste(background(new[name],pal,2).crop((0,0,64,240)),(256,0));im.save(out/f'{name}_background.png');items.append((name,im))
    sheet(items,out/'overview.png',2,(400,285));files={}
    for name,raw in new.items():
        if len(raw)!=len(old[name]):raise ValueError('Resource resized')
        (out/name).write_bytes(raw);files[name]={'before':sha256(old[name]),'after':sha256(raw),'changed_bytes':sum(a!=b for a,b in zip(old[name],raw))}
    recipe={'kind':'cliche_logo_v3','parent':str(PARENT.relative_to(ROOT)),'parent_sha256':PARENT_HASH,'source_sha256':SOURCE_HASH,'reference_sha256':REFERENCE_HASH,'generated_sha256':digest(D/'cliche_full_generated.png'),'micro_generated_sha256':digest(D/'cliche_micro_generated.png'),'files':files,'records':{n:rr[n] for n in new},'checks':checks}
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2));print(json.dumps({'out':str(out),'files':len(new),'title_bank':checks['title_bank']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
