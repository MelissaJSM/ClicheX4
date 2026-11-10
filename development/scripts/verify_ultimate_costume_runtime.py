"""얼티밋 의상 교환을 실제 RAM·VRAM에서 읽기 전용으로 검증한다.

한 번에 pre/post 중 현재 상태 하나를 확인한다. 같은 PID로 두 번 실행하면
동일 세션 전/후 증거를 남길 수 있다. 키 입력·포커스·메모리/세이브 쓰기는 없다.
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

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.capture_poc_memory import Region
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.ultimate_costume_renderer import START, END, emit, off
from scripts.ultimate_costume_swap_ui import SAVE_BEGIN, SAVE_END, save_code
from src.epsxe_state import framebuffer, match_sprite
from src.psx_disc import file_hash
from src.psx_player import bank_offsets, composition_frame, compose_indices, decode_stream, graphics_bank
from src.psx_ui_atlas import local_composition

WORK = ROOT / 'work/ultimate_costume_swap_20261105'
PLAYER, BUFFER = 0x1418C8, 0x16DEA8
ULTIMATE, OWNED = 0x1721F7, 0x172207
ANCHOR_OFFSET = 0x11A2F8
ANCHOR = bytes.fromhex('150001000c0001922a0001930c00019436000100')
EMULATOR_SHA = 'a266ee19bbeba0da38ffbaa8b02b89fe2524af7a45a13ea9ff37feab7423986d'
CODE_RANGES = ((START, END), (SAVE_BEGIN, SAVE_END), (0x8001BE60, 0x8001BE64))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def clut_offset(code):
    return (code >> 6) * 2048 + (code & 63) * 32


def visual_mask(ultimate, owned, player_armor, frame):
    if not ultimate:
        return player_armor
    return 15 if owned == 0 or 217 <= frame <= 230 else 0


def load_assets(args):
    path = args.bin.resolve()
    require(path.is_relative_to((ROOT / 'out' / args.project).resolve()), 'BIN outside selected project')
    require(file_hash(path) == args.expected_sha256, 'BIN SHA-256 mismatch')
    manifest = json.loads(path.with_name('manifest.json').read_text('utf8'))
    require(manifest['task'] == 'ultimate_costume_swap' and manifest['project'] == args.project,
            'Not the reviewed costume swap build')
    require(manifest['modified_bin']['sha256'] == args.expected_sha256, 'Manifest BIN differs')
    resources, _ = read_disc(path, ('SLUS_005.61', 'PL02_U.ARC'))
    exe, arc = resources['SLUS_005.61'], resources['PL02_U.ARC']
    proposal_path = (ROOT / manifest['proposal']).resolve()
    require(proposal_path.is_relative_to(WORK.resolve()), 'Unexpected proposal location')
    proposal = json.loads(proposal_path.read_text('utf8'))
    for name, data in resources.items():
        require(sha(data) == proposal['files'][name]['sha256'], 'Disc differs from prepared ' + name)
    require(exe[off(START):off(END)] == emit(), 'Wrong gameplay display function')
    require(exe[off(SAVE_BEGIN):off(SAVE_END)] == save_code(), 'Wrong save display function')
    es = {kind: entry(arc, kind) for kind in (2, 3, 9)}
    bank = graphics_bank(es[2], 0, allow_bank_aliases=True)
    return path, manifest, exe, arc, es, bank


class Reader:
    """Provided 32-bit ePSXe only; handle cannot write process memory."""
    def __init__(self, pid, project):
        self.kernel = k = ctypes.WinDLL('kernel32', use_last_error=True)
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        k.VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                    ctypes.POINTER(Region), ctypes.c_size_t]
        k.VirtualQueryEx.restype = ctypes.c_size_t
        k.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = k.OpenProcess(0x410, False, pid)
        if not self.handle:
            raise OSError(ctypes.get_last_error(), 'Cannot open read-only ePSXe handle')
        try:
            buf = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(buf))
            require(k.QueryFullProcessImageNameW(self.handle, 0, buf, ctypes.byref(size)),
                    'Cannot authenticate process image')
            self.executable = Path(buf.value).resolve()
            allowed = [ROOT / 'ePSXe2018/ePSXe.exe',
                       ROOT / 'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator/ePSXe.exe']
            if project == 'ver_rin_nana':
                allowed = [ROOT / 'work/ver_rin_nana/emulator/ePSXe.exe']
            require(self.executable in [p.resolve() for p in allowed] and
                    file_hash(self.executable) == EMULATOR_SHA, 'Unexpected emulator path/hash')
        except Exception:
            self.close()
            raise

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None

    def read(self, address, length, optional=False):
        buf = ctypes.create_string_buffer(length)
        got = ctypes.c_size_t()
        ok = self.kernel.ReadProcessMemory(self.handle, address, buf, length, ctypes.byref(got))
        if not ok or got.value != length:
            if optional:
                return b''
            raise OSError('ReadProcessMemory failed: ' + hex(address))
        return buf.raw

    def find(self, needles):
        """Existing Region/anchor locator, bounded to this 32-bit process."""
        found = {name: set() for name in needles}
        address, scanned = 0, 0
        overlap = max(len(data) for data, _ in needles.values())
        while address < 0x100000000:
            region = Region()
            if not self.kernel.VirtualQueryEx(self.handle, address, ctypes.byref(region), ctypes.sizeof(region)):
                break
            start = region.base or 0
            end = start + region.size
            if end <= address:
                break
            if (region.state == 0x1000 and not region.protect & 0x100 and
                    region.protect & 0xff in (2, 4, 8, 0x20, 0x40, 0x80)):
                for offset in range(start, min(end, 0x100000000), 1048576):
                    blob = self.read(offset, min(1048576 + overlap, end - offset), optional=True)
                    scanned += len(blob)
                    for name, (needle, relative) in needles.items():
                        pos = blob.find(needle)
                        while pos >= 0:
                            if offset + pos >= relative:
                                found[name].add(offset + pos - relative)
                            pos = blob.find(needle, pos + 1)
            address = end
        return found, scanned


def verify_ram(ram, exe, es, bank):
    require(len(ram) == 0x200000 and ram[ANCHOR_OFFSET:ANCHOR_OFFSET + len(ANCHOR)] == ANCHOR,
            'RAM anchor mismatch')
    codes = []
    for start, end in CODE_RANGES:
        actual = ram[start & 0x1fffff:end & 0x1fffff]
        expected = exe[off(start):off(end)]
        require(actual == expected, 'Resident executable mismatch at ' + hex(start))
        codes.append({'start': hex(start), 'end': hex(end), 'bytes': len(actual), 'sha256': sha(actual)})
    player = ram[PLAYER:PLAYER + 228]
    require(player[2] == 0 and ram[ULTIMATE] == 1, 'Expected active Ultimate X player')
    assets = {}
    for kind in (2, 3, 9):
        at = ram.find(es[kind])
        require(at >= 0, 'PL02 resident entry missing: ' + str(kind))
        require(ram.find(es[kind], at + 1) < 0, 'Ambiguous resident entry: ' + str(kind))
        assets[str(kind)] = {'ram_offset': at, 'size': len(es[kind]), 'sha256': sha(es[kind])}
    gp = 0x80000000 + assets['2']['ram_offset'] + bank['base']
    cp = 0x80000000 + assets['3']['ram_offset'] + bank_offsets(es[3])[0]
    require(struct.unpack_from('<II', player, 0x38) == (gp, cp), 'Player is not using PL02 bank0')
    return codes, assets, (gp, cp)


def decoded_frame(es, bank, number):
    require(number < len(bank['frames']), 'Unsupported current graphics frame')
    frame = bank['frames'][number]
    require(1 <= frame['tile_count'] <= 32, 'Current frame is blank or exceeds 32-tile buffer')
    raw = decode_stream(es[2], frame['offset'], frame['limit'], frame['tile_count'] * 128).data
    return frame, raw


def gpu_upload(vram, tiles):
    result = bytearray()
    for first in range(0, tiles, 16):
        width = min(tiles - first, 16) * 8
        for y in range(16):
            at = (first // 16 * 16 + y) * 2048 + 640
            result.extend(vram[at:at + width])
    return bytes(result)


def color_image(indices, colors):
    table = np.array([[(int(word) >> shift & 31) * 255 // 31 for shift in (0, 5, 10)] +
                      [0 if n % 16 == 0 else 255] for n, word in enumerate(colors)], np.uint8)
    return Image.fromarray(table[indices])


def compose(raw, tiles, parts, number, mask, arm_type, vram, base_clut):
    canvas = Image.new('RGBA', (384, 384))
    layers = []
    for bit, bank in ((0, 0), (8, 8), (1, 5), (4, 7), (2, 6)):
        if bit and not mask & bit:
            continue
        comp = composition_frame(parts, bank, number)
        if not comp['parts']:
            continue
        code = base_clut if bank == 0 else 0x7844 if bank == 7 and arm_type == 2 else 0x7843
        if bank:
            comp = local_composition(comp)
        data, size, bounds, _ = compose_indices(raw, tiles, comp, allowed_cluts={0, 1, 2, 3})
        array = np.frombuffer(data, np.uint8).reshape(size[1], size[0])
        rows = 4 if bank == 0 else 1
        colors = b''.join(vram[clut_offset(code + row):clut_offset(code + row) + 32]
                          for row in range(rows))
        image = color_image(array, struct.unpack('<' + str(rows * 16) + 'H', colors))
        canvas.alpha_composite(image, (bounds[0] + 160, bounds[1] + 160))
        layers.append({'bank': bank, 'parts': len(comp['parts']), 'clut': hex(code),
                       'palette_sha256': sha(colors), 'part_cluts_preserved': bank == 0})
    return canvas, layers


def sample_key(player, ultimate, owned):
    return (player[2], player[0x15], player[0x17], player[0x38:0x44], player[0x47],
            player[0xa7], player[0xb8], ultimate, owned)


def main(args):
    require(0 < args.seconds <= 30, 'Observation window must be 0..30 seconds')
    path, manifest, exe, arc, es, bank = load_assets(args)
    metadata = {'project': args.project, 'bin': path.relative_to(ROOT).as_posix(),
                'bin_sha256': args.expected_sha256, 'exe_sha256': sha(exe), 'pl02_sha256': sha(arc),
                'exe_changed_bytes': manifest['checks']['exe_changed_bytes'],
                'exe_allocated_bytes_checked': sum(b - a for a, b in CODE_RANGES),
                'input_sent': False, 'focus_changed': False, 'process_memory_written': False,
                'save_files_written': False, 'fresh_boot_proven': False}
    if args.prepare_only:
        print(json.dumps({**metadata, 'prepared': True, 'process_opened': False})); return
    require(args.pid and args.expect and args.output, 'Runtime requires --pid, --expect, --output')
    output = args.output.resolve()
    require(output.is_relative_to(WORK.resolve()) and not output.exists(), 'Fresh task output required')
    output.mkdir(parents=True)
    report = {**metadata, 'pid': args.pid, 'expect': args.expect, 'passed': False,
              'limitation': 'Only the observed current frame is checked. Exact code/assets do not prove a fresh boot. '
                            'No keys or state changes are performed. A no-match during motion/occlusion is inconclusive.'}
    reader = None
    try:
        reader = Reader(args.pid, args.project)
        report['executable'] = str(reader.executable)
        report['process_open_rights'] = '0x410 (QUERY_INFORMATION | VM_READ)'
        candidates = {'ram': {args.ram_base} if args.ram_base is not None else set(),
                      'vram': {args.vram_base} if args.vram_base is not None else set()}
        scanned = 0
        needles = {}
        if args.ram_base is None:
            needles['ram'] = (ANCHOR, ANCHOR_OFFSET)
        if args.vram_base is None:
            needles['vram'] = (es[9][32:64], clut_offset(0x7843))
        if needles:
            found, scanned = reader.find(needles)
            candidates.update(found)
        valid = []
        for base in sorted(candidates['ram']):
            ram = reader.read(base, 0x200000, optional=True)
            try:
                codes, assets, pointers = verify_ram(ram, exe, es, bank)
                valid.append((base, ram, codes, assets, pointers))
            except (ValueError, struct.error):
                continue
        require(len(valid) == 1, 'No unique authenticated RAM: count=' + str(len(valid)))
        ram_base, ram, codes, assets, pointers = valid[0]
        report.update(ram_host_base=ram_base, code_ranges=codes, resident_entries=assets)
        number = ram[PLAYER + 0x47]
        frame, raw = decoded_frame(es, bank, number)
        if not candidates['vram']:
            width = min(frame['tile_count'], 16) * 8
            row = max(range(16), key=lambda y: len(set(raw[y * width:(y + 1) * width])))
            found, extra = reader.find({'vram': (raw[row * width:(row + 1) * width], row * 2048 + 640)})
            candidates.update(found); scanned += extra
        report.update(scanned_bytes=scanned, vram_candidates=sorted(candidates['vram']))
        require(candidates['vram'], 'VRAM not found; provide a current --vram-base')
        start = time.monotonic()
        attempts, last = 0, {}
        while time.monotonic() - start < args.seconds:
            player = reader.read(ram_base + PLAYER, 228)
            ultimate, owned = (reader.read(ram_base + at, 1)[0] for at in (ULTIMATE, OWNED))
            number = player[0x47]
            state = 'pre' if owned == 0 else 'post'
            last = {'frame': number, 'animation': player[0x17], 'ultimate': ultimate,
                    'persisted_armor': owned, 'player_armor': player[0xa7], 'state': state}
            if (state != args.expect or ultimate != 1 or player[2] != 0 or
                    struct.unpack_from('<II', player, 0x38) != pointers or
                    args.frame is not None and number != args.frame):
                time.sleep(.02); continue
            frame, expected = decoded_frame(es, bank, number)
            if reader.read(ram_base + BUFFER, len(expected)) != expected:
                time.sleep(.01); continue
            mask = visual_mask(ultimate, owned, player[0xa7], number)
            base_clut = struct.unpack_from('<H', player, 0x42)[0]
            if base_clut & 0x8000:
                base_clut = 0x7840
            for vram_base in sorted(candidates['vram']):
                vram = reader.read(vram_base, 0x100000, optional=True)
                attempts += 1
                if len(vram) != 0x100000 or gpu_upload(vram, frame['tile_count']) != expected:
                    continue
                again = reader.read(ram_base + PLAYER, 228)
                ug, ow = (reader.read(ram_base + at, 1)[0] for at in (ULTIMATE, OWNED))
                if sample_key(player, ultimate, owned) != sample_key(again, ug, ow):
                    continue
                image, layers = compose(expected, frame['tile_count'], es[3], number, mask,
                                        player[0xb8], vram, base_clut)
                other, _ = compose(expected, frame['tile_count'], es[3], number, mask ^ 15,
                                   player[0xb8], vram, base_clut)
                bbox = image.getbbox()
                if not bbox:
                    continue
                sprite = image.crop(bbox)
                matches, other_matches = [], []
                screens = {}
                for page in (0, 240):
                    screens[page] = framebuffer(vram, 0, page)
                    matches.extend({'page_y': page, **m} for m in match_sprite(screens[page], sprite))
                    if other.getbbox():
                        other_matches.extend({'page_y': page, **m} for m in
                                             match_sprite(screens[page], other.crop(other.getbbox())))
                discriminating = image.tobytes() != other.tobytes()
                last.update(visual_mask=mask, framebuffer_matches=matches,
                            alternate_mask_matches=other_matches, discriminating=discriminating)
                # Reject a selected image that is merely a subset of the
                # opposite costume on the same framebuffer page.
                alternate_pages = {m['page_y'] for m in other_matches}
                distinct_matches = [m for m in matches if m['page_y'] not in alternate_pages]
                last['discriminating_framebuffer_matches'] = distinct_matches
                if not distinct_matches or not discriminating:
                    continue
                sprite.save(output / 'expected_live_palette.png')
                if other.getbbox():
                    other.crop(other.getbbox()).save(output / 'alternate_mask.png')
                for page, screen in screens.items():
                    screen.save(output / f'framebuffer_{page}.png')
                (output / 'player.bin').write_bytes(player)
                (output / 'gpu_frame.bin').write_bytes(expected)
                final_ram = reader.read(ram_base, 0x200000)
                final_codes, final_assets, final_pointers = verify_ram(final_ram, exe, es, bank)
                require(final_codes == codes and final_assets == assets and final_pointers == pointers,
                        'Resident assets changed during observation')
                report.update(passed=True, vram_host_base=vram_base, observed=last,
                              base_clut=hex(base_clut), arm_type=player[0xb8],
                              layers=layers, tile_count=frame['tile_count'],
                              decoded_ram_and_gpu_sha256=sha(expected),
                              decoded_ram_matches=True, gpu_upload_matches=True,
                              resident_assets_still_exact=True,
                              sprite_world_bounds=[v - 160 for v in bbox],
                              framebuffer_matches=matches, alternate_mask_matches=other_matches,
                              discriminating_framebuffer_matches=distinct_matches,
                              display_verified_by='authenticated native code + exact texture + live CLUT/framebuffer')
                break
            if report['passed']:
                break
            time.sleep(.01)
        report.update(seconds=time.monotonic() - start, attempts=attempts, last_observed=last)
        require(report['passed'], 'No discriminating exact framebuffer match; see evidence.json')
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        if reader is not None:
            reader.close()
        (output / 'evidence.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf8')
        print(json.dumps({'passed': report['passed'], 'output': str(output),
                          'ram_base': report.get('ram_host_base'), 'vram_base': report.get('vram_host_base'),
                          'observed': report.get('observed', report.get('last_observed'))}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', choices=('ver_buki_riko', 'ver_rin_nana'), required=True)
    parser.add_argument('--bin', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--pid', type=int)
    parser.add_argument('--expect', choices=('pre', 'post'))
    parser.add_argument('--frame', type=int, help='선택: 대기 검증이면 현재 대기 프레임 번호를 지정')
    parser.add_argument('--ram-base', type=lambda value: int(value, 0))
    parser.add_argument('--vram-base', type=lambda value: int(value, 0))
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--output', type=Path)
    main(parser.parse_args())
