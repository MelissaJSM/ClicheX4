"""확정 candidate04 포스 노바의 실제 RAM/GPU를 읽기 전용 관측한다."""
import argparse,ctypes,hashlib,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import rgba
from src.psx_player import graphics_bank,bank_offsets,decode_stream,composition_frame,compose_indices
from src.psx_ui_atlas import local_composition
BUILD=ROOT/'out/ver_rin_nana/overhaul_20261105_candidate04/rin_nana.bin'
BIN_SHA='1a2d97272bb0dde2395aa7f1daa9136dd247125456090ff519fe3c484e3be2e2'
PLAYER=0x1418c8;BUF=0x16dea8

def sha(b):return hashlib.sha256(b).hexdigest()
def require(ok,msg):
    if not ok:raise ValueError(msg)
def digest(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
def load():
    require(digest(BUILD)==BIN_SHA,'Unexpected candidate BIN')
    with BUILD.open('rb')as f:
        d=DiscReader(f,BUILD.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files']}
        arc=d.read(rs['PL00_U.ARC']['lba'],rs['PL00_U.ARC']['size']);exe=d.read(rs['SLUS_005.61']['lba'],rs['SLUS_005.61']['size'])
    es={kind:entry(arc,kind)for kind in(2,3,9)};bank=graphics_bank(es[2],0,allow_bank_aliases=True);frames={}
    for n in range(213,221):
        f=bank['frames'][n];require(f['tile_count']<=32,'Buffer exceeds32 tiles')
        frames[n]=(f,decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data)
    return arc,exe,es,bank,frames
def compose(raw,count,parts,n,words,armtype,armor_words=None,arm_words=None):
    armor_words=words[16:32]if armor_words is None else armor_words
    arm_words=words[32:48]if arm_words is None else arm_words
    im=Image.new('RGBA',(384,384))
    for bi in(0,8,5,7,6):
        comp=composition_frame(parts,bi,n)
        if bi:comp=local_composition(comp)
        if not comp['parts']:continue
        data,size,bounds,_=compose_indices(raw,count,comp,allowed_cluts={0,1,2,3})
        small=np.frombuffer(data,np.uint8).reshape(size[1],size[0]);arr=np.zeros((384,384),np.uint8);ys,xs=np.nonzero(small)
        arr[ys+bounds[1]+160,xs+bounds[0]+160]=small[ys,xs]
        pal=words if bi==0 else arm_words if bi==7 and armtype==2 else armor_words
        im.alpha_composite(rgba(arr,pal))
    return im
def main(a):
    arc,exe,es,bank,frames=load()
    if a.prepare_only:
        print(json.dumps({'prepared':True,'bin_sha256':BIN_SHA,'arc_sha256':sha(arc),'frames':list(frames),'process_opened':False}));return
    out=a.out.resolve();require(out.is_relative_to(ROOT/'work/overhaul_20261105/ui')and not out.exists(),'Fresh UI output required')
    require(a.pid and a.ram_base and a.vram_base and 0<a.seconds<=30,'PID/address and duration 1..30 needed')
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x410,False,a.pid)
    if not h:raise OSError('Read-only process open failed')
    def read(at,n):
        b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
        if not k.ReadProcessMemory(h,at,b,n,ctypes.byref(got))or got.value!=n:raise OSError('Read failed')
        return b.raw
    try:
        ram=read(a.ram_base,0x200000);assets={}
        for pos in(0x1540c,0x15ecc,0x233c8):require(ram[pos:pos+64]==exe[pos-0x10000+2048:pos-0x10000+2112],'Native EXE differs')
        for kind in(2,3,9):
            at=ram.find(es[kind]);require(at>=0 and ram.find(es[kind],at+1)<0,'Resident asset missing/ambiguous '+str(kind));assets[str(kind)]={'ram_offset':at,'size':len(es[kind]),'sha256':sha(es[kind])}
        gptr=0x80000000+assets['2']['ram_offset']+bank['base'];cptr=0x80000000+assets['3']['ram_offset']+bank_offsets(es[3])[0]
        p=ram[PLAYER:PLAYER+228];require(p[2]==0 and p[0xa7]==15 and ram[0x1721f7]==0,'Expected Nana full Fourth armor0F/Ultimate0')
        require(struct.unpack_from('<II',p,0x38)==(gptr,cptr),'Active graphics/composition differs')
        out.mkdir(parents=True);(out/'ram_start.bin').write_bytes(ram)
        print(json.dumps({'ready':True,'pid':a.pid,'seconds':a.seconds,'output':str(out),'armor':15,'ultimate':0}),flush=True)
        start=time.monotonic();events=[];matched=set();key=None;active=None;skipped=0;polls=0
        while time.monotonic()-start<a.seconds:
            p=read(a.ram_base+PLAYER,228);n=p[0x47];gp,cp=struct.unpack_from('<II',p,0x38)
            if p[2]!=0 or p[0xa7]!=15 or n not in frames or(gp,cp)!=(gptr,cptr)or read(a.ram_base+0x1721f7,1)!=b'\0':skipped+=1;time.sleep(.003);continue
            f,expected=frames[n];sample=(n,p[0x17],p[0x15],p[0xb8]);now=time.monotonic()-start
            if sample!=key:
                active={'frame':n,'animation':p[0x17],'facing_raw':p[0x15],'armtype':p[0xb8],'first_seconds':now,'last_seconds':now,'attempts':0,'stable_samples':0,'ram_mismatch_samples':0,'gpu_mismatch_samples':0,'verified':False};events.append(active);key=sample
            decoded=read(a.ram_base+BUF,len(expected));gpu=bytearray()
            for first in range(0,f['tile_count'],16):
                width=min(16,f['tile_count']-first)*8
                for y in range(16):gpu+=read(a.vram_base+(first//16*16+y)*2048+640,width)
            again=read(a.ram_base+PLAYER,228);active['attempts']+=1;polls+=1;active['last_seconds']=time.monotonic()-start
            if(again[0x47],again[0x17],again[0x15],again[0xb8])!=sample or again[0xa7]!=15:continue
            active['stable_samples']+=1;active['ram_mismatch_samples']+=decoded!=expected;active['gpu_mismatch_samples']+=gpu!=expected
            if decoded==gpu==expected and not active['verified']:
                clut=struct.unpack_from('<H',p,0x42)[0];clut=0x7840 if clut&0x8000 else clut
                offset=(clut>>6)*2048+(clut&63)*32;colors=read(a.vram_base+offset,128)
                # Native func_800257BC passes fixed 0x7843/0x7844, not base+1/+2.
                def clut_bytes(code):return read(a.vram_base+(code>>6)*2048+(code&63)*32,32)
                armor_colors=clut_bytes(0x7843);arm_colors=clut_bytes(0x7844)
                rows=[colors[:32]==es[9][:32],armor_colors==es[9][32:64],arm_colors==es[9][64:96]]
                raw=bytes(gpu);stem=f'frame_{n:03}_{len(events):03}';(out/(stem+'.bin')).write_bytes(raw)
                (out/(stem+'_palettes.bin')).write_bytes(colors+armor_colors+arm_colors)
                actual=compose(raw,f['tile_count'],es[3],n,struct.unpack('<64H',colors),p[0xb8],struct.unpack('<16H',armor_colors),struct.unpack('<16H',arm_colors));actual.save(out/(stem+'_GPU_palette.png'))
                expected_image=compose(expected,f['tile_count'],es[3],n,struct.unpack_from('<64H',es[9]),p[0xb8])
                active.update(verified=True,tiles=f['tile_count'],ram_sha256=sha(decoded),gpu_sha256=sha(raw),expected_sha256=sha(expected),clut=hex(clut),armor_clut='0x7843',arm2_clut='0x7844',palette_rows_matching=rows,composition_matches_disc_with_live_palette=actual.tobytes()==expected_image.tobytes(),gpu_capture=stem+'.bin',composition_capture=stem+'_GPU_palette.png');matched.add(n)
            time.sleep(.003)
        final=read(a.ram_base,0x200000);(out/'ram_end.bin').write_bytes(final)
        report={'bin':BUILD.relative_to(ROOT).as_posix(),'bin_sha256':BIN_SHA,'arc_sha256':sha(arc),'pid':a.pid,'ram_host_base':a.ram_base,'vram_host_base':a.vram_base,'character':0,'armor':15,'ultimate':0,'seconds':time.monotonic()-start,'polls':polls,'skipped':skipped,'assets':assets,'assets_still_exact':{kind:final[v['ram_offset']:v['ram_offset']+v['size']]==es[int(kind)]for kind,v in assets.items()},'verified_frames':sorted(matched),'unobserved_frames':sorted(set(frames)-matched),'events':events,'keys_sent':False,'process_memory_written':False,'state_or_cards_modified':False,'limitation':'GPU bytes and live palettes are recomposed from authenticated resident part tables; this is not a framebuffer comparison. Non-atomic transition misses are recorded and do not alone prove a bug. Only observed frames are runtime verified.'}
        (out/'evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'verified_frames':sorted(matched)}),flush=True)
    finally:k.CloseHandle(h)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare-only',action='store_true');p.add_argument('--pid',type=int);p.add_argument('--ram-base',type=lambda x:int(x,0));p.add_argument('--vram-base',type=lambda x:int(x,0));p.add_argument('--seconds',type=float,default=15);p.add_argument('--out',type=Path);main(p.parse_args())
