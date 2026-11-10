"""X 아머 파츠를 합쳐 실제 RAM/VRAM/프레임버퍼와 비교한다. 읽기 전용."""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import struct
import sys
import time
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import new_run, write_json, digest
from scripts.analyze_shibuki_armor import entries
from scripts.emulator_session import checked_window
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank, decode_stream, composition_frame
from src.psx_sprite_batch import canvas_from_parts
from src.epsxe_state import framebuffer, match_sprite
from src.psx_ui_atlas import local_composition


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],default='ver_buki_riko')
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--frames', default='0,115,116,117,118,119')
    parser.add_argument('--seconds', type=float, default=12)
    parser.add_argument('--ready-file', type=Path)
    parser.add_argument('--both-directions', action='store_true')
    args = parser.parse_args()
    if not .1 <= args.seconds <= 30:
        raise ValueError('Observation must be at most 30 seconds')
    prior = json.loads(args.evidence.read_text(encoding='utf-8'))
    build = Path(prior['source_build']).resolve()
    if not build.is_relative_to(ROOT / 'out' / args.project):
        raise ValueError('Unexpected build')
    manifest = json.loads((build / 'manifest.json').read_text(encoding='utf-8'))
    ultimate=manifest['task'] in ('ultimate_armor_shibuki','ultimate_armor_nana')
    arc_path=build/('PL02_U.ARC' if ultimate else 'modified.arc')
    if manifest['task'] not in ('fourth_armor_shibuki','ultimate_armor_shibuki','fourth_armor_nana','ultimate_armor_nana') or digest(arc_path) != manifest['modified_archive_sha256']:
        raise ValueError('Expected unchanged armor build')
    if prior['modified_bin_sha256'] != manifest['modified_bin']['sha256']:
        raise ValueError('Discovery refers to another build')
    if args.project=='ver_rin_nana':
        import scripts.emulator_session as session_control
        session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
    checked_window(prior['pid'])
    es = entries(arc_path.read_bytes())
    g, c, pal = es[2], es[3], es[9]
    bank = graphics_bank(g, 0, allow_bank_aliases=True)
    requested = {int(v) for v in args.frames.split(',')}
    if not requested or not requested <= set(range(len(bank['frames']))):
        raise ValueError('Invalid frame set')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x410, False, prior['pid'])
    if not handle:
        raise OSError('Cannot read verified emulator')

    def read(address, length):
        buf = ctypes.create_string_buffer(length)
        got = ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle, address, buf, length, ctypes.byref(got)) or got.value != length:
            return b''
        return buf.raw

    out = new_run(ROOT, args.project, 'armor_capture')
    cached = {}
    results = {}
    armor_results = {}
    samples = {}
    checked_ram_entries = []
    try:
        bases = prior.get('ram_candidates', [prior.get('ram_host_address')])
        videos = prior.get('vram_candidates', [prior.get('vram_host_address')])
        valid = []
        for base in bases:
            ram = read(base, 0x200000)
            if len(ram) != 0x200000:
                continue
            player = ram[0x1418c8:0x1418c8 + 0xe4]
            pointer = struct.unpack_from('<I', player, 0x38)[0] & 0x1fffff
            if player[2] == 0 and ram[pointer:pointer + bank['end'] - bank['base']] == g[bank['base']:bank['end']]:
                valid.append(base)
                checked_ram_entries.append({'ram_base': base, 'complete_entries_match': {str(t): ram.count(es[t]) == 1 for t in (2, 3, 9)}})
        if len(valid) != 1:
            raise ValueError('Expected one patched X RAM')
        base = valid[0]
        if args.ready_file:
            ready=args.ready_file.resolve()
            if not ready.is_relative_to(ROOT/'work') or ready.exists():raise ValueError('Fresh isolated ready file required')
            write_json(ready,{'pid':prior['pid'],'output':str(out),'ram_verified':True})
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            player = read(base + 0x1418c8, 0xe4)
            if len(player) != 0xe4:
                break
            n, mask, arm_type = player[0x47], player[0xa7], player[0xb8]
            if player[2] != 0 or n not in requested or mask > 15 or arm_type not in (1, 2):
                time.sleep(.01)
                continue
            tag = (n, mask, arm_type, player[0x15] & 64, player[0x93])
            if tag in results:
                time.sleep(.01)
                continue
            if n not in cached:
                f = bank['frames'][n]
                raw = decode_stream(g, f['offset'], f['limit'], f['tile_count'] * 128).data
                canvas_size=(256,160) if ultimate and n in (217,218,219,220) else (160,160)
                layers = {bi: canvas_from_parts(raw, f['tile_count'], local_composition(composition_frame(c, bi, n)),size=canvas_size) for bi in (0, 5, 6, 7, 8)}
                cached[n] = f, raw, layers
            f, raw, layers = cached[n]
            ram_equal = read(base + 0x16dea8, len(raw)) == raw
            if not ram_equal:
                time.sleep(.01)
                continue
            for video in videos:
                vram = read(video, 1048576)
                if len(vram) != 1048576:
                    continue
                cursor = 0
                upload = True
                for first in range(0, f['tile_count'], 16):
                    width = min(16, f['tile_count'] - first) * 8
                    for y in range(16):
                        pos = (first // 16 * 16 + y) * 2048 + 640
                        upload &= vram[pos:pos + width] == raw[cursor:cursor + width]
                        cursor += width
                if not upload:
                    continue
                after = read(base + 0x1418c8, 0xe4)
                if not after or (after[0x47], after[0xa7], after[0xb8], after[0x15], after[0x93]) != (n, mask, arm_type, player[0x15], player[0x93]):
                    continue
                clut = struct.unpack_from('<H', player, 0x42)[0]
                body_clut = 0x7840 if clut & 0x8000 else clut
                canvas_size=(layers[0].shape[1],layers[0].shape[0])
                im = Image.new('RGBA', canvas_size)
                armor_im = Image.new('RGBA', canvas_size)
                palettes = {}
                for bit, bi in ((0, 0), (8, 8), (1, 5), (4, 7), (2, 6)):
                    if bit and not mask & bit:
                        continue
                    address = body_clut if bi == 0 else 0x7844 if bi == 7 and arm_type == 2 else 0x7843
                    pos = (address >> 6) * 2048 + (address & 63) * 32
                    colorbytes = vram[pos:pos + 32]
                    palettes[str(bi)] = {'clut': address, 'words_hex': colorbytes.hex(), 'matching_arc_rows': [i for i in range(len(pal) // 32) if pal[i * 32:i * 32 + 32] == colorbytes]}
                    layer = save_image(layers[bi].tobytes(), canvas_size, struct.unpack('<16H', colorbytes), out / 'scratch_layer.png').convert('RGBA')
                    im.alpha_composite(layer)
                    if bi:armor_im.alpha_composite(layer)
                bb = im.getbbox()
                sprite = im.crop(bb)
                matches = []
                armor_matches = []
                for page in (0, 240, 256):
                    screen = framebuffer(vram, 0, page)
                    found = match_sprite(screen, sprite)
                    if found:
                        filename = f'actual_{n:03}_m{mask}_a{arm_type}_d{tag[3]}_w{tag[4]}_{page}.png'
                        screen.save(out / filename)
                        matches.extend({'image': filename, 'page_y': page, **v} for v in found)
                    if tag not in armor_results and armor_im.getbbox() and all(v['matching_arc_rows'] for v in palettes.values()):
                        armor_found=match_sprite(screen,armor_im.crop(armor_im.getbbox()))
                        if armor_found:
                            filename=f'armor_actual_{n:03}_m{mask}_a{arm_type}_d{tag[3]}_w{tag[4]}_{page}.png'
                            screen.save(out/filename);armor_matches.extend({'image':filename,'page_y':page,**v} for v in armor_found)
                rec = {'frame': n, 'animation': player[0x17], 'armor': mask, 'arm_type': arm_type, 'direction_bit': tag[3], 'weapon': tag[4],
                       'ram_equal': ram_equal, 'vram_equal': upload, 'palettes': palettes, 'matches': matches, 'ram_host_address': base, 'vram_host_address': video}
                if tag not in samples:
                    im.save(out / f'expected_{n:03}.png')
                    framebuffer(vram, 0, 0).save(out / f'observed_{n:03}_0.png')
                    framebuffer(vram, 0, 240).save(out / f'observed_{n:03}_240.png')
                    framebuffer(vram, 0, 256).save(out / f'observed_{n:03}_256.png')
                    (out / f'sample_{n:03}_d{tag[3]}.vram').write_bytes(vram)
                    samples[tag] = rec
                if matches:
                    results[tag] = rec
                    (out / f'player_{n:03}.bin').write_bytes(player)
                    videos = [video]
                    break
                if armor_matches:
                    armor_results[tag]={**rec,'matches':armor_matches,'comparison_scope':'visible armor pixels only; base body and effects excluded'}
            covered={(r['frame'],r['direction_bit']) for r in results.values()}
            finished=covered>={(n,d) for n in requested for d in (0,64)} if args.both_directions else {r['frame'] for r in results.values()}>=requested
            if finished:
                break
            time.sleep(.01)
        report = {'pid': prior['pid'], 'source_build': str(build), 'modified_bin_sha256': manifest['modified_bin']['sha256'],
                  'input_sent': False, 'process_memory_written': False, 'focus_changed': False, 'checked_ram_entries': checked_ram_entries,
                  'requested_frames': sorted(requested), 'verified_frames': sorted({v['frame'] for v in results.values()}),
                  'results': list(results.values()), 'samples_without_full_match': [v for k, v in samples.items() if k not in results]}
        report['armor_only_results']=list(armor_results.values())
        report['verified_armor_only_frames']=sorted({v['frame'] for v in armor_results.values()})
        report['both_directions_requested']=args.both_directions
        write_json(out / 'verification.local.json', report)
        print(json.dumps({'output': str(out), 'verified_frames': report['verified_frames'], 'verified_armor_only_frames':report['verified_armor_only_frames'], 'observed_without_full_match': [v['frame'] for v in report['samples_without_full_match']]}))
    finally:
        kernel.CloseHandle(handle)


if __name__ == '__main__':
    main()
