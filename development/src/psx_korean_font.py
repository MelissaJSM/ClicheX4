"""Bounded US dialogue font-cache proposal; emits code, never patches a disc."""
import struct

R={'zero':0,'at':1,'v0':2,'v1':3,'a0':4,'a1':5,'a2':6,'a3':7,
   't0':8,'t1':9,'t2':10,'t3':11,'t4':12,'t5':13,'t6':14,'t7':15,
   's0':16,'s1':17,'s2':18,'t8':24,'t9':25,'sp':29,'ra':31}

class Assembly:
    def __init__(self):self.words=[];self.labels={};self.fixups=[]
    def emit(self,w):self.words.append(w)
    def nop(self):self.emit(0)
    def label(self,n):
        if n in self.labels:raise ValueError('Duplicate assembly label')
        self.labels[n]=len(self.words)
    def imm(self,op,rt,rs,value):self.emit(op<<26|R[rs]<<21|R[rt]<<16|(value&65535))
    def reg(self,fn,rd,rs,rt,shift=0):self.emit(R[rs]<<21|R[rt]<<16|R[rd]<<11|shift<<6|fn)
    def move(self,rd,rs):self.reg(0x21,rd,rs,'zero')
    def shift(self,fn,rd,rt,n):self.reg(fn,rd,'zero',rt,n)
    def branch(self,op,rs,rt,label):
        self.fixups.append((len(self.words),label));self.imm(op,rt,rs,0)
    def jump(self,op,address):self.emit(op<<26|((address>>2)&0x3ffffff))
    def finish(self):
        out=list(self.words)
        for at,label in self.fixups:
            distance=self.labels[label]-at-1
            if not -32768<=distance<=32767:raise ValueError('Branch out of range')
            out[at]|=distance&65535
        return struct.pack('<'+'I'*len(out),*out)

def emit_cache_code():
    """a0=AbcObj, a1=current 4-byte glyph record; preserves s0/s1/s2/ra.

    Header at the dialogue resource: +128 magic, +132 font offset,
    +136 glyph count, +140 code offset. Glyphs are 12x12, LSB-first 1bpp
    (18 bytes). Existing blank font tiles192..251 provide 60 cache slots.
    The code runs through KSEG1 to avoid executing a stale instruction cache.
    """
    a=Assembly();i=a.imm;r=a.reg;s=a.shift;b=a.branch
    i(9,'sp','sp',-192);i(43,'ra','sp',188);i(43,'s0','sp',184);i(43,'s1','sp',180);i(43,'s2','sp',176)
    a.move('s0','a0');a.move('s1','a1');i(40,'zero','s1',0)
    i(37,'t0','s0',4);a.nop();i(12,'t0','t0',0x7ff)
    i(11,'t1','t0',256);b(5,'t1','zero','legacy');a.nop()
    i(9,'t0','t0',-256);i(15,'s2','zero',0x1f80);i(35,'s2','s2',0x48);a.nop()
    i(35,'t1','s2',136);a.nop();r(0x2b,'t1','t0','t1');b(4,'t1','zero','invalid');a.nop()
    i(15,'t1','zero',0x8014);i(37,'t1','t1',-0x6820);a.nop()
    i(11,'t2','t1',60);b(4,'t2','zero','invalid');a.nop()
    i(9,'t1','t1',192);i(40,'t1','s1',1)
    # Rectangle x960+(tile%16)*4 words, y256+(tile//16)*16 pixels.
    i(12,'t2','t1',15);s(0,'t2','t2',2);i(9,'t2','t2',960);i(41,'t2','sp',16)
    s(2,'t1','t1',4);s(0,'t1','t1',4);i(9,'t1','t1',256);i(41,'t1','sp',18)
    i(9,'t1','zero',4);i(41,'t1','sp',20);i(9,'t1','zero',16);i(41,'t1','sp',22)
    # Source = message base + font offset + glyph*18.
    i(35,'t1','s2',132);s(0,'t2','t0',4);s(0,'t0','t0',1);r(0x21,'t0','t0','t2')
    r(0x21,'s2','s2','t1');r(0x21,'s2','s2','t0')
    # Clear all 16x16 pixels, including two blank top/bottom rows and right pad.
    i(9,'t0','sp',32);i(9,'t1','zero',32);a.label('clear')
    i(43,'zero','t0',0);i(9,'t0','t0',4);i(9,'t1','t1',-1);b(5,'t1','zero','clear');a.nop()
    i(9,'t0','sp',48);a.move('t1','zero');i(9,'t7','zero',12)
    # 2 input bits -> two native palette14 (white) nibbles.
    i(15,'t5','zero',0xeee0);i(13,'t5','t5',0x0e00)
    a.label('row');i(9,'t6','zero',6);a.label('pair')
    s(2,'t2','t1',2);r(0x21,'t2','t2','s2');i(36,'t2','t2',0)
    i(12,'t3','t1',3);s(0,'t3','t3',1);r(6,'t2','t3','t2');i(12,'t2','t2',3)
    s(0,'t2','t2',3);r(6,'t2','t2','t5');i(40,'t2','t0',0)
    i(9,'t0','t0',1);i(9,'t1','t1',1);i(9,'t6','t6',-1);b(5,'t6','zero','pair');a.nop()
    i(9,'t0','t0',2);i(9,'t7','t7',-1);b(5,'t7','zero','row');a.nop()
    # Synchronize before overwriting previous-page cache and before releasing
    # the stack-backed upload buffer. Native SDK calls, no gameplay hooks.
    a.jump(3,0x800ea20c);a.move('a0','zero')
    i(9,'a0','sp',16);a.jump(3,0x800ea4d0);i(9,'a1','sp',32)
    a.jump(3,0x800ea20c);a.move('a0','zero')
    b(4,'zero','zero','return');a.nop()
    a.label('invalid');i(9,'t0','zero',0x88)
    a.label('legacy');i(40,'t0','s1',1)
    a.label('return')
    i(15,'v0','zero',0x8014);i(37,'v0','v0',-0x6820);i(37,'v1','s0',6);s(0,'v0','v0',2)
    i(35,'ra','sp',188);i(35,'s0','sp',184);i(35,'s1','sp',180);i(35,'s2','sp',176)
    r(8,'zero','ra','zero');i(9,'sp','sp',192)
    return a.finish()

