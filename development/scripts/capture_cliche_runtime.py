"""Read-only logo VRAM/framebuffer evidence, bound to an emulator session."""
import argparse,ctypes,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window
from scripts.capture_poc_memory import Region
from scripts.prepare_riko_ui import entry
from scripts.prepare_cliche_logo import image_indices
from scripts.prepare_cliche_logo import words_at
from scripts.inventory_cliche_logo import indexed,D
from scripts.project import digest,new_run
from src.epsxe_state import framebuffer,match_sprite
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
import numpy as np

def main(session,label,seconds,known_base=None,mode='loading'):
    if not .1<=seconds<=30:raise ValueError('Capture duration')
    rec=json.loads((session/'session.local.json').read_text());checked_window(rec['pid']);build=Path(rec['cue']).parent
    if digest(build/'shibuki_riko.bin')!=rec['bin_sha256']:raise ValueError('Session build differs')
    g=entry((build/'LOAD_U.ARC').read_bytes(),0x10008);needle=g[8*128:9*128]
    recipe=json.loads((build/'recipe.json').read_text())
    pc=recipe['checks'].get('loading_palettes')
    if not pc:raise ValueError('Expected verified EXE loading palettes in recipe')
    a=indexed(g);expected=Image.new('RGBA',(112,32));expected.alpha_composite(image_indices(a[112:144,80:144],pc['row3']),(48,0));expected.alpha_composite(image_indices(a[112:144,:80],pc['row2']))
    if mode=='title':
        raw=(build/'ST0E_U0.ARC').read_bytes();p=struct.pack('<I',4)+entry(raw,0x12)
        pix,size,_,_=compose_static(entry(raw,0x10002),local_composition(aliased_composition(p,0,0)))
        expected=image_indices(np.frombuffer(pix,np.uint8).reshape(size[1],size[0]),words_at(entry((build/'COL0E_U0.ARC').read_bytes(),5),0))
    if len(set(needle))<8:raise ValueError('Weak VRAM anchor')
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t];k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x410,False,rec['pid'])
    if not h:raise OSError('Read-only process open failed')
    def read(a,n):
        buf=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
        return buf.raw if k.ReadProcessMemory(h,a,buf,n,ctypes.byref(got)) and got.value==n else b''
    out=new_run(ROOT,'ver_buki_riko','logo_runtime');bases=set();address=0;sample=[]
    try:
        if known_base:
            if not all(read(known_base+(256+y)*2048+896*2,128)==g[y*128:(y+1)*128] for y in (7,8,9,10)):raise ValueError('Cached VRAM anchor differs')
            bases.add(known_base)
        while not known_base and address<0x100000000:
            r=Region()
            if not k.VirtualQueryEx(h,address,ctypes.byref(r),ctypes.sizeof(r)):break
            lo=r.base or 0;end=lo+r.size
            if end<=address:break
            if r.state==0x1000 and not r.protect&0x100 and r.protect&255 in (2,4,8,32,64,128):
                for start in range(lo,end,1048576):
                    blob=read(start,min(end-start,1048704));pos=blob.find(needle)
                    while pos>=0:
                        base=start+pos-((256+8)*2048+896*2)
                        if base>0 and all(read(base+(256+y)*2048+896*2,128)==g[y*128:(y+1)*128] for y in (7,8,9,10)):bases.add(base)
                        pos=blob.find(needle,pos+1)
            address=end
        if not bases:raise ValueError('No verified LOAD texture in VRAM')
        start=time.monotonic();i=0
        while time.monotonic()-start<seconds:
            for base in sorted(bases):
                v=read(base,1048576)
                if len(v)!=1048576:continue
                if i==0:(out/f'vram_{base}.bin').write_bytes(v)
                pals=[struct.unpack_from('<16H',v,480*2048+n*32) for n in (2,3)]
                if i==0:expected.save(out/'expected.png')
                frames=[]
                for page in (0,256):
                    fb=framebuffer(v,0,page);path=out/f'frame_{i}_{page}.png'
                    hits=match_sprite(fb,expected)
                    if mode=='loading':
                        pos=recipe['checks'].get('loading_position',{'after':[208,256],'y':192})
                        hits=[h for h in hits if h['x']==pos['after'][0] and h['y']==pos['y'] and not h['flip_x']]
                    if i==0 or hits:fb.save(path)
                    frames.append({'page':page,'image':path.name if path.exists() else None,'matches':hits})
                sample.append({'i':i,'vram':base,'palette2':list(pals[0]),'palette3':list(pals[1]),'frames':frames})
                if any(f['matches'] for f in frames):
                    (out/f'vram_match_{i}.bin').write_bytes(v);start-=seconds
            i+=1;time.sleep(.25)
    finally:k.CloseHandle(h)
    report={'label':label,'mode':mode,'expected_palette_source':'build resource / verified US EXE table; independent of live palette','session':str(session),'bin_sha256':rec['bin_sha256'],'pid':rec['pid'],'vram_bases':sorted(bases),'samples':sample,'process_memory_written':False,'keys_sent':False}
    (out/'evidence.json').write_text(json.dumps(report,indent=2));print(json.dumps({'output':str(out),'samples':len(sample),'bases':sorted(bases)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--seconds',type=float,default=1);p.add_argument('--base',type=int);p.add_argument('--mode',choices=['title','loading'],default='loading');a=p.parse_args();main(a.session,a.label,a.seconds,a.base,a.mode)
