"""새 부팅 저장 화면의 포스아머 전체 도트와 세 색상표를 읽기 전용 대조한다."""
import argparse,ctypes,json,struct,sys
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import scripts.emulator_session as control
from scripts.capture_poc_memory import Region
from scripts.project import digest,new_run
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import DiscReader,sha256
from scripts.verify_shibuki_save_icon import icon,rgba
from src.epsxe_state import framebuffer,match_sprite

def main(session,build,mask,arm):
    session,build=session.resolve(),build.resolve()
    if not session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions') or not build.is_relative_to(ROOT/'out/ver_rin_nana'):raise ValueError('Unexpected path')
    s=json.loads((session/'session.local.json').read_text('utf8'));m=json.loads((build/'manifest.json').read_text('utf8'))
    if s['bin_sha256']!=m['modified_bin']['sha256'] or digest(build/'rin_nana.bin')!=s['bin_sha256']:raise ValueError('Session BIN differs')
    control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe';control.checked_window(s['pid'])
    ultimate=m['task']=='ultimate_armor_nana'
    # Inherited art folders are historical snapshots. Verify the actual disc.
    with (build/'rin_nana.bin').open('rb') as stream:
        disc=DiscReader(stream,(build/'rin_nana.bin').stat().st_size)
        records={q['path']:q for q in disc.inspect()['files']}
        assets={}
        for name in ('MOJIPAT.ARC','LOAD_U.ARC'):
            q=records['/ARC/'+name+';1'];assets[name]=disc.read(q['lba'],q['size'])
    menu=assets['MOJIPAT.ARC'];tex=entry(assets['LOAD_U.ARC'],0x10008);po=struct.unpack_from('<I',menu,4)[0]
    rows=(30,31) if ultimate else (8,9,11);pals={r:menu[po+r*32:po+(r+1)*32] for r in rows};probe=pals[rows[0]]
    def palette_offset(row):return (480+row//16)*2048+(row%16)*32
    paloff=palette_offset(rows[0])
    if ultimate:
        from scripts.prepare_shibuki_ultimate_save_ui import render
        expected=rgba(render(menu,tex,mask))
    else:expected=rgba(icon(menu,tex,mask,arm))
    expected=expected.crop(expected.getbbox())
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t];k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x410,False,s['pid'])
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    def read(addr,size):
        buf=ctypes.create_string_buffer(size);got=ctypes.c_size_t()
        return buf.raw if k.ReadProcessMemory(h,addr,buf,size,ctypes.byref(got)) and got.value==size else b''
    out=new_run(ROOT,'ver_rin_nana','ultimate_save_live' if ultimate else 'fourth_save_live');expected.save(out/'expected.png');candidates=set();found=[];resident=[]
    try:
        address=0
        while address<0x100000000:
            reg=Region()
            if not k.VirtualQueryEx(h,address,ctypes.byref(reg),ctypes.sizeof(reg)):break
            start=reg.base or 0;end=start+reg.size
            if end<=address:break
            if reg.state==0x1000 and not reg.protect&0x100 and reg.protect&0xff in (2,4,8,0x20,0x40,0x80):
                for off in range(start,end,1048576):
                    blob=read(off,min(1048576+32,end-off));pos=blob.find(probe)
                    while pos>=0:
                        base=off+pos-paloff
                        if base>0:candidates.add(base)
                        pos=blob.find(probe,pos+1)
            address=end
        for addr in candidates:
            raw=read(addr,1048576)
            if len(raw)!=1048576 or any(raw[palette_offset(r):palette_offset(r)+32]!=v for r,v in pals.items()):continue
            # LOAD's sprite page persists through gameplay and F3. A correct
            # disc/menu alone does not prove that its live texture is current.
            atlas=b''.join(raw[(256+y)*2048+1792:(256+y)*2048+1920] for y in range(256))
            mismatch=sum(a!=b for a,b in zip(atlas,tex))
            resident.append({'vram_host_address':addr,'atlas_sha256':sha256(atlas),'atlas_matches_disc':atlas==tex,'different_atlas_bytes':mismatch})
            (out/f'vram_candidate_{addr}.bin').write_bytes(raw)
            for page in (0,240):
                screen=framebuffer(raw,0,page);matches=match_sprite(screen,expected)
                screen.save(out/f'candidate_{addr}_{page}.png')
                if matches:
                    screen.save(out/f'framebuffer_{page}.png');(out/'vram.bin').write_bytes(raw)
                    found.extend({'vram_host_address':addr,'page_y':page,**q} for q in matches)
    finally:k.CloseHandle(h)
    report={'session':str(session),'pid':s['pid'],'build_sha256':s['bin_sha256'],'armor_mask':mask,'arm_type':arm,'palette_rows':list(rows),
            'disc_resource_sha256':{n:sha256(v) for n,v in assets.items()},
            'expected_sha256':digest(out/'expected.png'),'resident_atlases':resident,'matches':found,
            'verified':bool(found) and any(q['atlas_matches_disc'] and any(h['vram_host_address']==q['vram_host_address'] for h in found) for q in resident),'process_memory_written':False,'keys_sent':False,
            'scope':'current save/load icon opaque pixels and palettes; not all equipment combinations or capsule effects'}
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'verified':report['verified'],'matches':found,'resident_atlases':resident}))
    if not report['verified']:raise RuntimeError('Save icon or persistent atlas differs; captured evidence retained')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--mask',type=int,choices=range(16),default=15);p.add_argument('--arm',type=int,choices=(1,2),default=2);a=p.parse_args();main(a.session,a.build,a.mask,a.arm)
