"""린 팔레트에 맞춘 피격 몸체·흰 섬광. 원작 CLUT2 효과는 유지한다."""
from src.psx_player import graphics_bank, composition_frame, decode_stream
from src.psx_frame_edit import edit_frame_indices
from src.psx_hurt import derive_hurt_frames, edit_hurt_stream
from src.psx_hurt_launch import derive_launch

LIGHT_MAP=bytes((0,7,8,9,8,9,10,9,10,11,11,11,13,14,11,11))
FRAMES=frozenset(range(135,146))

def derive(gfx,parts,ordinary,strong):
    frames=derive_hurt_frames(gfx,parts,ordinary,spark_index=11,fill_index=10,outline_index=11)
    bank=graphics_bank(gfx,0);f=bank['frames'][135]
    raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
    streams={135:edit_hurt_stream(raw,f['tile_count'],{n:composition_frame(parts,0,n) for n in (135,136,137)},ordinary,spark_index=11)}
    f=bank['frames'][138];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
    streams[138]=edit_frame_indices(raw,f['tile_count'],composition_frame(parts,0,138),*frames[138])
    launched,launch_streams=derive_launch(gfx,parts,strong,light_mapping=LIGHT_MAP,flash_fill=10,flash_outline=11)
    frames.update(launched);streams.update(launch_streams)
    return frames,streams

def validate(gfx,parts,frames):
    if not FRAMES<=frames.keys():raise ValueError('All Rin hurt variants are required')
    expected,streams=derive(gfx,parts,frames[135],frames[139])
    if any(frames[n]!=expected[n] for n in FRAMES):raise ValueError('Rin hurt effect differs from its body')
    return streams
