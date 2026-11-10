"""검증된 작업용 ePSXe에 일반 키 입력을 재생하고 읽기 전용 상태를 기록한다."""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.emulator_session import checked_window, Input, KeyInput
from scripts.project import new_run, write_json, digest
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank
from src.epsxe_state import framebuffer

KEYS = {'left': (0x4b, 9), 'right': (0x4d, 9), 'up': (0x48, 9),
        'down': (0x50, 9), 'z': (0x2c, 8), 'x': (0x2d, 8),
        's': (0x1f, 8), 'd': (0x20, 8), 'w': (0x11, 8), 'e': (0x12, 8),
        'r': (0x13, 8), 't': (0x14, 8), 'q': (0x10, 8), 'y': (0x15, 8),
        'c': (0x2e, 8), 'v': (0x2f, 8), 'f': (0x21, 8), 'start': (0x2f, 8)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],default='ver_buki_riko')
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    if args.project=='ver_rin_nana':
        import winreg
        import scripts.emulator_session as session_control
        session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as reg:
            pad=list(map(int,winreg.QueryValueEx(reg,'Pad1')[0].split(',')))
        if len(pad)!=16:raise ValueError('Incomplete pad mapping')
        for name,index in {'left':0,'right':1,'up':2,'down':3,'special':4,'dash':5,'jump':6,'fire':7,'start':12}.items():
            sc=pad[index]
            if not 1<=sc<=255:raise ValueError('Invalid scan code')
            KEYS[name]=(sc&127,8|int(bool(sc&128)))
    session = args.session.resolve()
    if not session.is_relative_to(ROOT / 'work' / args.project / 'emulator_sessions'):
        raise ValueError('Unexpected session')
    record = json.loads((session / 'session.local.json').read_text())
    plan = json.loads(args.plan.read_text())
    duration = plan['seconds']
    if not .1 <= duration <= 30:
        raise ValueError('Playback duration must be .1..30 seconds')
    for key, begin, end in plan['keys']:
        if key not in KEYS or not 0 <= begin < end <= duration:
            raise ValueError('Invalid key interval')
    user, window = checked_window(record['pid'])
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = None
    def read(address, length):
        buffer = ctypes.create_string_buffer(length)
        count = ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle, address, buffer, length, ctypes.byref(count)) or count.value != length:
            raise OSError('Short process read')
        return buffer.raw
    def send(key, down):
        scan, flags = KEYS[key]
        event = Input(); event.type = 1
        event.data.key = KeyInput(0, scan, flags | (0 if down else 2), 0, 0)
        if user.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) != 1:
            raise OSError('Input failed')
    out = new_run(ROOT, args.project, 'input_playback')
    held = set(); trace = []; last_image = -1; failure = None
    try:
        if args.baseline:
            prior = json.loads(args.baseline.read_text())
            if prior['pid'] != record['pid'] or prior['modified_bin_sha256'] != record['bin_sha256']:
                raise ValueError('Baseline/session mismatch')
            build = Path(prior['source_build'])
            manifest = json.loads((build / 'manifest.json').read_text())
            arc_path = build / 'modified.arc'
            if digest(arc_path) != manifest['modified_archive_sha256']:
                raise ValueError('Changed archive')
            arc = arc_path.read_bytes()
            entry = next(e for e in psx_arc(arc) if e['type'] == '0x2')
            gfx = arc[entry['offset']:entry['offset'] + entry['size']]
            bank = graphics_bank(gfx, 0)
            handle = kernel.OpenProcess(0x410, False, record['pid'])
            if not handle: raise OSError('Read-only process open failed')
            base = prior['ram_host_address']; video = prior['vram_host_address']
            player = read(base + 0x1418c8, 0xe4)
            pointer = struct.unpack_from('<I', player, 0x38)[0] & 0x1fffff
            valid_banks=[bank,graphics_bank(gfx,1)] if manifest.get('bank1_frame_inputs') else [bank]
            if player[2] != 1 or not any(read(base + pointer, b['end'] - b['base']) == gfx[b['base']:b['end']] for b in valid_banks):
                raise ValueError('Current RAM does not match patched Zero bank')
        user.ShowWindowAsync(window, 9); user.SetForegroundWindow(window); time.sleep(.15)
        start = time.monotonic()
        while time.monotonic() - start < duration:
            elapsed = time.monotonic() - start
            if user.GetForegroundWindow() != window:
                raise RuntimeError('Focus changed; input stopped')
            wanted = {key for key, begin, end in plan['keys'] if begin <= elapsed < end}
            for key in held - wanted: send(key, False)
            for key in wanted - held: send(key, True)
            held = wanted
            if handle:
                player = read(base + 0x1418c8, 0xe4)
                state = [player[2], player[4], player[5], player[0x17], player[0x47],
                    *[round(struct.unpack_from('<i', player, offset)[0] / 65536, 3) for offset in (8, 12)],
                    player[0x5c], player[0x4a], player[0x89], struct.unpack_from('<H', player, 0x7c)[0]]
                if not trace or trace[-1][1:] != state: trace.append([round(elapsed, 5), *state])
                if elapsed - last_image >= .3:
                    raw = read(video, 1048576)
                    framebuffer(raw, 0, 0).save(out / f'page0_{elapsed:06.2f}.png')
                    framebuffer(raw, 0, 256).save(out / f'page256_{elapsed:06.2f}.png')
                    last_image = elapsed
            time.sleep(.005)
    except BaseException as error:
        failure = repr(error)
        raise
    finally:
        for key in held: send(key, False)
        if handle: kernel.CloseHandle(handle)
        write_json(out / 'playback.local.json', {'session': str(session), 'baseline': str(args.baseline),
            'plan': plan, 'effective_key_mapping':{name:KEYS[name] for name,_,_ in plan['keys']},'error': failure, 'process_memory_written': False,
            'collision_flags_player_offset': '0x89',
            'columns': ['seconds', 'character', 'state', 'action', 'animation', 'frame', 'x', 'y',
                        'hp', 'wall_climbable', 'collision_flags', 'held_input'], 'rows': trace})
        print(json.dumps({'output': str(out), 'error': failure,
            'animations': sorted({r[4] for r in trace}), 'last': trace[-1] if trace else None}))


if __name__ == '__main__': main()
