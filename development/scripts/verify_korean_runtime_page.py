"""Independently verify a captured native dialogue page; no emulator access."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(value,reason):
    if not value:
        raise ValueError(reason)


def texture_tile(vram,tile):
    x=960+(tile%16)*4
    y=256+(tile//16)*16
    return b''.join(vram[(y+row)*2048+x*2:(y+row)*2048+x*2+8] for row in range(16))


def archive_font_tile(font,tile):
    x=(tile%16)*8
    y=(tile//16)*16
    return b''.join(font[(y+row)*128+x:(y+row)*128+x+8] for row in range(16))


def expand_bitmap(bits):
    # Independent slow reference: exactly 144 source bits, 12 per row;
    # palette14 in a 16x16 tile, with a two-pixel top margin.
    pixels=[0]*256
    for bit in range(144):
        if bits[bit//8]&(1<<(bit%8)):
            row,col=divmod(bit,12)
            pixels[(row+2)*16+col]=14
    return bytes(pixels[i]|pixels[i+1]<<4 for i in range(0,256,2))


def native_draw_buffers(ram):
    """Read US DrawInfo structs, not guessed texture-page/framebuffer offsets.

    symbols.us.txt: draw_infos=0x80166C10, second struct=0x80166CB0.
    obj.h: DISPENV at +0, DRAWENV at +0x14; the latter begins with
    RECT clip and two s16 drawing offsets. 2824.c initializes y0/y240.
    """
    result=[]
    for address in (0x166c10,0x166cb0):
        display=struct.unpack_from('<4h',ram,address)
        clip=struct.unpack_from('<4h',ram,address+20)
        offset=struct.unpack_from('<2h',ram,address+28)
        x,y,w,h=clip
        require(w==320 and h==240 and 0<=x<=704 and 0<=y<=272,'Unexpected native framebuffer geometry')
        require(display[2:]==(320,240),'Unexpected native display geometry')
        result.append({'struct_address':hex(address|0x80000000),
                       'draw_clip':list(clip),'draw_offset':list(offset),'display_rect':list(display)})
    require(result[0]['draw_clip']!=result[1]['draw_clip'],'Native double buffers overlap exactly')
    return result


def verify(capture,candidate,archive,message,page):
    evidence=json.loads((capture/'evidence.json').read_text('utf-8'))
    require(len(evidence['ram_bases'])==len(evidence['vram_bases'])==1,'Capture RAM/VRAM must be unique')
    ram=(capture/f"ram_{evidence['ram_bases'][0]}.bin").read_bytes()
    vram=(capture/f"vram_{evidence['vram_bases'][0]}.bin").read_bytes()
    require(len(ram)==0x200000 and len(vram)==0x100000,'Invalid native memory size')
    session=json.loads((ROOT/evidence['session']/'session.local.json').read_text('utf-8'))
    require(session['bin_sha256']==evidence['bin_sha256'],'Session/capture build mismatch')
    build=Path(session['cue']).parent
    proposal=json.loads((candidate/'proposal.json').read_text('utf-8'))
    text=entry((candidate/archive).read_bytes(),0x15)
    require(text==entry((build/archive).read_bytes(),0x15),'Candidate/build dialogue differs')
    base=ram.find(text)
    require(base>=0 and ram.find(text,base+1)<0,'Complete RAM dialogue resource must match uniquely')
    require(base%4==len(text)%4==0,'Native RAM dialogue is not word-aligned')
    meta=proposal['dialogue'][archive]
    expected_page=next(p for p in meta['pages'] if p['message']==message and p['page']==page)
    inverse={int(code):char for code,char in ((256+i,c) for i,c in enumerate(meta['glyphs']))}
    # Native US glyph IDs, without importing the generator's encoder.
    for i,c in enumerate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'):
        inverse[64+i]=c
    inverse.update({128:'↑',129:'←',130:'→',131:'+',132:'-',133:',',134:'.',135:'!',136:'?',137:'“',138:'”',139:"'",140:'·',141:'…',2047:' '})
    pos=struct.unpack_from('<H',text,message*2)[0]
    pages=[]
    for _ in range(page+1):
        words=[]
        while True:
            word=struct.unpack_from('<H',text,pos)[0]
            pos+=2
            words.append(word)
            if word&0xa000:
                break
        pages.append(words)
    lines=[];line='';records=[];x=-120;y=29
    for word in pages[-1]:
        code=word&0x7ff
        require(code in inverse,'Unknown dialogue character')
        char=inverse[code]
        line+=char
        if code!=2047:
            tile=192+len(records) if code>=256 else code
            records.append({'char':char,'code':code,'tile':tile,'x':x&255,'y':y&255})
        if word&0x4000:
            lines.append(line);line='';x=-120;y+=18
        else:
            x+=12
        if word&0xa000:
            lines.append(line)
    require(lines==expected_page['lines'],'Independent page text differs')
    count=struct.unpack_from('<H',ram,0x1397e0)[0]
    require(count==len(records),'Visible glyph count differs')
    require(struct.unpack_from('<HH',ram,0x1396c8)==(count,1),'Native glyph batch count/active differs')
    require((struct.unpack_from('<I',ram,0x13bc28)[0]&0x1fffffff)==base+pos,'AbcObj pointer is not at requested page end')
    font=entry((build/'LOAD_U.ARC').read_bytes(),0x10001)
    for index,record in enumerate(records):
        actual=tuple(ram[0x1396cc+index*4:0x1396cc+index*4+4])
        require(actual==(0,record['tile'],record['x'],record['y']),f'Glyph record differs at {index}')
        if record['code']>=256:
            start=meta['font_offset']+(record['code']-256)*18
            expected=expand_bitmap(text[start:start+18])
        else:
            expected=archive_font_tile(font,record['tile'])
        actual_bitmap=texture_tile(vram,record['tile'])
        require(expected==actual_bitmap,f'GPU tile differs at {index}: {record["char"]}')
        record['bitmap_sha256']=digest(actual_bitmap)
        record['bitmap_equal']=True
    obj=struct.unpack_from('<I',ram,0x1397c0)[0]&0x1fffffff
    require(obj>0 and obj+0x44<len(ram),'Invalid native dialogue object')
    require(ram[obj:obj+2]==b'\x01\x16','Inactive/wrong native dialogue object')
    require(struct.unpack_from('<I',ram,obj+0x3c)[0]==0x801396c8,'Dialogue object uses a different glyph batch')
    tpage,clut=struct.unpack_from('<HH',ram,obj+0x40)
    stage=ram[0x1721cc]
    require(tpage==0x1f00 and clut==(0x78ce if stage==13 else 0x7845),'Unexpected native font texture/CLUT')
    palette_x=(clut&63)*16;palette_y=clut>>6
    palette=struct.unpack_from('<16H',vram,palette_y*2048+palette_x*2)
    require(palette[0]==0 and palette[14]&0x7fff==0x7fff,'Font transparency/white ink differs')
    origin_x,origin_y=(struct.unpack_from('<i',ram,obj+a)[0]>>16 for a in (8,12))
    framebuffer_checks=[]
    for buffer in native_draw_buffers(ram):
        frame_x,frame_y,frame_w,frame_h=buffer['draw_clip']
        offset_x,offset_y=buffer['draw_offset']
        matching=total=0
        for record in records:
            tile=texture_tile(vram,record['tile'])
            rx=record['x']-256 if record['x']>127 else record['x']
            ry=record['y']-256 if record['y']>127 else record['y']
            for py in range(16):
                for px in range(16):
                    ink=tile[py*8+px//2]>>((px%2)*4)&15
                    if ink!=14:
                        continue
                    xx=offset_x+origin_x+rx+px;yy=offset_y+origin_y+ry+py
                    require(frame_x<=xx<frame_x+frame_w and frame_y<=yy<frame_y+frame_h,'Glyph leaves native framebuffer')
                    total+=1
                    actual=struct.unpack_from('<H',vram,(yy*1024+xx)*2)[0]
                    matching+=(actual&0x7fff)==(palette[14]&0x7fff)
        framebuffer_checks.append({'page_x':frame_x,'page_y':frame_y,'draw_info':buffer,'matching_white_pixels':matching,'white_pixels':total,'all_white_pixels_match':total>0 and matching==total})
    require(any(c['all_white_pixels_match'] for c in framebuffer_checks),'Font cache exists but corresponding framebuffer text does not match')
    exe=(candidate/'SLUS_005.61').read_bytes()
    anchors=[(0x232a8,4),(0x232b0,4),(0x233c8,56),(0x23400,80),(0xea20c,108),(0xea4d0,100)]
    for address,length in anchors:
        require(ram[address:address+length]==exe[address-0x10000+2048:address-0x10000+2048+length],f'Runtime EXE code differs at {address:x}')
    korean=[r for r in records if r['code']>=256]
    return {
        'kind':'captured_native_korean_page_verification',
        'capture':str(capture),'bin_sha256':evidence['bin_sha256'],
        'ram_sha256':digest(ram),'vram_sha256':digest(vram),
        'archive':archive,'message':message,'page':page,'lines':lines,
        'dialogue_resource_ram_address':hex(base|0x80000000),'dialogue_resource_sha256':digest(text),
        'visible_glyphs':count,'korean_tiles_compared':len(korean),
        'legacy_tiles_compared':count-len(korean),'records':records,
        'active_cache_tiles':[r['tile'] for r in korean],
        'font_object':{'address':hex(obj|0x80000000),'stage':stage,'texture':hex(tpage),'clut':hex(clut),
                       'clut_x':palette_x,'clut_y':palette_y,'palette':[hex(v) for v in palette]},
        'framebuffer_white_ink_checks':framebuffer_checks,
        'runtime_exe_anchors_equal':[hex(a|0x80000000) for a,_ in anchors],
        'captured_page_verified':True,'full_game_verified':False,
        'scope':'Captured completed page: records, coordinates, active font bitmaps, native font object, actual framebuffer white ink and EXE anchors. Unused cache tiles and other pages are not claimed.',
        'emulator_accessed':False,'process_memory_written':False,'keys_sent':False,
    }


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--archive',required=True)
    p.add_argument('--message',type=int,required=True)
    p.add_argument('--page',type=int,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    result=verify(a.capture,a.candidate,a.archive,a.message,a.page)
    with a.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','font_object')},ensure_ascii=False))
