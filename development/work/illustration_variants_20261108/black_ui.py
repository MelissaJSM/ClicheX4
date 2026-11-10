"""Black Zero UI palette proposal in the existing HQ function allocation."""
from pathlib import Path
import sys, struct, json, hashlib

ROOT = Path(__file__).resolve().parents[2]
H = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.psx_korean_font import Assembly

START, END = 0x800C9EE8, 0x800CA0C8
OLD_ANIMATE, TABLE = 0x800CA030, 0x8010E57C
HOOK = 0x80022994
CHANGES = {
    'ver_rin_nana': {2:(8,3,5), 3:(13,4,7), 7:(22,2,5), 8:(30,4,7), 9:(31,12,14)},
    'ver_buki_riko': {2:(28,29,30), 3:(3,4,6), 4:(5,6,8), 5:(11,12,15), 13:(21,22,24)},
}

def off(a): return a - 0x80010000 + 2048
def sha(b): return hashlib.sha256(b).hexdigest()
def words(mode):
    normal = json.loads((H/mode/'source.json').read_text('utf8'))['portraits']['zero_hq']['palette']
    other = json.loads((H/mode/'source.json').read_text('utf8'))['portraits']['zero_dialogue']['palette']
    assert normal == other
    result = list(normal)
    for idx, (r,g,b) in CHANGES[mode].items(): result[idx] = (normal[idx]&0x8000) | r | g<<5 | b<<10
    return normal, result

def init(helper):
    a=Assembly(); i=a.imm; b=a.branch; r=a.reg; s=a.shift
    i(9,'sp','sp',-24); i(43,'ra','sp',20); i(43,'s0','sp',16); a.move('s0','a0')
    i(32,'v0','s0',2); i(15,'t0','zero',0x8017); i(32,'t1','t0',0x2203)
    r(0x2b,'t2','zero','v0')  # native: every nonzero signed partner value
    s(0,'t3','t2',2); i(9,'t3','t3',8)
    i(15,'t4','zero',0x8014); i(35,'t4','t4',0x6a8)
    i(15,'v1','zero',0x1f80); i(35,'v1','v1',0x20)
    r(0x21,'t4','t4','t3'); r(0x21,'v1','v1','t3')
    i(35,'t4','t4',0); i(35,'v0','v1',0); r(0x23,'v1','v1','t3')
    s(2,'t4','t4',7); r(0x21,'v1','v1','v0'); i(43,'v1','s0',0x3c); i(41,'t4','s0',0x40)
    s(0,'v0','t2',1); i(9,'v0','v0',0x7883); i(41,'v0','s0',0x42)
    s(0,'v0','t2',4); s(0,'v1','v0',4); r(0x23,'v1','v1','v0')
    i(9,'v1','v1',42); s(0,'v1','v1',16); i(43,'v1','s0',8)
    i(9,'v0','v0',416); s(0,'v0','v0',16); i(43,'v0','s0',12)
    i(15,'v0','zero',0x8011); i(9,'v0','v0',-0x1aec)
    b(4,'t1','zero','x'); i(9,'v1','zero',-40)
    i(9,'v0','v0',36); i(9,'v1','zero',36)
    a.label('x'); b(4,'t2','zero','anim'); a.nop(); r(0x21,'v0','v0','v1')
    a.label('anim'); i(43,'v0','s0',0x30)
    b(5,'t2','zero','nocolor'); a.move('a0','s0'); a.jump(3,helper); a.nop()
    a.label('nocolor'); i(36,'v0','s0',4); i(9,'v1','zero',3)
    i(40,'zero','s0',0x14); i(40,'zero','s0',0x15); i(40,'v1','s0',0x16)
    i(9,'v0','v0',1); i(40,'v0','s0',4); a.move('a0','s0')
    a.jump(3,0x80015d60); a.move('a1','zero')
    a.move('a0','s0'); i(35,'ra','sp',20); i(35,'s0','sp',16)
    a.jump(2,0x8002b288); i(9,'sp','sp',24)
    return a.finish()

