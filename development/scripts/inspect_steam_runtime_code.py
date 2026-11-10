"""Read the verified running game's executable code sections without any writes/input."""
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.steam_runtime import game_window,EXE


def main():
    _,(_,pid,title)=game_window()
    raw=EXE.read_bytes();pe=struct.unpack_from('<I',raw,60)[0]
    count=struct.unpack_from('<H',raw,pe+6)[0];optional=struct.unpack_from('<H',raw,pe+20)[0]
    base=struct.unpack_from('<I',raw,pe+24+28)[0]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x410,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    out=ROOT/'work/steam_port_20261109/runtime/code'
    out.mkdir(parents=True,exist_ok=True)
    report={'pid':pid,'title':title,'preferred_image_base':hex(base),'read_only':True,'sections':[]}
    try:
        header=ctypes.create_string_buffer(4096);got=ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle,base,header,4096,ctypes.byref(got)) or header.raw[:2]!=b'MZ':
            raise ValueError('Image not at verified preferred base; module discovery required')
        for i in range(count):
            pos=pe+24+optional+40*i
            name=raw[pos:pos+8].split(b'\0')[0].decode('ascii')
            size,rva,_,_=struct.unpack_from('<IIII',raw,pos+8)
            flags=struct.unpack_from('<I',raw,pos+36)[0]
            if not flags&0x20000000:continue
            data=bytearray(size);missing=[]
            for offset in range(0,size,4096):
                n=min(4096,size-offset);buf=ctypes.create_string_buffer(n)
                if kernel.ReadProcessMemory(handle,base+rva+offset,buf,n,ctypes.byref(got)) and got.value==n:
                    data[offset:offset+n]=buf.raw
                else:missing.append(hex(base+rva+offset))
            path=out/(name.strip('.')+'.bin');path.write_bytes(data)
            report['sections'].append({'name':name,'base':hex(base+rva),'size':size,'sha256':hashlib.sha256(data).hexdigest(),'missing_pages':missing,'path':str(path.relative_to(ROOT))})
    finally:kernel.CloseHandle(handle)
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
