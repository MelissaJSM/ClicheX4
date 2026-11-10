"""지원 미국판의 제로 압축 데이터를 복원하고 저장 상태와 대조한다. 원본 쓰기 없음."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from scripts.project import load_project, validate_bin, new_run, write_json, inspect_references
from src.psx_player import bank_offsets, graphics_bank, decode_stream, composition_frame, compose_indices, indexed_atlas, u32
from src.epsxe_state import locate_vram, framebuffer, match_sprite


def save_image(indices, size, palette, path):
    from PIL import Image
    picture = Image.frombytes('P', size, indices)
    rgb = []
    for word in palette:
        rgb.extend(((word & 31)*255//31, ((word >> 5) & 31)*255//31, ((word >> 10) & 31)*255//31))
    picture.putpalette(rgb + [0]*(768-len(rgb)))
    picture.info['transparency'] = 0
    picture.save(path)
    return picture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', choices=['ver_buki_riko','ver_rin_nana'], required=True)
    parser.add_argument('--state', type=Path)
    args = parser.parse_args()
    project = load_project(ROOT, args.project)
    inspect_references(ROOT, project)
    profile = json.loads((ROOT/'config/ps1_us_slus00561.json').read_text(encoding='utf-8'))
    source = ROOT/project['source_bin']
    validate_bin(source, profile['source_sha256'])
    with source.open('rb') as stream:
        reader = DiscReader(stream, source.stat().st_size)
        arc = reader.read(profile['zero_archive']['lba'], profile['zero_archive']['size'])
        exe = reader.read(profile['executable']['lba'], profile['executable']['size'])
    if sha256(arc) != profile['zero_archive']['sha256'] or sha256(exe) != profile['executable']['sha256']:
        raise ValueError('Archive/executable identity mismatch')
    entries = psx_arc(arc)
    def entry(kind):
        matches = [e for e in entries if e['type'] == hex(kind)]
        if len(matches) != 1:
            raise ValueError('Ambiguous archive entry')
        e = matches[0]
        return e, arc[e['offset']:e['offset']+e['size']]
    graphics_meta, graphics = entry(2)
    parts_meta, parts = entry(3)
    palette_meta, palette_bytes = entry(9)
    palette = struct.unpack_from('<16H', palette_bytes)
    if palette[0] != 0:
        raise ValueError('Preview transparent color assumption failed')
    def exe_slice(address, size):
        pos = address-profile['executable']['load_address']+2048
        if pos < 2048 or pos+size > len(exe):
            raise ValueError('Executable address outside loaded image')
        return exe[pos:pos+size]
    animation_id = profile['idle_animation_id']
    sequence_address = u32(exe_slice(profile['zero_animation_table_address']+animation_id*4,4),0)
    bank_id = exe_slice(profile['zero_animation_bank_table_address']+animation_id,1)[0]
    if bank_id != 0:
        raise ValueError('Unexpected idle graphics bank')
    sequence, seen, position = [], set(), 0
    while position not in seen:
        if len(seen) > 256 or position < 0:
            raise ValueError('Invalid animation cycle')
        seen.add(position)
        duration,event,step,frame = struct.unpack('<bbbB',exe_slice(sequence_address+position*4,4))
        if duration <= 0:
            raise ValueError('Invalid animation duration')
        sequence.append({'position':position,'duration_ticks':duration,'event':event,'relative_step':step,'frame':frame})
        position += step
    out = new_run(ROOT,args.project,'zero_extract')
    (out/'original.arc').write_bytes(arc)
    (out/'original.exe').write_bytes(exe)
    (out/'palette_bank.bin').write_bytes(palette_bytes)
    (out/'graphics_entry.bin').write_bytes(graphics)
    (out/'composition_entry.bin').write_bytes(parts)
    rebuilt = bytearray(arc)
    banks, decoded, unique = [], {}, {}
    for bank_index in range(len(bank_offsets(graphics))):
        bank = graphics_bank(graphics,bank_index)
        bank_report = {'index':bank_index,'base':bank['base'],'end':bank['end'],'frames':[]}
        for f in bank['frames']:
            stream = decode_stream(graphics,f['offset'],f['limit'],f['tile_count']*128)
            if stream.serialize() != graphics[stream.start:stream.end]:
                raise ValueError('Compressed token roundtrip failed')
            dest = graphics_meta['offset']+stream.start
            rebuilt[dest:dest+stream.end-stream.start] = stream.serialize()
            decoded[bank_index,f['index']] = (f,stream)
            unique.setdefault((stream.start,stream.end),[]).append([bank_index,f['index']])
            bank_report['frames'].append({**f,'stream_end':stream.end,'decoded_sha256':sha256(stream.data),
                                           'compressed_sha256':sha256(stream.serialize())})
        banks.append(bank_report)
    if bytes(rebuilt) != arc:
        raise ValueError('Archive roundtrip failed')
    (out/'roundtrip.arc').write_bytes(rebuilt)
    preview_frames = []
    for frame in sorted({s['frame'] for s in sequence}):
        f, stream = decoded[bank_id,frame]
        composition = composition_frame(parts,0,frame)
        indices,size,bounds,provenance = compose_indices(stream.data,f['tile_count'],composition)
        name = f'idle_{frame:03d}'
        (out/(name+'.packed4')).write_bytes(stream.data)
        (out/(name+'.indices')).write_bytes(indices)
        picture = save_image(indices,size,palette,out/(name+'.png'))
        picture.resize((size[0]*6,size[1]*6),resample=0).save(out/(name+'_6x.png'))
        atlas,_,height = indexed_atlas(stream.data,f['tile_count'])
        save_image(atlas,(256,height),palette,out/(name+'_atlas.png'))
        metadata = {'frame':frame,'size':size,'bounds_relative_to_origin':bounds,'origin_in_image':[-bounds[0],-bounds[1]],
                    'graphics':f,'stream_end':stream.end,'composition':composition,'provenance':provenance,
                    'word_literal_owners':stream.owners,'shared_graphics_frames':unique[stream.start,stream.end]}
        write_json(out/(name+'.json'),metadata)
        preview_frames.append({k:v for k,v in metadata.items() if k not in ['provenance','word_literal_owners']})
    report = {'project':args.project,'source_sha256':profile['source_sha256'],'archive':profile['zero_archive'],
              'entries':entries,'graphics_banks':banks,'distinct_compressed_streams':len(unique),
              'archive_roundtrip_sha256':sha256(rebuilt),'compressed_token_roundtrip':True,
              'idle_animation':{'id':animation_id,'table_address':profile['zero_animation_table_address'],
                                'sequence_address':sequence_address,'bank':bank_id,'steps':sequence,
                                'loop_to_step':position,'time_unit':'animation update tick; wall-time rate not measured'},
              'palette_words':list(palette),'palette_high_bits_preserved':True,
              'idle_frames':preview_frames,'runtime':None,'game_data_modified':False}
    if args.state:
        state_path = args.state.resolve()
        if not state_path.is_relative_to((ROOT/'work').resolve()):
            raise ValueError('State must be in project work directory')
        with gzip.open(state_path,'rb') as stream:
            state = stream.read(8*1024*1024+1)
        if len(state) > 8*1024*1024 or not state.startswith(b'ePSXe'):
            raise ValueError('Unsupported save state')
        anchor = exe_slice(sequence_address,48)
        start = state.find(anchor)
        if start < 0 or state.find(anchor,start+1) != -1:
            raise ValueError('RAM anchor is not unique')
        ram_start = start-(sequence_address & 0x1fffff)
        if ram_start < 0 or ram_start+0x200000 > len(state):
            raise ValueError('RAM range outside state')
        ram = state[ram_start:ram_start+0x200000]
        def memory(address,size):
            offset=address & 0x1fffff
            if not 0x80000000 <= address < 0x80200000 or offset+size > len(ram):
                raise ValueError('Invalid emulated RAM pointer')
            return ram[offset:offset+size]
        if memory(profile['zero_animation_table_address'],576) != exe_slice(profile['zero_animation_table_address'],576):
            raise ValueError('RAM animation table differs from executable')
        player=memory(profile['player_object_address'],0xe4)
        if player[2] != 1 or player[0x17] != animation_id:
            raise ValueError('Save state is not Zero idle animation')
        frame=player[0x47]
        f,stream=decoded[bank_id,frame]
        gfx_pointer=u32(player,0x38); parts_pointer=u32(player,0x3c)
        gb=banks[bank_id]
        graphics_match=memory(gfx_pointer,gb['end']-gb['base'])==graphics[gb['base']:gb['end']]
        part_offsets=bank_offsets(parts)
        parts_match=memory(parts_pointer,part_offsets[1]-part_offsets[0])==parts[part_offsets[0]:part_offsets[1]]
        decoded_match=memory(profile['player_gfx_buffer_address'],len(stream.data))==stream.data
        if not (graphics_match and parts_match and decoded_match):
            raise ValueError('Runtime resource/buffer mismatch')
        vram = locate_vram(state,stream.data,f['tile_count'])
        clut = struct.unpack_from('<H',player,0x42)[0]
        palette_pos = vram+(clut >> 6)*2048+(clut & 63)*32
        if state[palette_pos:palette_pos+32] != palette_bytes[:32]:
            raise ValueError('VRAM palette differs from archive bank 0')
        from PIL import Image
        sprite=Image.open(out/f'idle_{frame:03d}.png')
        framebuffer_matches=[]
        for page in (0,256):
            screen=framebuffer(state,vram,page)
            screen.save(out/f'runtime_framebuffer_{page}.png')
            framebuffer_matches.extend({'page_y':page,**m} for m in match_sprite(screen,sprite))
        if not framebuffer_matches:
            raise ValueError('Sprite does not match saved framebuffer')
        report['runtime']={'state_sha256':sha256(state_path.read_bytes()),'expanded_size':len(state),
                           'ram_offset':ram_start,'character':player[2],'animation':player[0x17],
                           'frame':frame,'remaining_duration':player[0x44],'graphics_pointer':gfx_pointer,
                           'composition_pointer':parts_pointer,'texture_base':struct.unpack_from('<H',player,0x40)[0],
                           'clut':struct.unpack_from('<H',player,0x42)[0],'graphics_bank_matches':graphics_match,
                           'composition_bank_matches':parts_match,'decompressed_buffer_matches':decoded_match,
                           'vram_offset':vram,'vram_upload_matches':True,'palette_matches':True,
                           'framebuffer_matches':framebuffer_matches}
        (out/'baseline_state.gz').write_bytes(state_path.read_bytes())
    validate_bin(source,profile['source_sha256'])
    write_json(out/'report.json',report)
    print(json.dumps({'output':str(out),'banks':[len(b['frames']) for b in banks],
                      'distinct_streams':len(unique),'idle_frames':len(preview_frames),'roundtrip':True,'runtime':report['runtime']}))


if __name__ == '__main__':
    main()
