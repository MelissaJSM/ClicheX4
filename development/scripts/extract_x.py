"""미국판 X의 전체 압축 참조와 기본 237프레임을 추출한다. 원본은 읽기 전용."""
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw, ImageFont
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from scripts.project import load_project, inspect_references, validate_bin, new_run, write_json
from scripts.extract_zero import save_image
from src.psx_player import bank_offsets, graphics_bank, decode_stream, composition_frame, compose_indices


def main():
    project = load_project(ROOT, 'ver_buki_riko')
    refs = inspect_references(ROOT, project)
    cfg = json.loads((ROOT/'config/shibuki_x_us.json').read_text(encoding='utf-8'))
    original = ROOT/project['source_bin']
    validate_bin(original, cfg['source_sha256'])
    accepted = json.loads((ROOT/'projects/ver_buki_riko/riko_accepted_build.json').read_text(encoding='utf-8'))
    parent = ROOT/accepted['cue']
    parent = parent.with_suffix('.bin')
    validate_bin(parent, accepted['bin_sha256'])
    with original.open('rb') as stream:
        reader = DiscReader(stream, original.stat().st_size)
        arc = reader.read(cfg['archive']['lba'], cfg['archive']['size'])
        exe = reader.read(cfg['executable']['lba'], cfg['executable']['size'])
    if sha256(arc) != cfg['archive']['sha256'] or sha256(exe) != cfg['executable']['sha256']:
        raise ValueError('Unsupported X archive/executable')
    with parent.open('rb') as stream:
        current_arc = DiscReader(stream, parent.stat().st_size).read(cfg['archive']['lba'], len(arc))
    if current_arc != arc:
        raise ValueError('Accepted Riko build has changed X archive')
    entries = psx_arc(arc)
    def entry(kind):
        matches = [e for e in entries if int(e['type'], 16) == kind]
        if len(matches) != 1:
            raise ValueError('Ambiguous X entry')
        e = matches[0]
        return e, arc[e['offset']:e['offset']+e['size']]
    gm, gfx = entry(2)
    _, parts = entry(3)
    _, palette = entry(9)
    words = struct.unpack_from('<64H', palette)
    out = new_run(ROOT, project['project_id'], 'shibuki_x_extract')
    for name, data in [('original.arc', arc), ('original.exe', exe), ('graphics_entry.bin', gfx),
                       ('composition_entry.bin', parts), ('palette_bank.bin', palette)]:
        (out/name).write_bytes(data)
    banks, streams, frames = [], {}, []
    rebuilt = bytearray(arc)
    offsets = bank_offsets(gfx, allow_aliases=True)
    for bi in range(len(offsets)):
        bank = graphics_bank(gfx, bi, allow_bank_aliases=True)
        banks.append({'bank': bi, 'offset': bank['base'], 'end': bank['end'], 'count': len(bank['frames']),
                      'alias_ids': [i for i, o in enumerate(offsets) if o == bank['base']]})
        for f in bank['frames']:
            raw = decode_stream(gfx, f['offset'], f['limit'], f['tile_count']*128)
            if raw.serialize() != gfx[raw.start:raw.end]:
                raise ValueError('Compressed byte roundtrip failed')
            rebuilt[gm['offset']+raw.start:gm['offset']+raw.end] = raw.serialize()
            streams.setdefault(str(raw.start), []).append([bi, f['index']])
            if bi != 0:
                continue
            comp = composition_frame(parts, 0, f['index'])
            record = {**f, 'compressed_end': raw.end, 'decoded_sha256': sha256(raw.data), 'composition': comp}
            try:
                pixels, size, bounds, _ = compose_indices(raw.data, f['tile_count'], comp, allowed_cluts={0,1,2,3})
                path = f"base_{f['index']:03d}.png"
                pic = save_image(pixels, size, words, out/path)
                record.update(image=path, size=size, bounds=bounds, opaque_bbox=pic.convert('RGBA').getbbox(),
                              opaque_pixels=sum(bool(p) for p in pixels), rendered=True,
                              palette_status='Static first four CLUTs; runtime palette selection not yet confirmed')
            except ValueError as exc:
                record.update(image=None, rendered=False, reason=str(exc))
            frames.append(record)
    if bytes(rebuilt) != arc:
        raise ValueError('Full X ARC roundtrip mismatch')
    (out/'roundtrip.arc').write_bytes(rebuilt)
    def exeread(addr, size):
        offset = addr - cfg['executable']['load_address'] + 2048
        if offset < 2048 or offset+size > len(exe):
            raise ValueError('X animation points outside executable')
        return exe[offset:offset+size]
    animations = []
    for aid in range(cfg['animation_table_count']):
        address, = struct.unpack('<I', exeread(cfg['animation_table_address']+4*aid, 4))
        pos, seen, steps = 0, set(), []
        while pos not in seen:
            if pos < 0 or len(seen) >= 512:
                raise ValueError('Invalid X sequence traversal')
            seen.add(pos)
            duration, event, step, frame = struct.unpack('<bbbB', exeread(address+pos*4, 4))
            steps.append(dict(position=pos, duration_ticks=duration, event=event, relative_step=step, frame=frame))
            pos += step
        animations.append(dict(id=aid, address=address, steps=steps, loop_to=pos,
                               runtime_verified=False, event_branch_semantics_verified=False))
    idle = animations[cfg['idle_animation_id']]
    if idle['address'] != cfg['idle_sequence_address'] or sorted({s['frame'] for s in idle['steps']}) != [0,115,116,117,118,119]:
        raise ValueError('Unexpected X idle sequence')
    report = dict(project=project['project_id'], task='x_shibuki', source_sha256=cfg['source_sha256'],
                  accepted_parent_sha256=accepted['bin_sha256'], parent_x_arc_original=True,
                  archive=cfg['archive'], entries=entries, graphics_banks=banks,
                  compressed_references=sum(b['count'] for b in banks), unique_streams=len(streams),
                  stream_sharing=streams, base_frames=frames, base_rendered=sum(f['rendered'] for f in frames),
                  palette_words=list(words), animations=animations, idle_animation=idle,
                  byte_identical_roundtrip=True, runtime_verified=False, references=refs,
                  parts_banks=len(bank_offsets(parts)), armor_mapping_verified=False)
    write_json(out/'inventory.json', report)
    font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 13)
    # Common world origin and ground line: no per-frame fit-to-box scaling.
    for name, selected in [('base_master_2x.png', frames), ('idle_original_4x.png', [frames[n] for n in [0,115,116,117,118,119]])]:
        zoom = 4 if name.startswith('idle') else 2
        cols = 6 if zoom == 4 else 12
        w, h = 112*zoom, 100*zoom
        sheet = Image.new('RGB', (cols*w, ((len(selected)+cols-1)//cols)*h), '#222630')
        draw = ImageDraw.Draw(sheet)
        for index, rec in enumerate(selected):
            x, y = index%cols*w, index//cols*h
            draw.text((x+5,y+4), f"X {rec['index']:03d}", font=font, fill='white')
            draw.line((x,y+80*zoom,x+w,y+80*zoom), fill='#414855')
            if rec['rendered']:
                im = Image.open(out/rec['image']).convert('RGBA')
                l,t,_,_ = rec['bounds']
                sheet.paste(im.resize((im.width*zoom,im.height*zoom),Image.Resampling.NEAREST),
                            (x+(50+l)*zoom,y+(57+t)*zoom), im.resize((im.width*zoom,im.height*zoom),Image.Resampling.NEAREST))
        sheet.save(out/name)
    inspect_references(ROOT, project)
    validate_bin(original, cfg['source_sha256'])
    validate_bin(parent, accepted['bin_sha256'])
    # A repeated extraction produces new evidence without silently replacing
    # the inventory referenced by approved artwork.
    pointer=ROOT/'projects/ver_buki_riko/shibuki_source_inventory.json'
    if not pointer.exists():
        write_json(pointer, {'task':'x_shibuki', 'inventory':str((out/'inventory.json').relative_to(ROOT)).replace('\\','/'),
                            'original_master':str((out/'base_master_2x.png').relative_to(ROOT)).replace('\\','/'),
                            'runtime_verified':False})
    print(json.dumps({'output':str(out), 'compressed_references':report['compressed_references'],
                      'unique_streams':len(streams),'base_rendered':report['base_rendered'],'roundtrip':True}))


if __name__ == '__main__':
    main()
