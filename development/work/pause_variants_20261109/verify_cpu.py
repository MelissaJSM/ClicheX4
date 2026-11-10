"""Execute the original full pause widget renderer and candidate on MIPS."""
from pathlib import Path
import struct, json, sys
import unicorn as uc
from unicorn import mips_const as m
from PIL import Image
from prepare import ROOT,H,MODES,entry,sha,save_json,off,HOOK,hook,selector,aliased_composition,render_static_rgba

STOP=0x80008000
PAL,PARTS,PRIM,MODE,LINK=0x180000,0x181000,0x190000,0x192000,0x193000
ENGINE=0x1721c0
DRAW_SYNC=0x800ea0f4

def run(exe,arc,item,char=0,special=0,armor=0,flag=0,life=0,weapon=0,selected=0):
    u=uc.Uc(uc.UC_ARCH_MIPS,uc.UC_MODE_MIPS32|uc.UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0,0x200000);u.mem_map(0x1f800000,4096)
    u.mem_write(0x10000,exe[2048:]);u.mem_write(PAL,entry(arc,17));u.mem_write(PARTS,entry(arc,18))
    u.mem_write(DRAW_SYNC&0x1fffffff,bytes(32))
    for p,v in [(0x38,PAL),(0x3c,PARTS),(0x100,PRIM),(0x104,MODE)]:u.mem_write(0x1f800000+p,struct.pack('<I',v|0x80000000))
    u.mem_write(0x13bc40+20,struct.pack('<I',LINK|0x80000000))
    engine=bytearray([0x5a]*128);engine[0x37]=special;engine[0x43]=char;engine[0x44]=life;engine[0x46]=0;engine[0x47]=armor
    u.mem_write(ENGINE,bytes(engine));u.mem_write(0x1754c5,bytes([flag]));u.mem_write(0x1754b4,bytes([selected]))
    u.mem_write(0x141bd8,struct.pack('<I',16));u.mem_write(0x14195b,bytes([weapon]));u.mem_write(0x141970,bytes([48]))
    vals={'SP':0x801ff000,'RA':STOP,'A0':item}
    for k in range(8):vals['S'+str(k)]=0x43210000+k*100
    vals['FP']=0x56781234
    for reg,value in vals.items():u.reg_write(getattr(m,'UC_MIPS_REG_'+reg),value)
    writes=[];calls=0;trace=[]
    def code(u,addr,size,data):
        trace.append(addr)
        if addr in (STOP,DRAW_SYNC):u.emu_stop()
    def mem(u,access,addr,size,value,data):
        addr&=0x1fffffff
        assert any(lo<=addr and addr+size<=hi for lo,hi in [(0x1fefb0,0x1ff000),(PRIM,PRIM+4096),(MODE,MODE+4096),(LINK,LINK+4),(0x13bc54,0x13bc58),(0x1f800100,0x1f800108)]),(hex(addr),size)
        writes.append((addr,size))
    u.hook_add(uc.UC_HOOK_CODE,code);u.hook_add(uc.UC_HOOK_MEM_WRITE,mem)
    pc=0x800175ac
    try:
        for _ in range(100):
            u.emu_start(pc,STOP+4,count=20000)
            pc=u.reg_read(m.UC_MIPS_REG_PC)
            if pc==STOP:break
            assert pc==DRAW_SYNC,hex(pc)
            pc=u.reg_read(m.UC_MIPS_REG_RA);calls+=1
            for reg in ['V0','V1','A0','A1','A2','A3','T0','T1','T2','T3','T4','T5','T6','T7','T8','T9']:
                u.reg_write(getattr(m,'UC_MIPS_REG_'+reg),1 if reg=='V0' else 0xdead0000)
        else:raise AssertionError('Too many native calls')
    except Exception:
        print(item,char,special,armor,'TRACE',[hex(v)for v in trace[-35:]]);raise
    assert pc==STOP
    for reg,value in vals.items():
        if reg!='A0':assert u.reg_read(getattr(m,'UC_MIPS_REG_'+reg))==value,reg
    assert bytes(u.mem_read(ENGINE,128))==engine
    assert bytes(u.mem_read(PAL,2048))==entry(arc,17)
    count=(struct.unpack('<I',u.mem_read(0x1f800100,4))[0]&0x1fffffff)-PRIM
    assert count%40==0
    primitives=bytes(u.mem_read(PRIM,count))
    return primitives,bytes(u.mem_read(MODE,count//5)),calls

def raster(arc,prims):
    g=entry(arc,0x10007);pal=entry(arc,17);canvas=Image.new('RGBA',(320,240))
    coords=[]
    from src.psx_ui_atlas import tile_pixels
    for k in range(0,len(prims),40):
        x,y=struct.unpack_from('<hh',prims,k+8);u,v=prims[k+12:k+14];clut=struct.unpack_from('<H',prims,k+14)[0]
        assert u%16==v%16==0 and clut in (0x790a,0x790b),(u,v,hex(clut))
        words=struct.unpack_from('<16H',pal,(10+(clut==0x790b))*32)
        colors=[tuple((w>>s&31)*255//31 for s in (0,5,10))+(255 if i else 0,)for i,w in enumerate(words)]
        im=Image.new('RGBA',(16,16));im.putdata([colors[q]for q in tile_pixels(g,(v//16)*16+u//16)])
        canvas.alpha_composite(im,(x,y));coords.append((x,y))
    return canvas,coords

def main():
    reports=[]
    for mode in MODES:
        d=H/mode;before=(d/'originals/SLUS_005.61').read_bytes();after=(d/'prepared/SLUS_005.61').read_bytes()
        assert before[:off(HOOK)]==after[:off(HOOK)] and before[off(HOOK)+len(hook()):]==after[off(HOOK)+len(hook()):]
        generic=0;portraits=0
        for name in ['PL00_U.ARC','PL02_U.ARC','PL01_U.ARC']:
            old=(d/'originals'/name).read_bytes();new=(d/'prepared'/name).read_bytes()
            # Every other widget; both character paths, highlights, life counter, optional item.
            for item in range(39):
                if item==30:continue
                for char in (0,1):
                    for flag in (0,1):
                        for life in ((0,9) if item==31 else (0,)):
                            kw=dict(item=item,char=char,flag=flag,life=life,weapon=flag*2,selected=item&15)
                            assert run(before,old,**kw)==run(after,new,**kw),(mode,name,kw)
                            generic+=1
            for char in (0,1):
                for special in (0,1,255):
                    for armor in range(16):
                        p,_,calls=run(after,new,30,char,special,armor)
                        original=run(before,old,30,char,special,armor)[0]
                        assert len(p)==len(original)==760 and calls==19
                        got,coords=raster(new,p)
                        oldcoords=[struct.unpack_from('<hh',original,k+8)for k in range(0,760,40)]
                        assert coords==oldcoords
                        idx=(1 if special else 0) if char else ((4+(armor!=0)) if special else armor&3)
                        im=Image.open(d/'prepared'/f'{name[:4]}_{idx}.png').convert('RGBA')
                        expected=Image.new('RGBA',(320,240));expected.alpha_composite(im,(32,144))
                        assert got.tobytes()==expected.tobytes(),(mode,name,char,special,armor,idx)
                        portraits+=1
            # Save raster from actual emitted native GPU sprite primitives, not just a sheet renderer.
            from scripts.prepare_ui_revision import pause_background
            for idx in ([0,1,2,3]if name=='PL00_U.ARC' else [0,1]):
                char=int(name=='PL01_U.ARC');special=(idx if char else int(name=='PL02_U.ARC'))
                armor=idx if name=='PL00_U.ARC' else 15*idx
                p,_,_=run(after,new,30,char,special,armor)
                face,_=raster(new,p);bg=pause_background(new);bg.alpha_composite(face)
                bg.save(d/'prepared'/f'menu_{name[:4]}_{idx}.png')
        report={'mode':mode,'unicorn_version':uc.__version__,'generic_widget_cases':generic,
            'portrait_state_cases':portraits,'native_function_executed':'0x800175AC',
            'geometry_primitives_19_and_menu_origin_exact':True,'native_gpu_output_equals_registered_art':True,
            'all_other_widget_output_identical':True,'engine_palette_saved_registers_preserved':True,
            'only_native_stack_gpu_buffers_ot_scratch_written':True,'exe_sha256':sha(after),'passed':True,'actual_gameplay_verified':False}
        save_json(d/'prepared/cpu_verification.json',report);reports.append(report)
        print(mode,generic,portraits,'PASS',flush=True)
    save_json(H/'cpu_verification.json',reports)
if __name__=='__main__':main()
