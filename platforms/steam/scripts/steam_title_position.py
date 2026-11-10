"""Align the JP title's settled and fade positions in a normally launched game.

The on-disk executable must be original. A game UI field and one branch selecting
the fade X coordinate are adjusted. Steam startup/authentication code is untouched.
Both adjustments disappear when the process exits.
When the corresponding loading assets are installed, their strictly bounded
rectangle tables and Japanese logo colors are connected in the same session.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

from release_paths import ROOT
from scripts.steam_runtime import EXE,game_window
from src.steam_executable import ORIGINAL_SHA256,JP_TITLE_OFFSET

ADDRESS=0xf71738
CONSUMER=0x9e23b9
FADE_START=0xa62c0f
FADE_BRANCH=0xa62c12
FADE_ORIGINAL=bytes.fromhex('83f80175046a78eb056890000000')
FADE_ALIGNED=bytes.fromhex('83f801eb046a78eb056890000000')


def loading_patches(original,check_installed=True):
    allowed_files={'nativeDX10/X4/romPC/load.arc','nativeDX10/X4/romPC/load_eng.arc'}
    spec=None
    matches=[]
    for filename in ('dialogue_display_patch.json','menu_runtime_patch.json','loading_runtime_patch.json'):
        path=ROOT/'work/steam_port_20261109'/filename
        if not path.exists():continue
        candidate=json.loads(path.read_text(encoding='utf8'))
        if set(candidate['installed_requirements'])!=allowed_files:raise ValueError('Unrecognized loading target set')
        candidate_matches=[hashlib.sha256((EXE.parent/rel).read_bytes()).hexdigest()==expected for rel,expected in candidate['installed_requirements'].items()]
        if check_installed and any(candidate_matches) and not all(candidate_matches):raise ValueError('Incomplete regional loading installation')
        if not check_installed or all(candidate_matches):
            spec=candidate;matches=candidate_matches;break
    if spec is None:return []
    allowed={(0x1ae0f10,0x16dfd10,72),(0x1ae0f58,0x16dfd58,72),(0xf5eda8,0xb5e1a8,64)}
    rows=[(96,96,0,8,1,1),(184,192,112,5,2,2),(232,192,117,4,2,3),
          (16,192,8,5,1,0),(16,192,203,5,1,0),(96,192,13,3,1,0),
          (16,208,32,6,1,0),(120,208,121,3,1,0),(120,208,137,3,1,0)]
    wanted_table=b''.join(struct.pack('<hhBBBB',*r)for r in rows)
    result=[]
    for patch in spec['patches']:
        before,after=bytes.fromhex(patch['before_hex']),bytes.fromhex(patch['after_hex'])
        key=(patch['address'],patch['file_offset'],len(before))
        if key not in allowed or len(after)!=len(before):raise ValueError('Loading patch address/length is not allowed')
        allowed.remove(key)
        if original[key[1]:key[1]+key[2]]!=before:raise ValueError('Loading original mismatch')
        expected=wanted_table if len(before)==72 else original[0xb5e3a8:0xb5e3e8]
        if after!=expected:raise ValueError('Loading patch contents are not approved display values')
        result.append((patch['name'],key[0],before,after))
    if allowed:raise ValueError('Incomplete loading data patch')
    menu=spec.get('menu_layout_patches',[])
    if len(menu)>1:raise ValueError('Unrecognized menu patch count')
    for patch in menu:
        before,after=bytes.fromhex(patch['before_hex']),bytes.fromhex(patch['after_hex'])
        if (patch['address'],patch['file_offset'],len(before),len(after))!=(0xf7fba4,0xb7efa4,32,32):
            raise ValueError('Unrecognized menu display table')
        expected=bytes.fromhex('20038004a000100130024005d0ff01002004a0038000100130024005d0ff0000')
        if before!=expected or original[0xb7efa4:0xb7efc4]!=before:raise ValueError('Original Continue table differs')
        wanted=bytearray(before);wanted[0]=wanted[16]=84;wanted[11]=wanted[27]=118
        if after!=bytes(wanted):raise ValueError('Unrecognized Continue coordinates or footer')
        result.append((patch['name'],patch['address'],before,after))
    return result if all(matches) or not check_installed else []


def dialogue_patches():
    from src.steam_dialogue import runtime_patches
    path=ROOT/'work/steam_port_20261109/dialogue_runtime_patch.json'
    if not path.exists():return []
    spec=json.loads(path.read_text(encoding='utf8'))
    allowed={'nativeDX10/X4/romPC/'+name+suffix+'.arc'
             for name in ('load','pl00','pl01','pl02') for suffix in ('','_eng')}
    if set(spec['installed_requirements'])!=allowed:raise ValueError('Unrecognized dialogue target set')
    matches=[hashlib.sha256((EXE.parent/rel).read_bytes()).hexdigest()==expected
             for rel,expected in spec['installed_requirements'].items()]
    if any(matches) and not all(matches):raise ValueError('Incomplete regional dialogue installation')
    wanted=runtime_patches()
    actual=[(p['name'],p['address'],bytes.fromhex(p['before_hex']),bytes.fromhex(p['after_hex'])) for p in spec['patches']]
    if actual!=wanted:raise ValueError('Unrecognized dialogue instruction changes')
    return wanted if all(matches) else []


def apply(restore=False):
    original=EXE.read_bytes()
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA256:raise ValueError('Original executable required')
    extra_patches=loading_patches(original)
    glyph_patches=dialogue_patches()
    _,(_,pid,title)=game_window()
    if title!='Mega Man X Legacy Collection / ROCKMAN X ANNIVERSARY COLLECTION':raise ValueError('Game has not reached its normal window')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.WriteProcessMemory.argtypes=kernel.ReadProcessMemory.argtypes
    kernel.VirtualProtectEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
    kernel.FlushInstructionCache.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x438,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    def read(address,n):
        buf=ctypes.create_string_buffer(n);done=ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle,address,buf,n,ctypes.byref(done)) or done.value!=n:raise ctypes.WinError(ctypes.get_last_error())
        return buf.raw
    def write(address,data,code=False):
        old_protection=wintypes.DWORD();done=ctypes.c_size_t()
        if not kernel.VirtualProtectEx(handle,address,len(data),0x40 if code else 4,ctypes.byref(old_protection)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            buf=ctypes.create_string_buffer(data)
            if not kernel.WriteProcessMemory(handle,address,buf,len(data),ctypes.byref(done)) or done.value!=len(data):
                raise ctypes.WinError(ctypes.get_last_error())
            if code and not kernel.FlushInstructionCache(handle,address,len(data)):raise ctypes.WinError(ctypes.get_last_error())
            if read(address,len(data))!=data:raise ValueError('Title position read-back failed')
        finally:
            ignored=wintypes.DWORD()
            if not kernel.VirtualProtectEx(handle,address,len(data),old_protection.value,ctypes.byref(ignored)):
                raise ctypes.WinError(ctypes.get_last_error())
    before=None;changed=False;target=struct.pack('<h',120 if restore else 144)
    try:
        if read(0x400000,2)!=b'MZ':raise ValueError('Unrecognized module base')
        if read(CONSUMER,8)!=bytes.fromhex('0fbf04753817f700'):raise ValueError('Unrecognized native title coordinate consumer')
        before=read(ADDRESS,96);expected=original[JP_TITLE_OFFSET:JP_TITLE_OFFSET+96]
        if before[2:]!=expected[2:] or before[:2] not in (struct.pack('<h',120),struct.pack('<h',144)):
            raise ValueError('Unexpected native title initialization table')
        fade_before=read(FADE_START,len(FADE_ORIGINAL))
        if fade_before not in (FADE_ORIGINAL,FADE_ALIGNED):raise ValueError('Unexpected native title fade position code')
        fade_target=FADE_ORIGINAL if restore else FADE_ALIGNED
        planned=[(ADDRESS,before[:2],target,False),(FADE_BRANCH,fade_before[3:4],fade_target[3:4],True)]
        for name,address,old,new in extra_patches:
            current=read(address,len(old))
            if current not in (old,new):raise ValueError('Unexpected loading runtime data: '+name)
            planned.append((address,current,old if restore else new,False))
        for name,address,old,new in glyph_patches:
            current=read(address,len(old))
            if current not in (old,new):raise ValueError('Unexpected dialogue instructions: '+name)
            planned.append((address,current,old if restore else new,True))
        applied=[]
        try:
            for address,old,new,is_code in planned:
                if old==new:continue
                applied.append((address,old,is_code));write(address,new,is_code);changed=True
            if read(ADDRESS,96)!=target+before[2:] or read(FADE_START,len(fade_target))!=fade_target:
                raise ValueError('Title alignment protection check failed')
        except Exception:
            for address,old,is_code in reversed(applied):write(address,old,is_code)
            raise
        after=read(ADDRESS,96)
    finally:kernel.CloseHandle(handle)
    if hashlib.sha256(EXE.read_bytes()).hexdigest()!=ORIGINAL_SHA256:raise ValueError('Executable changed externally')
    return {'pid':pid,'address':hex(ADDRESS),'before_x':struct.unpack_from('<h',before)[0],
            'after_x':struct.unpack_from('<h',after)[0],'changed':changed,'other_title_fields_preserved':True,
            'executable_original_hash_verified':True,'game_rendering_code_changed':not restore,
            'steam_startup_or_authentication_code_changed':False,'fade_x':120 if restore else 144,
            'fade_branch_address':hex(FADE_BRANCH),
            'loading_data_patches':[name for name,_,_,_ in extra_patches],
            'dialogue_code_patches':[name for name,_,_,_ in glyph_patches],
            'process_memory_readback_verified':True,'screen_verified':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--restore',action='store_true')
    p.add_argument('--wait',type=float,default=0);args=p.parse_args()
    if not 0<=args.wait<=30:raise ValueError('Wait must be 0..30 seconds')
    deadline=time.monotonic()+args.wait
    while True:
        try:report=apply(args.restore);break
        except (ValueError,OSError):
            if time.monotonic()>=deadline:raise
            time.sleep(.5)
    out=ROOT/'work/steam_port_20261109/runtime'/f'title_position_{report["pid"]}.json'
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
