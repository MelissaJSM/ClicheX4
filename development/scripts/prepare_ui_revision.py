"""Prepare approved UI registration/colors and the capsule NPC in fixed ARC slots."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_ui_revision import load,PARENT,PARENT_SHA,D
from scripts.inventory_shibuki_ui import sheet
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_ui import native,WORDS,static_repack
from scripts.prepare_riko_illustrations import repack_one_bank
from scripts.discover_inputs import psx_arc,sha256
from scripts.project import digest
from scripts.extract_zero import save_image
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels
from src.psx_static_effect import compose_static,patch_static
from src.psx_shibuki_text import char,code
from src.psx_text import message_ranges

DEATH_LUT=bytes([0,5,14,8,2,9,5,14,8,2,15,14,8,2,15,15])
ULTIMATE_DEATH_LUT=bytes([0,5,6,7,11,8,5,6,7,11,7,6,7,11,8,11])

def rename_gangzi(data):
    result=[];changes=[]
    for number,(start,end) in enumerate(message_ranges(data)):
        words=list(struct.unpack('<'+'H'*((end-start)//2),data[start:end]));out=[];i=0
        while i<len(words):
            if ''.join(map(char,words[i:i+9]))=='DR\ue086 LIGHT':
                old=words[i:i+9];new='Pres\ue086 GangZi'
                out.extend((old[0]&~(511|0xe000))|code(ch)|((old[-1]&0xe000) if j==len(new)-1 else 0) for j,ch in enumerate(new))
                changes.append({'message':number,'word_offset':i,'from':'DR. LIGHT','to':'Pres. GangZi'});i+=9
            else:out.append(words[i]);i+=1
        if [w&0xa000 for w in out if w&0xa000]!=[w&0xa000 for w in words if w&0xa000]:raise ValueError('GangZi page flags changed')
        width=0
        for w in out:
            width+=1
            if w&0xe000:
                if width>20:raise ValueError('GangZi text overflow')
                width=0
        result.append(struct.pack('<'+'H'*len(out),*out))
    cursor=len(result)*2;offsets=[]
    for raw in result:offsets.append(cursor);cursor+=len(raw)
    if cursor>=65536:raise ValueError('Text offset overflow')
    return struct.pack('<'+'H'*len(offsets),*offsets)+b''.join(result),changes

def last_text(arc,data):
    es=psx_arc(arc);e=es[-1]
    if e['type']!='0x15' or (len(data)+2047)//2048!=(e['size']+2047)//2048:raise ValueError('Text does not fit existing final slot')
    out=bytearray(arc);struct.pack_into('<I',out,12+8*e['index'],len(data));out[e['offset']:e['offset']+len(data)]=data
    if len(out)!=len(arc) or any(a['offset']!=b['offset'] for a,b in zip(es,psx_arc(out))):raise ValueError('Text relocation refused')
    return bytes(out)

def tint_palette(data,kind):
    out=bytearray(data);touched=[]
    slots={0:[15],1:list(range(8,15)),2:list(range(6,15)),3:list(range(11,16)),4:list(range(8,16)),5:list(range(8,16)),11:list(range(1,16))}
    for row,indices in slots.items():
        for i in indices:
            pos=row*32+i*2;w=struct.unpack_from('<H',data,pos)[0];r,g,b=(w>>s&31 for s in (0,5,10))
            # Keep highlight luminance and metal neutrals, tint only accent ramps.
            hi=max(r,g,b);lo=min(r,g,b)
            if kind=='violet':rgb=(round(lo+(hi-lo)*.64),round(lo+(hi-lo)*.28),hi)
            else:rgb=(round(lo+(hi-lo)*.25),hi,round(lo+(hi-lo)*.83))
            new=(w&0x8000)|sum(v<<(j*5) for j,v in enumerate(rgb));struct.pack_into('<H',out,pos,new);touched.append([row,i])
    return bytes(out),touched

def pause_background(arc):
    g=entry(arc,0x10007);mp=struct.unpack('<768H',entry(arc,0x10));pal=entry(arc,0x11);canvas=Image.new('RGBA',(320,240))
    for n,v in enumerate(mp[:512]):
        x=n//256*256+n%16*16;y=n%256//16*16
        if x>=320 or y>=240:continue
        colors=struct.unpack_from('<16H',pal,(v>>12)*32);px=tile_pixels(g,v&255);im=Image.new('RGBA',(16,16));im.putdata([tuple((colors[k]>>s&31)*255//31 for s in (0,5,10))+(255,) for k in px]);canvas.paste(im,(x,y))
    return canvas

def fit_frames(texture,parts,bank,frames,groups):
    """Preserve the proven cover; contract it only when contracting a raster."""
    out=bytearray(parts);targets={};report=[];demands={}
    for n,(a,(bx,by)) in frames.items():
        c=aliased_composition(parts,bank,n);_,old_size,bb,_=compose_static(texture,local_composition(c))
        h,w=a.shape
        if w>old_size[0] or h>old_size[1]:raise ValueError('Cover expansion is not supported')
        covered=np.zeros_like(a,dtype=bool)
        for q in c['parts']:
            x=min(w-16,(q['x']-bb[0])*w//old_size[0]);y=min(h-16,(q['y']-bb[1])*h//old_size[1])
            covered[y:y+16,x:x+16]=True
            if not -128<=bx+x<=127 or not -128<=by+y<=127:raise ValueError('Frame coordinate overflow')
            off=q['record_offset'];value=bytes(((bx+x)&255,(by+y)&255))
            if off in demands and demands[off]!=value:raise ValueError('Conflicting frame registration alias')
            demands[off]=value;out[off+2:off+4]=value
        if np.any((a>0)&~covered):raise ValueError(f'Frame {n} contracts outside part coverage')
        targets[n]=(a.tobytes(),(w,h));report.append({'frame':n,'bounds':[bx,by,bx+w,by+h],'parts':len(c['parts'])})
    g,p,packed=repack_one_bank(texture,bytes(out),bank,targets,{n:0 for n in targets})
    return g,p,{'registration':report,'packing':packed}

def prepare(output,death_approved=False):
    output.mkdir(exist_ok=False);records,original,current=load();changes={};checks={};previews=[]
    get=lambda n:changes.get(n,current[n])
    def show(a,pal,name):
        im=save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,output/(name+'.png')).convert('RGBA');previews.append((name,im));return im
    # Native menu palette rows are private to each player archive.
    for name,kind in [('PL00_U.ARC','violet'),('PL02_U.ARC','violet'),('PL01_U.ARC','mint')]:
        raw=get(name);p,slots=tint_palette(entry(raw,0x11),kind);raw=replace_entry(raw,0x11,p);checks[name+'_menu_palette']=slots
        if name!='PL01_U.ARC':
            g=entry(raw,0x10007);p=struct.pack('<I',4)+entry(raw,0x12);c=local_composition(aliased_composition(p,0,10));_,sz,_,cov=compose_static(g[96*128:],c)
            source=ROOT/'work/ver_buki_riko/shibuki_ui_v1/dialogue_generated.png';w,h=Image.open(source).size
            a=native(source,sz,(58,74),(3,3),crop=(round(w*.18),0,round(w*.84),h));a[~np.array([bool(v) for v in cov]).reshape(a.shape)]=0
            show(a,WORDS,name+'_pause_portrait');ng=patch_static(g[96*128:],{10:c},{10:(a.tobytes(),sz)});raw=replace_entry(raw,0x10007,g[:96*128]+ng)
            checks[name+'_portrait_bbox']=Image.fromarray(a).getbbox()
        changes[name]=raw;pause_background(raw).save(output/(name+'_menu.png'))
    # HUD: a compact fox badge; all max-HP frames share one world-space origin.
    mark=Image.open(ROOT/'character/ver_buki_riko/buki(zero)_mark.webp').convert('RGBA').getchannel('A').resize((11,8),Image.Resampling.BOX);alpha=np.array(mark)
    for name in ['PL00_U.ARC','PL02_U.ARC']:
        raw=get(name);g=entry(raw,0x10206);p=entry(raw,3);targets={};cluts={}
        for n in range(69,78):
            px,sz,bb,_=compose_static(g,local_composition(aliased_composition(p,1,n)));a=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]).copy();y=26-bb[1];x=-18-bb[0];a[y:y+15,x-1:x+22]=0
            badge=Image.new('L',(15,12));draw=ImageDraw.Draw(badge);draw.polygon([(2,0),(12,0),(14,2),(14,9),(12,11),(2,11),(0,9),(0,2)],fill=14,outline=12)
            bx=-15-bb[0];by=27-bb[1];a[by:by+12,bx:bx+15]=np.array(badge);region=a[by+2:by+10,bx+2:bx+13];region[alpha>=90]=10;region[(alpha>=40)&(alpha<90)]=11;targets[1,n]=a
            if n in [69,77]:show(a,struct.unpack('<16H',(ROOT/'work/ver_buki_riko/art_pilot/hud_mark_v1/hud_palette.bin').read_bytes()),name+f'_hud_{n}')
        if death_approved:
            death_lut=DEATH_LUT if name=='PL00_U.ARC' else ULTIMATE_DEATH_LUT
            for n in range(105,114):
                px,sz,_,_=compose_static(entry(original[name],0x10206),local_composition(aliased_composition(entry(original[name],3),1,n)));a=np.frombuffer(bytes(death_lut[v] for v in px),np.uint8).reshape(sz[1],sz[0]);targets[1,n]=a;cluts[1,n]=0
                if n in [105,110]:show(a,struct.unpack_from('<16H',entry(raw,9)),name+f'_death_{n}')
        ng,np_,checks[name+'_static']=static_repack(g,p,targets,cluts);changes[name]=replace_entry(replace_entry(raw,0x10206,ng),3,np_)
    if death_approved:
        # Shared EXE CLUT moves down two rows; Riko offset moves up two rows.
        raw=get('PL01_U.ARC');p=bytearray(entry(raw,3));offsets=set()
        for n in range(105,114):
            for q in aliased_composition(p,1,n)['parts']:
                off=q['record_offset']
                if off not in offsets:
                    if q['clut']!=1:raise ValueError('Unexpected Riko orb CLUT')
                    p[off]=(p[off]&~12)|12;offsets.add(off)
        changes['PL01_U.ARC']=replace_entry(raw,3,bytes(p));checks['riko_death_clut']={'old_final':'0x7803','new_final':'0x7803','changed_records':len(offsets)}
    # X stage-local afterimages, exact original-ramp signature protects other rows.
    oldtrail=entry(original['COL00_0X.ARC'],5)[13*32:16*32];trail=b''.join(struct.pack('<16H',0,*([0x8000|r|(g<<5)|(b<<10)]*15)) for r,g,b in [(15,8,24),(10,5,18),(6,3,12)])
    copies=[]
    for name in original:
        if not (name.startswith('COL') and name.endswith('X.ARC')):continue
        raw=get(name);p=entry(raw,5)
        if p[13*32:16*32]==oldtrail:
            changes[name]=replace_entry(raw,5,p[:13*32]+trail+p[16*32:]);copies.append(name)
    if len(copies)!=24:raise ValueError(f'Unexpected trail copy count {len(copies)}')
    checks['violet_trail_stage_copies']=copies
    # HQ: preserve idle; register ground poses by actual soles, crouch by body scale.
    name='ST0D_0X.ARC';raw=get(name);g=entry(raw,0x10102);p=entry(raw,10);frames={};details=[]
    for n in range(12):
        px,sz,bb,_=compose_static(g[63488:75776],local_composition(aliased_composition(p,2,n)));a=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]).copy();bx,by=bb[:2]
        if n==0:
            yy,xx=np.nonzero(a[-9:]);sole_center=bx+(int(xx.min())+int(xx.max()))/2
        if n in [6,7,8]:a=np.array(Image.fromarray(a).resize((69,81),Image.Resampling.NEAREST));by=49-a.shape[0]
        if n in [3,4,5,6,7,8,10]:
            yy,xx=np.nonzero(a[-9:]);bx=round(sole_center-(int(xx.min())+int(xx.max()))/2)
        frames[n]=(a,(bx,by));details.append({'frame':n,'old_bounds':bb,'new_origin':[bx,by],'size':[a.shape[1],a.shape[0]]})
    ng,np_,report=fit_frames(g[63488:75776],p,2,frames,[[0,1,2,11],[3,4,5],[6,7,8],[9],[10]])
    changes[name]=replace_entry(replace_entry(raw,0x10102,g[:63488]+ng+g[75776:]),10,np_);checks['hq']={'frames':details,**report}
    hq=[];pal=struct.unpack_from('<16H',entry(get('COL0D_0X.ARC'),5),35*32)
    for n,(a,(bx,by)) in frames.items():
        im=show(a,pal,f'hq_{n:02}');canvas=Image.new('RGBA',(160,160));canvas.alpha_composite(im,(80+bx,100+by));hq.append((str(n),canvas))
    sheet(hq,output/'hq_registration.png',6,(180,190))
    # Header name growth fits the text padding already reserved by the approved build.
    for name in ['PL00_U.ARC','PL02_U.ARC']:
        raw=get(name);text,renames=rename_gangzi(entry(raw,0x15));changes[name]=last_text(raw,text);checks[name+'_gangzi_name']={'count':len(renames),'changes':renames,'growth':len(text)-len(entry(raw,0x15))}
    from scripts.prepare_gangzi_capsule import patch_capsules
    checks['gangzi']=patch_capsules(current,changes,output)
    files=[]
    for name,data in sorted(changes.items()):
        if len(data)!=len(current[name]):raise ValueError('Archive resize')
        if data==current[name]:continue
        (output/name).write_bytes(data);files.append({'file':name,'source':records[name],'parent_sha256':sha256(current[name]),'sha256':sha256(data)})
    recipe={'kind':'ui_revision_v2','parent_build':str(PARENT.relative_to(ROOT)),'parent_bin_sha256':PARENT_SHA,'files':files,'checks':checks,'death_exe_patch_required':death_approved,'runtime_verified':False,'gangzi_art_pending':False}
    (output/'recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf8');sheet(previews,output/'review.png',6,(180,140));print(json.dumps({'output':str(output),'files':len(files),'death_exe_patch_required':death_approved}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--death-approved',action='store_true');a=p.parse_args();prepare(a.output.resolve(),a.death_approved)