def emit_hook():
    a=Assembly();i=a.imm;r=a.reg
    i(15,'t0','zero',0x1f80);i(35,'t0','t0',0x48)
    i(15,'a1','zero',0x8014);i(9,'a1','a1',-0x6934);r(0x21,'a1','a1','v0')
    i(35,'t9','t0',140);i(15,'t1','zero',0x2000);r(0x21,'t9','t9','t0');r(0x25,'t9','t9','t1')
    r(9,'ra','t9','zero');a.move('a0','s0')
    a.nop();a.nop();a.nop()
    out=a.finish()
    if len(out)!=56:raise AssertionError('Hook does not fit original store block')
    return out

def font_cache_proposal(exe):
    """Return a reviewable EXE proposal; requires all three dialogue resources."""
    if exe[:8]!=b'PS-X EXE' or struct.unpack_from('<I',exe,24)[0]!=0x80010000:raise ValueError('Wrong executable')
    out=bytearray(exe);edits=[]
    def patch(address,before,after):
        off=address-0x80010000+2048
        if exe[off:off+len(before)]!=before or len(before)!=len(after):raise ValueError(f'Unexpected text instructions at {address:08x}')
        out[off:off+len(after)]=after;edits.append({'address':address,'offset':off,'before':before.hex(),'after':after.hex()})
    patch(0x800232a8,struct.pack('<I',0x240201ff),struct.pack('<I',0x240207ff))
    patch(0x800232b0,struct.pack('<I',0x306301ff),struct.pack('<I',0x306307ff))
    # Exact bytes are supplied below by a literal opcode list, not guessed from
    # the assembler's alias spellings.
    ops=[0x3c018014,0x00220821,0xa02096cc,0x3c028014,0x844297e0,0x96030004,0x00021080,0x3c018014,0x00220821,0xa02396cd,0x3c028014,0x844297e0,0x96030006,0x00021080]
    original=struct.pack('<14I',*ops)
    patch(0x800233c8,original,emit_hook())
    return bytes(out),{'kind':'korean_dialogue_font_cache_proposal','code_bytes':len(emit_cache_code()),'hook_changes':edits,'changed_bytes':sum(a!=b for a,b in zip(exe,out)),'reserved_tiles':[192,251],'maximum_visible_glyphs':60,'advance_pixels':12,'line_step_pixels':18,'bin_applied':False}