def animate():
    a=Assembly(); i=a.imm; b=a.branch; r=a.reg
    i(9,'sp','sp',-24); i(43,'ra','sp',20); i(43,'s0','sp',16); a.move('s0','a0')
    i(32,'v0','s0',2); i(15,'t0','zero',0x8017); i(36,'a1','t0',0x2200)
    r(0x2b,'v0','zero','v0'); i(9,'t0','zero',16); r(4,'t0','v0','t0')
    r(0x24,'v0','a1','t0'); b(5,'v0','zero','set'); a.nop()
    a.jump(3,0x80015dc8); a.nop(); b(4,'zero','zero','screen'); a.nop()
    a.label('set'); a.jump(3,0x80015d60); i(12,'a1','a1',15)
    a.label('screen'); a.move('a0','s0'); i(35,'ra','sp',20); i(35,'s0','sp',16)
    a.jump(2,0x8002b288); i(9,'sp','sp',24)
    return a.finish()

def palette_helper(mode):
    a=Assembly(); i=a.imm; b=a.branch; r=a.reg; s=a.shift
    i(15,'t0','zero',0x8017); i(36,'t1','t0',0x2203); i(36,'t0','t0',0x21f7)
    i(9,'t1','t1',-1); b(5,'t1','zero','return'); i(37,'t2','a0',0x42)
    b(4,'t0','zero','return'); i(15,'t1','zero',0x1f80)
    i(35,'t1','t1',0x28)
    i(12,'t0','t2',15); s(2,'t2','t2',2); i(12,'t2','t2',0x70)
    r(0x25,'t0','t0','t2'); s(0,'t0','t0',5); r(0x21,'t1','t1','t0')
    normal, black = words(mode)
    for idx in CHANGES[mode]:
        i(9,'t0','zero',black[idx]); i(41,'t0','t1',idx*2)
    i(15,'t0','zero',0x8016); i(36,'t1','t0',0x6bb0); a.nop()
    i(13,'t1','t1',1); i(40,'t1','t0',0x6bb0)
    a.label('return'); r(8,'zero','ra','zero'); a.nop()
    return a.finish()

def proposal(mode):
    old=(H/mode/'originals/SLUS_005.61').read_bytes()
    init_size=len(init(0)); anim=animate(); anim_addr=START+init_size; helper_addr=anim_addr+len(anim)
    code=init(helper_addr)+anim+palette_helper(mode)
    assert len(code)<=END-START,(len(code),END-START,init_size,len(anim))
    assert struct.unpack_from('<I',old,off(TABLE))[0]==OLD_ANIMATE
    assert old[off(HOOK):off(HOOK)+12]==bytes(12)
    # The original animate entry must only be referenced by its callback table.
    refs=[p for p in range(2048,len(old)-3,4) if old[p:p+4]==struct.pack('<I',OLD_ANIMATE)]
    assert refs==[off(TABLE)],refs
    jal=struct.pack('<I',3<<26|((OLD_ANIMATE>>2)&0x3ffffff)); jump=struct.pack('<I',2<<26|((OLD_ANIMATE>>2)&0x3ffffff))
    assert jal not in old[2048:off(0x800f0000)] and jump not in old[2048:off(0x800f0000)]
    new=bytearray(old); new[off(START):off(END)]=code.ljust(END-START,b'\0')
    struct.pack_into('<I',new,off(TABLE),anim_addr)
    h=Assembly(); h.jump(3,helper_addr); h.move('a0','s0'); h.nop()
    new[off(HOOK):off(HOOK)+12]=h.finish()
    return bytes(new), {'init_address':START,'init_bytes':init_size,'animate_address':anim_addr,'animate_bytes':len(anim),'helper_address':helper_addr,'helper_bytes':len(palette_helper(mode)),'region_bytes':len(code),'region_capacity':END-START,'normal_palette':words(mode)[0],'black_palette':words(mode)[1],'source_exe_sha256':sha(old),'target_exe_sha256':sha(new),'animate_pointer_references':refs,'palette_only_indices':list(CHANGES[mode]),'runtime_verified':False}

if __name__=='__main__':
    for mode in CHANGES:
        new,report=proposal(mode); d=H/mode/'black_proposal'; d.mkdir(exist_ok=True)
        (d/'SLUS_005.61').write_bytes(new); (d/'report.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
        print(mode,report)
