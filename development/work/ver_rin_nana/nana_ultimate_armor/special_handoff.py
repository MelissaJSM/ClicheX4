import ctypes,gzip,json,sys
from ctypes import wintypes
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.prepare_nana_fourth_pilot import entry,write
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.capture_poc_memory import Region
import scripts.emulator_session as emulator
D=R/'work/ver_rin_nana/nana_ultimate_armor'
B=R/'out/ver_rin_nana/nana_ultimate_special_20261104T113013217294Z'
session=R/'work/ver_rin_nana/emulator_sessions/20261104T113522156087Z'
s=json.loads((session/'session.local.json').read_text('utf8'))
emulator.EMULATOR=R/'work/ver_rin_nana/emulator/ePSXe.exe'
emulator.checked_window(s['pid'])
assert digest(Path(s['executable']))==s['exe_sha256'] and digest(B/'rin_nana.bin')==s['bin_sha256']
k=ctypes.WinDLL('kernel32');k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t]
h=k.OpenProcess(0x410,False,s['pid']);assert h
try:
    def read(address,size):
        buf=ctypes.create_string_buffer(size);got=ctypes.c_size_t()
        return buf.raw[:got.value] if k.ReadProcessMemory(h,address,buf,size,ctypes.byref(got)) else b''
    anchor=bytes.fromhex('150001000c0001922a0001930c00019436000100');address=0;candidates=set()
    while address<0x100000000:
        region=Region()
        if not k.VirtualQueryEx(h,address,ctypes.byref(region),ctypes.sizeof(region)):break
        start=region.base or 0;end=start+region.size
        if end<=address:break
        if region.state==0x1000 and not region.protect&0x100 and region.protect&0xff in(2,4,8,0x20,0x40,0x80):
            for off in range(start,end,1048576):
                blob=read(off,min(1048640,end-off));pos=blob.find(anchor)
                while pos>=0:
                    candidates.add(off+pos-0x11a2f8);pos=blob.find(anchor,pos+1)
        address=end
    arc=(B/'PL02_U.ARC').read_bytes();valid=[]
    for candidate in candidates:
        data=read(candidate,0x200000)
        if all(data[pos:pos+len(entry(arc,t))]==entry(arc,t) for t,pos in((2,1542560),(3,1734644),(9,1540096))):valid.append((candidate,data))
    assert len(valid)==1,valid
    ram_host,ram=valid[0];loaded={}
    for t,pos in((2,1542560),(3,1734644),(9,1540096)):
        a=entry(arc,t);assert ram[pos:pos+len(a)]==a
        loaded[str(t)]=dict(offset=pos,sha256=sha256(a),matches=True)
    state=gzip.decompress((R/'work/ver_rin_nana/checkpoints/nana_ultimate_special_v1/SLUS_005.61.000').read_bytes())
    player_same=ram[0x1418c8:0x1418c8+228]==state[442+0x1418c8:442+0x1418c8+228]
    saved=json.loads((D/'special_saved_progress.json').read_text('utf8'));backup=R/saved['backup'];records=json.loads((backup/'backup.json').read_text('utf8'));cards=[q for q in records if '/memcards/'in q['path']];cards_same=all(digest(R/q['path'])==q['sha256']for q in cards)
    handoff=dict(build=B.relative_to(R).as_posix(),sha256=s['bin_sha256'],session=session.relative_to(R).as_posix(),pid=s['pid'],ram_host=ram_host,loaded_arc_entries=loaded,loaded_arc_verified=True,latest_post_aiming_laser_progress_restored=True,player_record_identical=player_same,cards_preserved=cards_same,checkpoint='work/ver_rin_nana/checkpoints/nana_ultimate_special_v1/refresh.json',menu_screenshot=(session/'20261104T113530616388Z.png').relative_to(R).as_posix(),special_actual_frames_verified=[],special_user_accepted=False,process_memory_written=False,automatic_input_stopped=True,control_handed_to_user=True,runtime_attempt='Separate historical test state with isolated cards; charge input produced no verified new target frames; no success inferred',runtime_evidence='work/ver_rin_nana/armor_capture/20261104T113324534717Z/verification.local.json',user_will_obtain_double_cyclone=True)
    write(D/'special_handoff.json',handoff)
    for name in('current_build.json','nana_ultimate_candidate.json'):
        p=R/'projects/ver_rin_nana'/name;c=json.loads(p.read_text('utf8'));assert c['sha256']=='0d32b509c59a07febf875e286a90555f7437cdbb4b3c4349fa532c8eeb75e121';c.update(build=handoff['build'],cue=handoff['build']+'/rin_nana.cue',sha256=handoff['sha256'],current_session=handoff['session'],emulator_pid=s['pid'],stage='SPECIAL_REVIEW',next_scope='User obtains and tests Double Cyclone; then Rising Fire/Frost9 armor refs',runtime_verified=False,ultimate_ceremony_user_accepted=True,ultimate_victory_edge_user_accepted=True,ultimate_special_applied=True,ultimate_special_user_accepted=False,ultimate_special_loaded_arc_verified=True,ultimate_special_actual_frames_verified=[],ultimate_special_handoff=(D/'special_handoff.json').relative_to(R).as_posix(),ultimate_special_report='docs/NANA_ULTIMATE_SPECIALS.md',cumulative_ultimate_references=142,automatic_input_stopped=True,control_handed_to_user=True,user_will_obtain_double_cyclone=True)
        for key,value in(('current_build',handoff['build']),('current_sha256',handoff['sha256']),('active_bin_sha256',handoff['sha256'])):
            if key in c:c[key]=value
        write(p,c)
    s.update(save_state_loaded=True,save_state_sha256=digest(R/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000'),loaded_screen='Weapon Get Aiming Laser',graphics_cache_refreshed=True);write(session/'session.local.json',s);print(json.dumps(handoff))
finally:k.CloseHandle(h)
