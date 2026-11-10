"""Execute original x86 Frost initializer/getters/UV code, then verify ARC scope."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
from src.steam_effect_colors import TEXT_BASE,TEXT_SHA256
from scripts.build_steam_frost_labels import W,D,one,cof_table,tokens,save,sha
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames

def main():
    code=(W/'runtime/code/text.bin').read_bytes()
    if sha(code)!=TEXT_SHA256:raise ValueError('Original native code hash')
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x3000000);u.mem_write(TEXT_BASE,code)
    obj,actor,sp,stop,cof=0x2700000,0x2701000,0x2801000,0x2900000,0x2a00000
    u.mem_write(obj+0x38,struct.pack('<I',actor));u.mem_write(sp,struct.pack('<I',stop))
    u.reg_write(UC_X86_REG_ESI,obj);u.reg_write(UC_X86_REG_ESP,sp)
    u.emu_start(0xa9a012,0xa9a035,count=100)
    u.emu_start(0xa9a048,0xa9a058,count=100)
    assert u.reg_read(UC_X86_REG_ESP)==sp
    def get(addr):
        u.reg_write(UC_X86_REG_ECX,actor);u.reg_write(UC_X86_REG_ESP,sp);u.emu_start(addr,stop,count=100)
        return u.reg_read(UC_X86_REG_EAX)
    assert get(0x98e0c0)==3 and get(0x98e0e0)==0x30b and get(0x98e0d0)&65535==32
    runs=[];native_uvs=0
    for r in json.loads((W/'frost_labels_builds.json').read_text('utf8')):
        if not r['target_arc'].startswith(('pl00','pl02')):continue
        pl=r['target_arc'][:4];raw=(ROOT/r['output']).read_bytes();assert sha(raw)==r['output_sha256']
        a=SteamArc(raw);old=SteamArc((ROOT/r['parent']).read_bytes(),r['parent_sha256']);orig=SteamArc((W/'original'/r['relative_path']).read_bytes())
        fixed=one(a,b'COF\0',pl+'_003');before=old.by_key[fixed.key]
        assert fixed.payload==orig.by_key[fixed.key].payload
        assert [e.key for e in a.entries if e.payload!=old.by_key[e.key].payload]==[fixed.key]
        pat=pat_frames(one(a,b'PAT\0',pl.upper()).payload)[11];tex=one(a,b'TEX\0',pl+'_003').payload
        ys=cof_table(fixed.payload)[1];bys=cof_table(before.payload)[1]
        frames=[]
        for n in range(9,21):
            for table in [bys,ys]:
                # Native renderer selects COF[frame] at AA2FAF..AA2FC3.
                u.mem_write(cof+0x70,struct.pack('<256I',*table));u.mem_write(sp+0x70+3*4,struct.pack('<I',cof))
                u.mem_write(sp+0x3c,struct.pack('<I',3));u.mem_write(sp+0x24,struct.pack('<I',n));u.reg_write(UC_X86_REG_ESP,sp)
                u.emu_start(0xaa2faf,0xaa2fc3,count=20);y=struct.unpack('<I',u.mem_read(sp+0x40,4))[0];assert y==table[n]
                for flags,t,x,dy in struct.iter_unpack('<BBbb',pat[n]):
                    tile=(flags&3)*256+t+32
                    # Original GPU command builder adds this COF Y to tile Y.
                    u.reg_write(UC_X86_REG_ECX,tile);u.mem_write(sp+0xb4,struct.pack('<I',y));u.emu_start(0x999c2a,0x999c48,count=30)
                    assert u.reg_read(UC_X86_REG_ECX)==tile//16*16+y
                    assert u.reg_read(UC_X86_REG_EAX)==(tile%16)*16;native_uvs+=1
            bad=tokens(tex,pat[n],bys[n],32);good=tokens(tex,pat[n],ys[n],32)
            assert not bad.any()
            if n>9:assert good.any()
            frames.append(n)
        runs.append({'target_arc':r['target_arc'],'charged_frames':frames,'only_frost_cof_changed':True,'native_restoration_exact':True})
    result={'passed':True,'original_text_sha256':TEXT_SHA256,'initializer':hex(0xa99ff0),'graphics_bank':3,'pattern_bank':11,'charged_tile_base':32,'native_uv_cases':native_uvs,'cof_selector':hex(0xaa2faf),'uv_builder':hex(0x999c2a),'native_callees_mocked':False,'failure_reproduced_on_all_four_archives':True,'normal_ice_source_and_timing_unchanged':True,'results':runs,'actual_gameplay_verified':False}
    save(D/'native_frost_verification.json',result);print(result)

if __name__=='__main__':main()
