"""Pause-only native portrait variants. Fixed ARC sizes, no gameplay edits."""
from pathlib import Path
import json, struct, sys, hashlib
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
H = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.prepare_riko_ui import entry, replace_entry
from scripts.discover_inputs import psx_arc
from src.psx_static_effect import compose_static, patch_static
from src.psx_ui_atlas import aliased_composition, local_composition, tile_pixels, write_tile
from src.psx_ui_render import render_static_rgba
from src.psx_korean_font import Assembly

MODES = ('ver_rin_nana', 'ver_buki_riko')
HOOK, RESUME = 0x80017660, 0x8001769c
BANK, CODE = 1024, 1536
def off(a): return a - 0x80010000 + 2048
def sha(b): return hashlib.sha256(b).hexdigest()
def save_json(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', 'utf8')

def selector():
    a=Assembly(); i=a.imm; b=a.branch; r=a.reg; s=a.shift
    # Entry preserves original a0/id, a2/layout, a3/parts, v0/header offset.
    r(0x21,'a1','a3','v0'); i(12,'v1','a0',255); i(9,'t0','zero',30)
    b(4,'v1','t0','portrait'); i(9,'t0','zero',38)
    b(5,'v1','t0','done'); a.nop()
    # Native optional menu item 38: add ten frames when its flag is active.
    i(15,'t0','zero',0x8017); i(36,'t0','t0',0x54c5); a.nop()
    b(4,'t0','zero','done'); a.nop()
    i(36,'v0','a2',4); a.nop(); s(0,'v0','v0',2); i(9,'v0','v0',40)
    r(0x21,'a1','a3','v0'); b(4,'zero','zero','done'); a.nop()
    a.label('portrait')
    i(15,'t0','zero',0x8017); i(36,'v0','t0',0x2207)
    i(36,'t1','t0',0x2203); i(36,'t0','t0',0x21f7)
    b(5,'t1','zero','zero_char'); i(12,'v1','v0',3)
    b(4,'t0','zero','pick'); a.nop()
    r(0x2b,'v1','zero','v0'); b(4,'zero','zero','pick'); i(9,'v1','v1',4)
    a.label('zero_char'); r(0x2b,'v1','zero','t0')
    a.label('pick'); i(15,'a3','zero',0x1f80); i(35,'a3','a3',0x38)
    s(0,'v1','v1',2); i(9,'a3','a3',BANK); r(0x21,'a1','a3','v1')
    # A MIPS J preserves the current high nibble; explicitly return from KSEG1.
    a.label('done'); i(15,'t0','zero',RESUME>>16); i(13,'t0','t0',RESUME&65535)
    r(8,'zero','t0','zero'); a.nop()
    code=a.finish(); assert len(code)<=512
    return code

def hook():
    a=Assembly(); i=a.imm
    # RAM resource changes between characters; execute through KSEG1.
    i(15,'t0','zero',0x1f80); i(35,'t0','t0',0x38)
    i(15,'t1','zero',0xa000); i(9,'t0','t0',CODE)
    a.reg(0x25,'t0','t0','t1'); a.reg(8,'zero','t0','zero'); a.nop()
    return a.finish()

def palette_image(a, words):
    colors=np.array([[*(int(w>>s&31)*255//31 for s in (0,5,10)),255 if n else 0]
                     for n,w in enumerate(words)],np.uint8)
    return Image.fromarray(colors[a], 'RGBA')

def source_x(mode, n):
    folder=ROOT/('work/nana_dialogue_hair_20261108/native_v2' if mode==MODES[0]
                 else 'work/armor_dialogue_20261108/ver_buki_riko/native_proposal')
    im=Image.open(folder/f'{n:02}.png')
    assert im.mode=='P' and im.size==(112,96)
    # Existing indexed game artwork, not a new illustration or a generated redraw.
    return im, folder/f'{n:02}.png'

def x_target(mode,n,mask):
    im,src=source_x(mode,n)
    a=np.array(im.resize((84,72),Image.Resampling.NEAREST).crop((16,-2,80,78)))
    a[~mask]=0; a[mask&(a==0)]=1
    rgb=im.getpalette()
    words=[0]+[(rgb[k*3]>>3)|(rgb[k*3+1]>>3)<<5|(rgb[k*3+2]>>3)<<10|0x8000 for k in range(1,16)]
    return a,words,{'path':src.relative_to(ROOT).as_posix(),'sha256':sha(src.read_bytes()),
                    'native_source_size':[112,96],'registration_size':[84,72],'crop':[16,-2,80,78]}

def zero_target(mode,old,mask):
    p=struct.pack('<I',4)+entry(old,18);c=aliased_composition(p,0,10)
    normal=list(struct.unpack_from('<16H',entry(old,17),320))
    if mode==MODES[0]:
        pixels,_,_,_=compose_static(entry(old,0x10007)[12288:],local_composition(c))
        a=np.frombuffer(pixels,np.uint8).reshape(80,64).copy(); black=list(normal)
        for idx,(r,g,b) in {2:(8,3,5),3:(13,4,7),7:(22,2,5),8:(30,4,7),9:(31,12,14)}.items():
            black[idx]=0x8000|r|g<<5|b<<10
        return a,normal,black,{'normal_pause_preserved':True}
    d=ROOT/'work/illustration_variants_20261108/ver_buki_riko/regions_v2'
    g=(d/'dialogue_texture.bin').read_bytes();p=struct.pack('<I',4)+(d/'dialogue_parts.bin').read_bytes()
    pixels,size,_,_=compose_static(g,local_composition(aliased_composition(p,0,1)))
    im=Image.frombytes('L',size,pixels)
    a=np.array(im.resize((84,72),Image.Resampling.NEAREST).crop((16,-2,80,78)))
    a[~mask]=0; a[mask&(a==0)]=1
    report=json.loads((d/'report.json').read_text('utf8'))
    return a,report['normal_palette'],report['black_palette'],{'source':d.relative_to(ROOT).as_posix(),
        'native_source_size':size,'registration_size':[84,72],'crop':[16,-2,80,78],
        'normal_black_share_pixels':True}

def prepare(mode):
    d=H/mode; out=d/'prepared';out.mkdir(exist_ok=True)
    base=(H/MODES[0]/'originals/PL00_U.ARC').read_bytes()
    c=aliased_composition(struct.pack('<I',4)+entry(base,18),0,10)
    pixels,size,bounds,_=compose_static(entry(base,0x10007)[12288:],local_composition(c))
    mask=np.frombuffer(pixels,np.uint8).reshape(80,64)>0
    assert mask.sum()==3388
    reports=[];board=Image.new('RGB',(8*260,380),(32,40,55));draw=ImageDraw.Draw(board);col=0
    for name in ['PL00_U.ARC','PL02_U.ARC','PL01_U.ARC']:
        old=(d/'originals'/name).read_bytes();oldg=entry(old,0x10007)
        oldpal=entry(old,17);oldparts=struct.pack('<I',4)+entry(old,18)
        c=aliased_composition(oldparts,0,10)
        assert len(oldg)==32768 and len(oldpal)==2048 and not any(oldpal[1024:])
        assert all(q['flags']==0 for q in c['parts'])
        if name=='PL01_U.ARC':
            a,normal,black,source=zero_target(mode,old,mask)
            targets={0:(a,0),1:(a,1)};sources=[source];palettes=[normal,black]
            ids=[0,1,0,0,0,1]
        else:
            frame_ids=[0,1,2,3] if name=='PL00_U.ARC' else [8,9]
            targets={};sources=[];palettes=[]
            for k,n in enumerate(frame_ids):
                a,normal,source=x_target(mode,n,mask);targets[k]=(a,0);sources.append(source)
                if not palettes:palettes=[normal]
                assert normal==palettes[0]
            ids=[0,1,2,3,0,0] if name=='PL00_U.ARC' else [0,0,0,0,0,1]
        # Original portrait slots + unreferenced final two texture rows. No UI relocation.
        owned={96+q['tile'] for q in c['parts']};free=sorted(owned|set(range(224,256)))
        all_tiles={96+q['tile']for f in range(38)if f!=10 for q in aliased_composition(oldparts,0,f)['parts']}
        assert not (set(free)&all_tiles)
        assert all((v&255) not in free for v in struct.unpack('<768H',entry(old,16))[:512])
        g=bytearray(oldg);assigned={};records={};bank=bytearray(24);bank_offsets={}
        for k,(a,clut) in targets.items():
            assert np.array_equal(a>0,mask)
            parts=bytearray()
            for q in c['parts']:
                x=q['x']-bounds[0];y=q['y']-bounds[1];pattern=a[y:y+16,x:x+16].tobytes()
                if pattern not in assigned:
                    assert free,('Atlas full',mode,name,len(assigned))
                    tile=free.pop(0);assigned[pattern]=tile;write_tile(g,tile,pattern)
                tile=assigned[pattern];assert 96<=tile<256
                parts+=struct.pack('<BBbb',clut<<2,tile-96,q['x'],q['y'])
            bank_offsets[k]=len(bank)//4;bank+=parts;records[k]=bytes(parts)
        for k,idx in enumerate(ids):struct.pack_into('<HH',bank,k*4,19,bank_offsets[idx])
        assert len(bank)<=512
        pal=bytearray(oldpal);pal[320:352]=struct.pack('<16H',*palettes[0])
        if len(palettes)>1:pal[352:384]=struct.pack('<16H',*palettes[1])
        pal[BANK:BANK+len(bank)]=bank;pal[CODE:CODE+len(selector())]=selector()
        # Frame10 remains the default portrait for old/static callers too.
        pp=bytearray(entry(old,18))
        for j,q in enumerate(c['parts']):pp[q['record_offset']-4:q['record_offset']]=records[0][j*4:j*4+4]
        new=replace_entry(replace_entry(replace_entry(old,0x10007,g),17,pal),18,pp)
        assert len(new)==len(old)
        assert [(e['type'],e['offset'],e['size'])for e in psx_arc(old)]==[(e['type'],e['offset'],e['size'])for e in psx_arc(new)]
        for e in psx_arc(old):
            if int(e['type'],16) not in (0x10007,17,18):assert entry(old,int(e['type'],16))==entry(new,int(e['type'],16))
        for t in range(256):
            if t not in owned|set(assigned.values()):assert tile_pixels(g,t)==tile_pixels(oldg,t)
        for f in range(38):
            if f!=10:
                before=aliased_composition(oldparts,0,f);after=aliased_composition(struct.pack('<I',4)+pp,0,f)
                assert before==after
                assert compose_static(oldg[12288:],before)[:3]==compose_static(g[12288:],after)[:3]
        frames=[]
        for k,idx in enumerate(ids):
            nc=aliased_composition(struct.pack('<I',4)+bytes(bank),0,k)
            got,sz,bb,_=compose_static(g[12288:],local_composition(nc))
            assert (got,sz,bb)==(targets[idx][0].tobytes(),(64,80),bounds)
            assert [(q['x'],q['y'])for q in nc['parts']]==[(q['x'],q['y'])for q in c['parts']]
            im,_=render_static_rgba(g[12288:],nc,{i:v for i,v in enumerate(palettes)})
            path=out/f'{name[:4]}_{k}.png';im.save(path)
            frames.append({'index':k,'target':idx,'rgba_sha256':sha(im.tobytes()),'opaque_pixels':3388})
        for k in range(len(targets)):
            im=palette_image(targets[k][0],palettes[targets[k][1]])
            im.save(out/f'{name[:4]}_unique_{k}.png')
            large=im.resize((256,320),Image.Resampling.NEAREST);board.paste(large,(col*260,40),large)
            draw.text((col*260+4,10),f'{name[:4]} {k}',fill='white');col+=1
        (out/name).write_bytes(new)
        reports.append({'file':name,'before':sha(old),'after':sha(new),'frames':frames,'sources':sources,
            'unique_portrait_tiles':len(assigned),'atlas_capacity':51,'bank_bytes':len(bank),
            'mask_pixels':3388,'bounds':bounds,'non_portrait_frames_preserved':37,
            'non_ui_entries_exact':True,'geometry_and_menu_origin_unchanged':True,
            'normal_palette':palettes[0],'black_palette':palettes[1] if len(palettes)>1 else None})
    board.save(out/'review.png')
    oldexe=(d/'originals/SLUS_005.61').read_bytes();newexe=bytearray(oldexe)
    newexe[off(HOOK):off(HOOK)+len(hook())]=hook()
    (out/'SLUS_005.61').write_bytes(newexe)
    save_json(out/'verification.json',{'mode':mode,'arcs':reports,'selector_bytes':len(selector()),
        'exe_hook':[hex(HOOK),hex(HOOK+len(hook()))],'exe_before':sha(oldexe),'exe_after':sha(newexe),
        'native_palette_upload_bytes':1024,'payload_start':BANK,'no_arc_or_ram_growth':True,
        'native_palette_row11_unused_by_other_widgets':True,'runtime_verified':False})
    print(mode,[(q['file'],q['unique_portrait_tiles'],q['bank_bytes'])for q in reports])

if __name__=='__main__':
    for mode in MODES:prepare(mode)
