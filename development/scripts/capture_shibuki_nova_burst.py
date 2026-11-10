"""Capture Nova display pages without assuming CPU/GPU frame synchronization."""
import argparse,ctypes,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,new_run,write_json
from scripts.emulator_session import checked_window
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from src.epsxe_state import framebuffer,match_sprite
from scripts.extract_zero import save_image

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],default='ver_buki_riko');p.add_argument('--evidence',type=Path,required=True);p.add_argument('--ready-file',type=Path,required=True);p.add_argument('--seconds',type=float,default=6);a=p.parse_args()
    if not .1<=a.seconds<=8 or a.ready_file.exists() or not a.ready_file.resolve().is_relative_to(ROOT/'work'):raise ValueError('Invalid capture scope')
    if a.project=='ver_rin_nana':
        import scripts.emulator_session as session_control
        session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
    prior=json.loads(a.evidence.read_text());checked_window(prior['pid']);build=Path(prior['source_build']);manifest=json.loads((build/'manifest.json').read_text());arc=(build/'PL02_U.ARC').read_bytes()
    if not build.resolve().is_relative_to(ROOT/'out'/a.project):raise ValueError('Unexpected project build')
    requested=range(213,221) if a.project=='ver_rin_nana' else (217,218,219,220)
    if digest(build/'PL02_U.ARC')!=manifest['modified_archive_sha256'] or manifest['modified_bin']['sha256']!=prior['modified_bin_sha256']:raise ValueError('Changed build')
    ram_base,=prior['ram_candidates'];video,=prior['vram_candidates'];g,c=entry(arc,2),entry(arc,3)
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE;k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x410,False,prior['pid']);assert h
    def read(address,size):
        b=ctypes.create_string_buffer(size);got=ctypes.c_size_t()
        if not k.ReadProcessMemory(h,address,b,size,ctypes.byref(got)) or got.value!=size:raise OSError('Process read failed')
        return b.raw
    out=new_run(ROOT,a.project,'nova_burst');samples=[]
    try:
        ram=read(ram_base,0x200000)
        if ram.count(g)!=1 or ram.count(c)!=1 or ram[0x1721f7]!=1:raise ValueError('Wrong runtime assets')
        write_json(a.ready_file,{'output':str(out),'pid':prior['pid']});deadline=time.monotonic()+a.seconds
        while time.monotonic()<deadline:
            player=read(ram_base+0x1418c8,0xe4)
            if player[0x47] in requested and len(samples)<240:samples.append((player,read(video,1048576)))
            time.sleep(.008)
    finally:k.CloseHandle(h)
    bank=graphics_bank(g,0,allow_bank_aliases=True);targets={}
    for n in requested:
        f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;targets[n]=canvas_from_parts(raw,f['tile_count'],local_composition(composition_frame(c,5,n)),size=(256,160))
    matches=[];scenes=[];observed=set()
    for i,(player,vram) in enumerate(samples):
        observed.add(player[0x47]);words=struct.unpack_from('<16H',vram,(0x7843>>6)*2048+(0x7843&63)*32)
        screens=[framebuffer(vram,0,y) for y in (0,256)]
        for n,t in targets.items():
            im=save_image(t.tobytes(),(256,160),words,out/'scratch.png').convert('RGBA');im=im.crop(im.getbbox())
            for page,screen in zip((0,256),screens):
                found=match_sprite(screen,im)
                if found:
                    name=f'match_{n}_{i:03}_{page}.png';screen.save(out/name);matches.append({'displayed_frame':n,'cpu_frame':player[0x47],'direction':player[0x15]&64,'page':page,'image':name,'matches':found})
        if i%3==0:
            for page,screen in zip((0,256),screens):
                name=f'sample_{i:03}_{page}.png';screen.save(out/name);scenes.append(name)
    write_json(out/'verification.local.json',{'pid':prior['pid'],'build':str(build),'bin_sha256':manifest['modified_bin']['sha256'],'samples':len(samples),'observed_cpu_frames':sorted(observed),'verified_display_frames':sorted({r['displayed_frame'] for r in matches}),'matches':matches,'scene_samples':scenes,'process_memory_written':False})
    print(json.dumps({'output':str(out),'samples':len(samples),'verified_frames':sorted({r['displayed_frame'] for r in matches})}))

if __name__=='__main__':main()
