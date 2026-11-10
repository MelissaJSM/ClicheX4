"""Korean dialogue payload with original message IDs/page controls retained."""
import struct
from PIL import Image,ImageDraw,ImageFont
from src.psx_text import ALPHABET,message_ranges
from src.psx_korean_font import emit_cache_code

LEGACY={c:i+64 for i,c in enumerate(ALPHABET)}
LEGACY.update({'↑':128,'←':129,'→':130,'+':131,'-':132,',':133,'.':134,'!':135,'?':136,'“':137,'”':138,"'":139,'·':140,'…':141,' ':2047})
FONT_PATH='C:/Windows/Fonts/gulim.ttc'

def glyph_bitmap(char):
    font=ImageFont.truetype(FONT_PATH,12)
    im=Image.new('1',(12,12));d=ImageDraw.Draw(im)
    box=font.getbbox(char);d.text((0,-box[1]),char,font=font,fill=1)
    if not im.getbbox():raise ValueError(f'Empty glyph {char!r}')
    return sum(bool(v)<<i for i,v in enumerate(im.getdata())).to_bytes(18,'little')

def build_dialogue(source,messages,translations,*,immediate_headers=None):
    """translations: message ID -> same number of pages, each 1..3 lines.

    Preserve each page's side flag, typewriter flag and original page/end flag.
    Untranslated messages keep words byte-exact except the new space code.
    Caller must explicitly report untranslated pages; this also supports pilots.
    """
    if len(messages)>64:raise ValueError('Message directory exceeds reserved header')
    immediate_headers=set() if immediate_headers is None else set(immediate_headers)
    known_pages={(m['id'],pi) for m in messages for pi in range(len(m['pages']))}
    if immediate_headers-known_pages:raise ValueError('Unknown immediate speaker page')
    chars=sorted({c for pages in translations.values() for lines in pages for line in lines for c in line if c not in LEGACY})
    if len(chars)>1791:raise ValueError('Font dictionary exceeds 11-bit IDs')
    codes={**LEGACY,**{c:256+i for i,c in enumerate(chars)}}
    old_ranges=message_ranges(source);out=bytearray(144);changes=[]
    for message,(lo,hi) in zip(messages,old_ranges):
        mi=message['id'];struct.pack_into('<H',out,mi*2,len(out))
        if mi not in translations:
            words=struct.unpack('<'+'H'*((hi-lo)//2),source[lo:hi])
            out+=struct.pack('<'+'H'*len(words),*(w|0x600 if w&511==511 else w for w in words));continue
        pages=translations[mi]
        if len(pages)!=len(message['pages']):raise ValueError(f'Message {mi}: page count changed')
        for pi,(lines,oldpage) in enumerate(zip(pages,message['pages'])):
            if not 1<=len(lines)<=3 or any(not line or len(line)>20 for line in lines):raise ValueError(f'Page {mi}/{pi}: line limit {lines}')
            words=[w for line in oldpage['lines'] for w in line['words']]
            side={w&0x800 for w in words}
            if len(side)!=1:raise ValueError('Mixed page side flags')
            # Page-final glyphs commonly omit 0x1000: the native emitter stops
            # on 0x2000/0x8000 there instead. They cannot define body timing.
            header=bool(oldpage['lines'][0]['words'][-1]&0x4000 and
                        (not oldpage['lines'][0]['words'][0]&0x1000 or (mi,pi) in immediate_headers))
            if (mi,pi) in immediate_headers and not header:raise ValueError('Speaker line has no native newline')
            header_words=oldpage['lines'][0]['words'] if header else []
            if header and len(lines)<2:raise ValueError('Immediate header/body boundary removed')
            body_words=words[len(header_words):]
            timing={w&0x1000 for w in body_words[:-1]}
            if len(timing)>1:raise ValueError('Mixed body typewriter timing requires an explicit mapping')
            body_flags=next(iter(side))|(next(iter(timing)) if timing else body_words[-1]&0x1000)
            for li,line in enumerate(lines):
                flags=(words[0]&0x800) if header and li==0 else body_flags
                encoded=[codes[c]|flags for c in line]
                if li+1==len(lines):
                    # Preserve the complete terminal control, including the
                    # few original terminal glyphs that also carry 0x1000.
                    encoded[-1]=(encoded[-1]&0x7ff)|(words[-1]&0xf800)
                else:
                    encoded[-1]|=0x4000
                    # Instant names can end with a four-tick pause before the
                    # body. Other native names intentionally have no pause.
                    if header and li==0:encoded[-1]|=header_words[-1]&0x1000
                out+=struct.pack('<'+'H'*len(encoded),*encoded)
            changes.append({'message':mi,'page':pi,'lines':lines,'side':next(iter(side)),'end_flags':oldpage['end_flags']})
        # Preserve trailing non-page data (PL00 dummy is deliberately unmodified).
        for line in message['trailing']:
            out+=struct.pack('<'+'H'*len(line['words']),*line['words'])
    text_end=len(out)
    out+=bytes((-len(out))%4);code_offset=len(out);out+=emit_cache_code()
    font_offset=len(out);font=b''.join(glyph_bitmap(c) for c in chars);out+=font
    if len(out)>65535:raise ValueError('Dialogue resource exceeds address range')
    out[128:144]=b'KOR1'+struct.pack('<III',font_offset,len(chars),code_offset)
    return bytes(out),{'translated_pages':len(changes),'total_pages':sum(len(m['pages']) for m in messages),'text_end':text_end,'code_offset':code_offset,'font_offset':font_offset,'font_bytes':len(font),'glyph_count':len(chars),'glyphs':''.join(chars),'pages':changes,'size':len(out)}

def replace_text_same_capacity(arc,text):
    from scripts.discover_inputs import psx_arc
    entries=psx_arc(arc);e=entries[-1]
    # Native CD loader packs RAM resources by their declared lengths, without
    # rounding: D_80137DC4 += D_80137DC8 (func_80013E68). Sector padding alone
    # cannot keep the next archive's word-addressed data aligned.
    if any(int(item['type'],16)<0x10000 and item['size']%4 for item in entries):
        raise ValueError('Unaligned native ARC RAM resource')
    # Keep the original sector allocation even when Korean text is shorter.
    declared=max(e['size'],(len(text)+3)&~3)
    if e['type']!='0x15' or declared>len(arc)-e['offset']:raise ValueError('Text exceeds current ARC allocation')
    out=bytearray(arc);struct.pack_into('<I',out,12+e['index']*8,declared)
    out[e['offset']:]=text+bytes(len(arc)-e['offset']-len(text))
    return bytes(out)
